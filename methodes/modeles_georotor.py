import numpy as np

def appliquer_rotation(X, Y, phi_deg):
    if phi_deg == 0: return np.array(X), np.array(Y)
    phi_rad = np.radians(phi_deg)
    X_arr, Y_arr = np.array(X), np.array(Y)
    return X_arr * np.cos(phi_rad) - Y_arr * np.sin(phi_rad), X_arr * np.sin(phi_rad) + Y_arr * np.cos(phi_rad)

# ==========================================
# 1. MÉTHODE HYBRIDE
# ==========================================
def modele_hybride_stator(N_lobes, e_excent, d_param, nb_points):
    me = N_lobes * e_excent
    b = e_excent - d_param
    pts_par_lobe = max(10, nb_points // (2 * N_lobes)) 
    
    # Segment 1
    phi1_max = np.pi * d_param / me 
    phi1 = np.linspace(-phi1_max, phi1_max, pts_par_lobe)
    x1 = (me - d_param) * np.cos(phi1) - d_param * np.cos((me/d_param - 1) * phi1)
    y1 = (me - d_param) * np.sin(phi1) + d_param * np.sin((me/d_param - 1) * phi1)
    
    # Segment 2
    phi2_max = (2*np.pi / N_lobes) - (np.pi*d_param/me) 
    phi2 = np.linspace(phi1_max, phi2_max, pts_par_lobe)
    x2 = (me + b) * np.cos(phi2) - b * np.cos((me/b + 1) * phi2 - np.pi*d_param/b)
    y2 = (me + b) * np.sin(phi2) - b * np.sin((me/b + 1) * phi2 - np.pi*d_param/b)
    
    x_single, y_single = np.concatenate([x1, x2]), np.concatenate([y1, y2])
    
    # Répétition polaire
    x_full, y_full = [], []
    for i in range(int(N_lobes)):
        angle = 2 * np.pi * i / N_lobes
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_full.extend(x_single * cos_a - y_single * sin_a)
        y_full.extend(x_single * sin_a + y_single * cos_a)
        
    x_full.append(x_full[0]); y_full.append(y_full[0])
    return np.array(x_full), np.array(y_full)

# ==========================================
# 2. MÉTHODE TROCHOÏDE
# ==========================================
def modele_trochoide(N_lobes, R_prim, R_traceur, nb_points, type_trochoide="Hypocycloïde"):
    N_rotor = N_lobes - 1
    r_roulant = R_prim / N_rotor
    theta = np.linspace(0, 2 * np.pi, nb_points)
    
    if type_trochoide == "Hypocycloïde":
        X = (r_roulant * N_lobes * np.cos(theta)) + (R_traceur * np.cos(N_lobes * theta))
        Y = (r_roulant * N_lobes * np.sin(theta)) - (R_traceur * np.sin(N_lobes * theta)) 
    else: # Épitrochoïde
        X = (r_roulant * N_lobes * np.cos(theta)) - (R_traceur * np.cos((N_lobes + 1) * theta))
        Y = (r_roulant * (N_lobes + 1) * np.sin(theta)) - (R_traceur * np.sin((N_lobes + 1) * theta))
    
    return X, Y, r_roulant

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