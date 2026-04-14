import numpy as np

def appliquer_rotation(X, Y, phi_deg):
    if phi_deg == 0: return np.array(X), np.array(Y)
    phi_rad = np.radians(phi_deg)
    X_arr, Y_arr = np.array(X), np.array(Y)
    return X_arr * np.cos(phi_rad) - Y_arr * np.sin(phi_rad), X_arr * np.sin(phi_rad) + Y_arr * np.cos(phi_rad)

# ==========================================
# 1. MÉTHODE HYBRIDE (Stator + Rotor)
# ==========================================
def modele_hybride(N_lobes, e_excent, d_param, nb_points):
    m = int(N_lobes)
    n = m - 1
    me = m * e_excent
    b = e_excent - d_param
    pts_par_lobe = max(10, int(nb_points) // (2 * m)) 
    
    phi1_max = np.pi * d_param / me 
    phi1_min = -np.pi * d_param / me
    phi1 = np.linspace(phi1_min, phi1_max, pts_par_lobe)
    x1 = (me - d_param) * np.cos(phi1) - d_param * np.cos((me/d_param - 1) * phi1)
    y1 = (me - d_param) * np.sin(phi1) + d_param * np.sin((me/d_param - 1) * phi1)
    
    phi2_min = phi1_max
    phi2_max = (2*np.pi / m) - (np.pi*d_param/me) 
    phi2 = np.linspace(phi2_min, phi2_max, pts_par_lobe)
    x2 = (me + b) * np.cos(phi2) - b * np.cos((me/b + 1) * phi2 - np.pi*d_param/b)
    y2 = (me + b) * np.sin(phi2) - b * np.sin((me/b + 1) * phi2 - np.pi*d_param/b)
    
    x_stator_single, y_stator_single = np.concatenate([x1, x2]), np.concatenate([y1, y2])
    
    x_stator_full, y_stator_full = [], []
    for i in range(m):
        angle = 2 * np.pi * i / m
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_stator_full.extend(x_stator_single * cos_a - y_stator_single * sin_a)
        y_stator_full.extend(x_stator_single * sin_a + y_stator_single * cos_a)
    x_stator_full.append(x_stator_full[0]); y_stator_full.append(y_stator_full[0])

    phi1_Int_max = np.pi * d_param / (n * e_excent)
    phi1_Int_min = -np.pi * d_param / (n * e_excent)
    phi1_Int = np.linspace(phi1_Int_min, phi1_Int_max, pts_par_lobe)
    xi1 = (n * e_excent - d_param) * np.cos(phi1_Int) - d_param * np.cos((n * e_excent / d_param - 1) * phi1_Int)
    eta1 = (n * e_excent - d_param) * np.sin(phi1_Int) + d_param * np.sin((n * e_excent / d_param - 1) * phi1_Int)
    
    phi2_Int_min = phi1_Int_max 
    phi2_int_max = 2*np.pi / n - np.pi*d_param/(n*e_excent)
    phi2_int = np.linspace(phi2_Int_min, phi2_int_max, pts_par_lobe)
    xi2 = (n * e_excent + b) * np.cos(phi2_int) - b * np.cos(((n * e_excent / b + 1) * phi2_int - np.pi*d_param/b))
    eta2 = (n * e_excent + b) * np.sin(phi2_int) - b * np.sin(((n * e_excent / b + 1) * phi2_int - np.pi*d_param/b))
    
    x_rotor_single, y_rotor_single = np.concatenate([xi1, xi2]), np.concatenate([eta1, eta2])
    
    x_rotor_full, y_rotor_full = [], []
    for i in range(n):
        angle = 2 * np.pi * i / n
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_rotor_full.extend(x_rotor_single * cos_a - y_rotor_single * sin_a)
        y_rotor_full.extend(x_rotor_single * sin_a + y_rotor_single * cos_a)
    x_rotor_full.append(x_rotor_full[0]); y_rotor_full.append(y_rotor_full[0])

    return np.array(x_stator_full), np.array(y_stator_full), np.array(x_rotor_full), np.array(y_rotor_full)

# ==========================================
# 2. MÉTHODE TROCHOÏDE (Adaptée N_lobes / e)
# ==========================================
def modele_trochoide(N_lobes, R_prim, e_excent, nb_points, type_trochoide="Hypocycloïde"):
    N = int(N_lobes)
    # Le rayon roulant se déduit mathématiquement du rayon primitif et du nb de lobes
    r_roulant = R_prim / N
    
    # L'excentricité agit comme le rayon traceur
    R_traceur = e_excent
    
    # Puisque N est un entier parfait, la courbe se referme toujours exactement en 2*pi
    theta = np.linspace(0, 2 * np.pi, int(nb_points))
    
    if type_trochoide == "Hypocycloïde":
        X = (R_prim - r_roulant) * np.cos(theta) + R_traceur * np.cos(((R_prim - r_roulant) / r_roulant) * theta)
        Y = (R_prim - r_roulant) * np.sin(theta) - R_traceur * np.sin(((R_prim - r_roulant) / r_roulant) * theta)
    else: 
        X = (R_prim + r_roulant) * np.cos(theta) - R_traceur * np.cos(((R_prim + r_roulant) / r_roulant) * theta)
        Y = (R_prim + r_roulant) * np.sin(theta) - R_traceur * np.sin(((R_prim + r_roulant) / r_roulant) * theta)
        
    return X, Y, None, None

# ==========================================
# 3. MÉTHODE PARAMÉTRIQUE
# ==========================================
def modele_parametrique_circ(N_lobes, R_prim, R_ext, r_cercle, nb_points_seg, phi_deg):
    cos_t = np.clip((R_prim**2 + r_cercle**2 - R_ext**2) / (2 * R_prim * r_cercle), -1.0, 1.0)
    t_int = np.arccos(cos_t)
    alpha_int = np.arctan2(r_cercle * np.sin(t_int), R_prim - r_cercle * cos_t)
    X_f, Y_f = [], []
    for k in range(int(N_lobes)):
        phi_k = k * 2 * np.pi / N_lobes
        for t in np.linspace(-t_int, t_int, int(nb_points_seg)):
            xl, yl = R_prim - r_cercle * np.cos(t), r_cercle * np.sin(t)
            X_f.append(xl * np.cos(phi_k) - yl * np.sin(phi_k))
            Y_f.append(xl * np.sin(phi_k) + yl * np.cos(phi_k))
        for th in np.linspace(phi_k + alpha_int, (k+1)*2*np.pi/N_lobes - alpha_int, int(nb_points_seg)):
            X_f.append(R_ext * np.cos(th)); Y_f.append(R_ext * np.sin(th))
    X_f.append(X_f[0]); Y_f.append(Y_f[0])
    return appliquer_rotation(X_f, Y_f, phi_deg)

def modele_parametrique_ell(N_lobes, R_prim, R_ext, a_ell, b_ell, nb_points_seg, phi_deg):
    Aq, Bq, Cq = a_ell**2 - b_ell**2, -2 * R_prim * a_ell, R_prim**2 + b_ell**2 - R_ext**2
    Delta = max(0, Bq**2 - 4 * Aq * Cq)
    c1, c2 = (-Bq - np.sqrt(Delta))/(2*Aq), (-Bq + np.sqrt(Delta))/(2*Aq)
    t_int = np.arccos(np.clip(c1 if abs(c1) <= 1 else c2, -1.0, 1.0))
    alpha_int = np.arctan2(b_ell * np.sin(t_int), R_prim - a_ell * np.cos(t_int))
    X_f, Y_f = [], []
    for k in range(int(N_lobes)):
        phi_k = k * 2 * np.pi / N_lobes
        for t in np.linspace(-t_int, t_int, int(nb_points_seg)):
            xl, yl = R_prim - a_ell * np.cos(t), b_ell * np.sin(t)
            X_f.append(xl * np.cos(phi_k) - yl * np.sin(phi_k))
            Y_f.append(xl * np.sin(phi_k) + yl * np.cos(phi_k))
        for th in np.linspace(phi_k + alpha_int, (k+1)*2*np.pi/N_lobes - alpha_int, int(nb_points_seg)):
            X_f.append(R_ext * np.cos(th)); Y_f.append(R_ext * np.sin(th))
    X_f.append(X_f[0]); Y_f.append(Y_f[0])
    return appliquer_rotation(X_f, Y_f, phi_deg)

def modele_parametrique_sin(N_lobes, R_prim, R_ext, A_sin, periode_deg, nb_points_seg, phi_deg):
    w = 360.0 / max(0.1, periode_deg)
    alpha_int = np.arccos(np.clip((R_prim - R_ext) / A_sin, -1.0, 1.0)) / w 
    X_f, Y_f = [], []
    for k in range(int(N_lobes)):
        phi_k = k * 2 * np.pi / N_lobes
        for th in np.linspace(phi_k - alpha_int, phi_k + alpha_int, int(nb_points_seg)):
            rv = R_prim - A_sin * np.cos(w * (th - phi_k))
            X_f.append(rv * np.cos(th)); Y_f.append(rv * np.sin(th))
        for th in np.linspace(phi_k + alpha_int, (k+1)*2*np.pi/N_lobes - alpha_int, int(nb_points_seg)):
            X_f.append(R_ext * np.cos(th)); Y_f.append(R_ext * np.sin(th))
    X_f.append(X_f[0]); Y_f.append(Y_f[0])
    return appliquer_rotation(X_f, Y_f, phi_deg)