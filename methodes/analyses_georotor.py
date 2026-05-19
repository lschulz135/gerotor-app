import numpy as np
from scipy.integrate import trapezoid
from scipy.interpolate import interp1d
from scipy.spatial.distance import cdist

def generate_full_profile(x_single, y_single, num_lobes, rotation_angle=0):
    x_full, y_full = [], []
    for i in range(num_lobes):
        angle = 2 * np.pi * i / num_lobes + rotation_angle
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_full.extend(x_single * cos_a - y_single * sin_a)
        y_full.extend(x_single * sin_a + y_single * cos_a)
    return np.array(x_full), np.array(y_full)

def find_chamber_boundaries(x_stator_full, y_stator_full, x_rotor_full, y_rotor_full, n_angles=3600):
    theta_sweep = np.linspace(0, 2*np.pi, n_angles)
    
    theta_stator = np.arctan2(y_stator_full, x_stator_full)
    r_stator = np.sqrt(x_stator_full**2 + y_stator_full**2)
    sort_idx = np.argsort(theta_stator)
    interp_stator = interp1d(
        np.concatenate([theta_stator[sort_idx] - 2*np.pi, theta_stator[sort_idx], theta_stator[sort_idx] + 2*np.pi]),
        np.concatenate([r_stator[sort_idx], r_stator[sort_idx], r_stator[sort_idx]]),
        kind='linear', bounds_error=False, fill_value='extrapolate'
    )
    r_stator_sweep = interp_stator(theta_sweep)
    
    theta_rotor = np.arctan2(y_rotor_full, x_rotor_full)
    r_rotor = np.sqrt(x_rotor_full**2 + y_rotor_full**2)
    sort_idx_r = np.argsort(theta_rotor)
    interp_rotor = interp1d(
        np.concatenate([theta_rotor[sort_idx_r] - 2*np.pi, theta_rotor[sort_idx_r], theta_rotor[sort_idx_r] + 2*np.pi]),
        np.concatenate([r_rotor[sort_idx_r], r_rotor[sort_idx_r], r_rotor[sort_idx_r]]),
        kind='linear', bounds_error=False, fill_value='extrapolate'
    )
    r_rotor_sweep = interp_rotor(theta_sweep)
    
    diff = r_stator_sweep - r_rotor_sweep
    chamber_segments = []
    in_chamber = False
    start_idx = None
    tolerance = 0.1
    
    for i in range(len(diff)):
        if diff[i] > tolerance and not in_chamber:
            start_idx = i
            in_chamber = True
        elif diff[i] <= tolerance and in_chamber:
            if start_idx is not None and (i - start_idx) > 10:
                chamber_segments.append((theta_sweep[start_idx], theta_sweep[i]))
            in_chamber = False
    if in_chamber and start_idx is not None:
        chamber_segments.append((theta_sweep[start_idx], theta_sweep[-1]))
        
    return chamber_segments, theta_sweep, r_stator_sweep, r_rotor_sweep, diff

def calculate_chamber_area_with_Ac_corrected(theta_start, theta_end, x_stator_full, y_stator_full, x_rotor_full, y_rotor_full, x_rotor_original, y_rotor_original, excentricite, n_angles=500):
    if theta_end < theta_start: theta_end += 2 * np.pi
    theta_sector = np.linspace(theta_start, theta_end, n_angles)
    
    theta_stator = np.arctan2(y_stator_full, x_stator_full)
    r_stator = np.sqrt(x_stator_full**2 + y_stator_full**2)
    sort_idx = np.argsort(theta_stator)
    interp_stator = interp1d(
        np.concatenate([theta_stator[sort_idx]-2*np.pi, theta_stator[sort_idx], theta_stator[sort_idx]+2*np.pi]),
        np.concatenate([r_stator[sort_idx]]*3), kind='linear', fill_value='extrapolate'
    )
    r_stator_sector = interp_stator(theta_sector)
    A_o = 0.5 * trapezoid(r_stator_sector**2, theta_sector)
    
    theta_rotor = np.arctan2(y_rotor_full, x_rotor_full)
    r_rotor = np.sqrt(x_rotor_full**2 + y_rotor_full**2)
    sort_idx_r = np.argsort(theta_rotor)
    interp_rotor = interp1d(
        np.concatenate([theta_rotor[sort_idx_r]-2*np.pi, theta_rotor[sort_idx_r], theta_rotor[sort_idx_r]+2*np.pi]),
        np.concatenate([r_rotor[sort_idx_r]]*3), kind='linear', fill_value='extrapolate'
    )
    r_rotor_sector = interp_rotor(theta_sector)
    A_i = 0.5 * trapezoid(r_rotor_sector**2, theta_sector)
    
    theta_rotor_original = np.arctan2(y_rotor_original, x_rotor_original)
    theta_L = theta_start % (2 * np.pi)
    theta_F = theta_end % (2 * np.pi)
    
    diff_L = np.minimum(np.abs(theta_rotor_original - theta_L), np.minimum(np.abs(theta_rotor_original - (theta_L - 2*np.pi)), np.abs(theta_rotor_original - (theta_L + 2*np.pi))))
    idx_L = np.argmin(diff_L)
    diff_F = np.minimum(np.abs(theta_rotor_original - theta_F), np.minimum(np.abs(theta_rotor_original - (theta_F - 2*np.pi)), np.abs(theta_rotor_original - (theta_F + 2*np.pi))))
    idx_F = np.argmin(diff_F)
    
    x_L, y_L = x_rotor_original[idx_L], y_rotor_original[idx_L]
    x_F, y_F = x_rotor_original[idx_F], y_rotor_original[idx_F]
    
    term_L = x_L * np.sin(theta_start) + y_L * np.cos(theta_start)
    term_F = x_F * np.sin(theta_end) + y_F * np.cos(theta_end)
    A_c = (excentricite / 2) * (term_L - term_F)
    
    A_chamber = A_o - A_i - A_c
    
    return {
        'A_chamber': A_chamber, 'A_o': A_o, 'A_i': A_i, 'A_c': A_c,
        'theta_start': theta_start, 'theta_end': theta_end,
        'x_stator': r_stator_sector * np.cos(theta_sector),
        'y_stator': r_stator_sector * np.sin(theta_sector),
        'x_rotor': r_rotor_sector * np.cos(theta_sector),
        'y_rotor': r_rotor_sector * np.sin(theta_sector)
    }

def generate_gerotor_profiles(m_param, e_param, d_param, n_points=2000):
    me_param = m_param * e_param
    b_param = e_param - d_param
    
    phi1_max = np.pi * d_param / me_param 
    phi1_min = -np.pi * d_param / me_param
    phi1 = np.linspace(phi1_min, phi1_max, n_points)
    x1 = (me_param - d_param) * np.cos(phi1) - d_param * np.cos((me_param/d_param - 1) * phi1)
    y1 = (me_param - d_param) * np.sin(phi1) + d_param * np.sin((me_param/d_param - 1) * phi1)
    
    phi2_min = phi1_max
    phi2_max = (2*np.pi / m_param) - (np.pi*d_param/me_param) 
    phi2 = np.linspace(phi2_min, phi2_max, n_points)
    x2 = (me_param + b_param) * np.cos(phi2) - b_param * np.cos((me_param/b_param + 1) * phi2 - np.pi*d_param/b_param)
    y2 = (me_param + b_param) * np.sin(phi2) - b_param * np.sin((me_param/b_param + 1) * phi2 - np.pi*d_param/b_param)
    
    x_stator = np.concatenate([x1, x2]); y_stator = np.concatenate([y1, y2])
    
    phi1_Int_max = np.pi * d_param / ((m_param - 1) * e_param)
    phi1_Int_min = -np.pi * d_param / ((m_param - 1) * e_param)
    phi1_Int = np.linspace(phi1_Int_min, phi1_Int_max, n_points)
    xi1 = ((m_param - 1) * e_param - d_param) * np.cos(phi1_Int) - d_param * np.cos(((m_param - 1) * e_param / d_param - 1) * phi1_Int)
    eta1 = ((m_param - 1) * e_param - d_param) * np.sin(phi1_Int) + d_param * np.sin(((m_param - 1) * e_param / d_param - 1) * phi1_Int)
    
    phi2_Int_min = phi1_Int_max 
    phi2_int_max = 2*np.pi / (m_param - 1) - np.pi*d_param/((m_param-1)*e_param)
    phi2_int = np.linspace(phi2_Int_min, phi2_int_max, n_points)
    xi2 = ((m_param - 1) * e_param + b_param) * np.cos(phi2_int) - b_param * np.cos((((m_param - 1) * e_param / b_param + 1) * phi2_int - np.pi*d_param/b_param))
    eta2 = ((m_param - 1) * e_param + b_param) * np.sin(phi2_int) - b_param * np.sin((((m_param - 1) * e_param / b_param + 1) * phi2_int - np.pi*d_param/b_param))
    
    x_rotor = np.concatenate([xi1, xi2]); y_rotor = np.concatenate([eta1, eta2])
    return x_stator, y_stator, x_rotor, y_rotor

def calc_curvature_generic(x, y):
    dx, dy = np.gradient(x), np.gradient(y)
    d2x, d2y = np.gradient(dx), np.gradient(dy)
    num = (dx**2 + dy**2)**1.5
    den = np.abs(dx * d2y - dy * d2x)
    den[den < 1e-10] = 1e-10
    return num / den

def find_constriction(x_stator, y_stator, x_rotor, y_rotor):
    rho_stator = calc_curvature_generic(x_stator, y_stator)
    rho_rotor = calc_curvature_generic(x_rotor, y_rotor)
    pts_s = np.column_stack([x_stator, y_stator])
    pts_r = np.column_stack([x_rotor, y_rotor])
    distances = cdist(pts_s, pts_r)
    min_idx = np.unravel_index(np.argmin(distances), distances.shape)
    i_s, i_r = min_idx[0], min_idx[1]
    return {
        'min_dist': distances[i_s, i_r],
        'pt_stator': (x_stator[i_s], y_stator[i_s]),
        'pt_rotor': (x_rotor[i_r], y_rotor[i_r]),
        'rho_stator': rho_stator[i_s],
        'rho_rotor': rho_rotor[i_r]
    }

def calculer_A_star(m, e, d):
    try:
        rho = ((m * e - d) + ((m - 1) * e - d)) / 2
        xs, ys, xr, yr = generate_gerotor_profiles(m, e, d, 800)
        xs_f, ys_f = generate_full_profile(xs, ys, m)
        xr_o, yr_o = generate_full_profile(xr, yr, m - 1)
        chambers, _, _, _, _ = find_chamber_boundaries(xs_f, ys_f, xr_o + e, yr_o)
        if not chambers: return None
        
        areas = []
        for t_s, t_e in chambers:
            res = calculate_chamber_area_with_Ac_corrected(t_s, t_e, xs_f, ys_f, xr_o + e, yr_o, xr_o, yr_o, e, 150)
            if res['A_chamber'] > 0: areas.append(res['A_chamber'])
        return min(areas) / (rho**2) if areas else None
    except: return None

def lancer_analyse_hybride(m, e, d, h, N_rpm):
    x_stator_single, y_stator_single, x_rotor_single, y_rotor_single = generate_gerotor_profiles(m, e, d, 2000)
    
    n = m - 1
    
    # Ligne corrigée ! (On passe bien x_single et y_single)
    x_stator_full, y_stator_full = generate_full_profile(x_stator_single, y_stator_single, m)
    x_rotor_original, y_rotor_original = generate_full_profile(x_rotor_single, y_rotor_single, n)
    
    x_rotor_full = x_rotor_original + e
    y_rotor_full = y_rotor_original

    # 1. Chambres et volumes
    chamber_segments, _, _, _, _ = find_chamber_boundaries(x_stator_full, y_stator_full, x_rotor_full, y_rotor_full)
    chamber_details = []
    for theta_start, theta_end in chamber_segments:
        res = calculate_chamber_area_with_Ac_corrected(theta_start, theta_end, x_stator_full, y_stator_full, x_rotor_full, y_rotor_full, x_rotor_original, y_rotor_original, e)
        if res['A_chamber'] > 0: chamber_details.append(res)
        
    areas = [c['A_chamber'] for c in chamber_details]
    
    # --- CALCUL EXACT DES VOLUMES ET PERTES ---
    nb_chambres = len(areas)
    A_min = min(areas) if areas else 0
    A_max = max(areas) if areas else 0
    
    # Volume par chambre (mm³)
    V_max_chambre = A_max * h
    V_mort_chambre = A_min * h
    V_cyl_chambre = V_max_chambre - V_mort_chambre
    
    # Performances globales de la pompe
    V_cyl_totale = V_cyl_chambre * nb_chambres       # Cylindrée totale par tour (mm³/tr)
    V_mort_total_tr = V_mort_chambre * nb_chambres   # Volume mort recirculé par tour (mm³/tr)
    
    # Débits (L/min)
    Q_th_lpm = (V_cyl_totale * N_rpm) / 1_000_000.0
    Q_recirc_lpm = (V_mort_total_tr * N_rpm) / 1_000_000.0

    performances = {
        "V_cyl_totale": V_cyl_totale,  # mm³
        "V_mort_total": V_mort_total_tr, # mm³
        "V_max_ch": V_max_chambre,     # mm³
        "V_min_ch": V_mort_chambre,    # mm³
        "Q_th_lpm": Q_th_lpm,          # L/min
        "Q_recirc_lpm": Q_recirc_lpm,  # L/min
        "ratio_mort": (V_mort_total_tr / V_cyl_totale * 100) if V_cyl_totale > 0 else 0 # %
    }
    # ------------------------------------------

    constriction = find_constriction(x_stator_full, y_stator_full, x_rotor_full, y_rotor_full)
    rho_carac = (((m * e) - d) + ((m - 1) * e - d)) / 2
    stats = {
        "m_actuel": m,
        "lambda_d": d / rho_carac,
        "lambda_r": (m * e) / rho_carac,
        "lambda_e": e / rho_carac,
        "rho_carac": rho_carac,
        "A_star": A_min / (rho_carac**2) if rho_carac else 0
    }

    # Étude paramétrique
    param_res = {
        "ld_vs_d_x": [], "astar_d_y": [],
        "le_vs_e_x": [], "astar_e_y": [],
        "lr_vs_m_x": [], "m_vals_x": [], "astar_m_y": []
    }

    d_values = np.linspace(max(0.5, d * 0.5), d * 1.5, 12)
    for d_val in d_values:
        a_star = calculer_A_star(m, e, d_val)
        param_res["ld_vs_d_x"].append(d_val / rho_carac)
        param_res["astar_d_y"].append(a_star if a_star else np.nan)

    e_values = np.linspace(max(0.5, e * 0.5), e * 1.5, 12)
    for e_val in e_values:
        a_star = calculer_A_star(m, e_val, d)
        rho_temp = ((m * e_val - d) + ((m - 1) * e_val - d)) / 2
        param_res["le_vs_e_x"].append(e_val / rho_temp if rho_temp else np.nan)
        param_res["astar_e_y"].append(a_star if a_star else np.nan)

    m_values = np.arange(max(3, m - 3), m + 4)
    for m_val in m_values:
        a_star = calculer_A_star(m_val, e, d)
        rho_temp = ((m_val * e - d) + ((m_val - 1) * e - d)) / 2
        param_res["lr_vs_m_x"].append((m_val * e) / rho_temp if rho_temp else np.nan)
        param_res["m_vals_x"].append(m_val)
        param_res["astar_m_y"].append(a_star if a_star else np.nan)

    return {
        "geometrie": {
            "x_stator_full": x_stator_full, "y_stator_full": y_stator_full,
            "x_rotor_original": x_rotor_original, "y_rotor_original": y_rotor_original,
            "x_rotor_full": x_rotor_full, "y_rotor_full": y_rotor_full,
            "chambres": chamber_details
        },
        "performances": performances,
        "parametrique": param_res,
        "stats": stats,
        "constriction": constriction
    }