import numpy as np
import matplotlib.pyplot as plt

def calculer_trochoide_et_enveloppe(N_lobes, R_prim, e_excent, rho_enveloppe, K, nb_points=3000):
    """
    K = 1  : Épitrochoïde
    K = -1 : Hypotrochoïde
    """
    n1 = int(N_lobes)
    n2 = n1 + K
    
    # Paramètre 'a' = rayon du centre du cercle roulant
    a = R_prim * (n2 / n1)
    
    # Résolution et plage angulaire
    phi1 = np.linspace(0, 2 * np.pi * n2, nb_points)
    
    # --- 1. TROCHOÏDE DE BASE (Éq. 1 du document) ---
    x_t = a * np.sin(phi1 / n2) - K * e_excent * np.sin(K * phi1)
    y_t = a * np.cos(phi1 / n2) - K * e_excent * np.cos(K * phi1)
    
    # --- 2. CALCUL DU VECTEUR NORMAL (Éq. 2 du document) ---
    dx_dphi = (a / n2) * np.cos(phi1 / n2) - e_excent * np.cos(K * phi1)
    dy_dphi = -(a / n2) * np.sin(phi1 / n2) + e_excent * np.sin(K * phi1)
    
    mag = np.hypot(dx_dphi, dy_dphi)
    
    # Sécurité au point de rebroussement (évite la division par zéro)
    mag_safe = np.where(mag < 1e-10, 1e-10, mag)
    
    n_x = dy_dphi / mag_safe
    n_y = -dx_dphi / mag_safe
    
    # --- 3. ENVELOPPE BRUTE (Éq. 3 du document) ---
    x_env_brut = x_t + rho_enveloppe * n_x
    y_env_brut = y_t + rho_enveloppe * n_y
    
    # --- 4. CORRECTION MATHÉMATIQUE (Insertion des arcs de cercle) ---
    # On détecte les sauts provoqués par les points de rebroussement
    dist_consecutifs = np.hypot(np.diff(x_env_brut), np.diff(y_env_brut))
    seuil_saut = abs(rho_enveloppe) * 0.2 # On détecte un saut anormal
    
    sauts = np.where(dist_consecutifs > seuil_saut)[0]
    
    if len(sauts) > 0:
        x_env_lisse, y_env_lisse = [], []
        idx_prec = 0
        
        for i in sauts:
            # On ajoute le profil lisse jusqu'au saut
            x_env_lisse.extend(x_env_brut[idx_prec:i+1])
            y_env_lisse.extend(y_env_brut[idx_prec:i+1])
            
            # On calcule l'angle de la normale avant et après le rebroussement
            angle_avant = np.arctan2(n_y[i], n_x[i])
            angle_apres = np.arctan2(n_y[i+1], n_x[i+1])
            
            # On calcule l'écart d'angle et on le normalise sur le chemin le plus court
            delta = angle_apres - angle_avant
            delta = (delta + np.pi) % (2 * np.pi) - np.pi
            
            # --- CONDITION AJOUTÉE ICI ---
            # Si c'est une épitrochoïde, la géométrie de la courbe impose de 
            # parcourir l'arc de cercle dans le sens inverse pour bomber vers l'extérieur.
            if K == 1:
                signe = 1 if delta >= 0 else -1
                delta = delta - signe * 2 * np.pi
            # -----------------------------
            
            # On génère un arc de cercle autour du sommet du lobe
            angles_arc = angle_avant + np.linspace(0, delta, 30)
            
            # Le centre de cet arc est le point de rebroussement lui-même
            x_env_lisse.extend(x_t[i] + rho_enveloppe * np.cos(angles_arc))
            y_env_lisse.extend(y_t[i] + rho_enveloppe * np.sin(angles_arc))
            
            idx_prec = i + 1
            
        x_env_lisse.extend(x_env_brut[idx_prec:])
        y_env_lisse.extend(y_env_brut[idx_prec:])
        
        return x_t, y_t, np.array(x_env_lisse), np.array(y_env_lisse)
    
    # Si aucun saut n'est détecté, on renvoie la courbe brute
    return x_t, y_t, x_env_brut, y_env_brut


# ==========================================
# ZONE DE TEST 
# ==========================================
if __name__ == "__main__":
    N = 8         
    R = 50.0        
    e = 6        # Excentricité = R/N -> on force le point de rebroussement !
    rho = -3.0      # Enveloppe externe
    K = -1           # 1 = Épitrochoïde
    
    x_t, y_t, x_env, y_env = calculer_trochoide_et_enveloppe(N, R, e, rho, K)

    plt.figure(figsize=(8, 8))
    titre = "Épitrochoïde" if K == 1 else "Hypotrochoïde"
    
    plt.plot(x_t, y_t, 'k--', alpha=0.4, label=f'{titre} génératrice')
    plt.plot(x_env, y_env, 'r-', linewidth=2, label=f'Enveloppe lissée ($\\rho$={rho})')
    
    plt.plot(0, 0, 'ko')
    plt.axis('equal')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.title(f"Test Enveloppe avec Arcs : {titre}\nN={N}, R={R}, e={e}", fontweight='bold')
    plt.legend(loc="upper right")
    
    plt.show()