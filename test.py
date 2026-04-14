import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import trapezoid
from scipy.interpolate import interp1d
from scipy.spatial.distance import cdist

# ========== PARAMÈTRES DU GEROTOR ==========
m = 4     # nombre de lobes du stator
e = 3.75    # excentricité (mm)
d = 2.5     # paramètre du cercle générateur d (mm)
h = 20      # longueur axiale du gerotor (mm)

n = m - 1   # nombre de lobes du rotor
me = m * e
b = e - d
n_points = 2000

# ========== PROFIL EXTERNE - STATOR ==========
print("Génération du profil EXTERNE (STATOR)...")

phi1_max = np.pi * d / me 
phi1_min = -np.pi * d / me
phi1 = np.linspace(phi1_min, phi1_max, n_points)

x1 = (me - d) * np.cos(phi1) - d * np.cos((me/d - 1) * phi1)
y1 = (me - d) * np.sin(phi1) + d * np.sin((me/d - 1) * phi1)

phi2_min = phi1_max
phi2_max = (2*np.pi / m) - (np.pi*d/me) 
phi2 = np.linspace(phi2_min, phi2_max, n_points)

x2 = (me + b) * np.cos(phi2) - b * np.cos((me/b + 1) * phi2 - np.pi*d/b)
y2 = (me + b) * np.sin(phi2) - b * np.sin((me/b + 1) * phi2 - np.pi*d/b)

x_stator_single = np.concatenate([x1, x2])
y_stator_single = np.concatenate([y1, y2])
phi_stator_single = np.concatenate([phi1, phi2])

# ========== PROFIL INTERNE - ROTOR ==========
print("Génération du profil INTERNE (ROTOR)...")

phi1_Int_max = np.pi * d / ((m - 1) * e)
phi1_Int_min = -np.pi * d / ((m - 1) * e)
phi1_Int = np.linspace(phi1_Int_min, phi1_Int_max, n_points)

xi1 = ((m - 1) * e - d) * np.cos(phi1_Int) - d * np.cos(((m - 1) * e / d - 1) * phi1_Int)
eta1 = ((m - 1) * e - d) * np.sin(phi1_Int) + d * np.sin(((m - 1) * e / d - 1) * phi1_Int)

phi2_Int_min = phi1_Int_max 
phi2_int_max = 2*np.pi / (m - 1) - np.pi*d/((m-1)*e)
phi2_int = np.linspace(phi2_Int_min, phi2_int_max, n_points)

xi2 = ((m - 1) * e + b) * np.cos(phi2_int) - b * np.cos((((m - 1) * e / b + 1) * phi2_int - np.pi*d/b))
eta2 = ((m - 1) * e + b) * np.sin(phi2_int) - b * np.sin((((m - 1) * e / b + 1) * phi2_int - np.pi*d/b))

x_rotor_single = np.concatenate([xi1, xi2])
y_rotor_single = np.concatenate([eta1, eta2])
phi_rotor_single = np.concatenate([phi1_Int, phi2_int])

# ========== FONCTIONS UTILES ==========

def generate_full_profile(x_single, y_single, num_lobes, rotation_angle=0):
    """Génère le profil complet avec rotation"""
    x_full = []
    y_full = []
    
    for i in range(num_lobes):
        angle = 2 * np.pi * i / num_lobes + rotation_angle
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        x_rot = x_single * cos_a - y_single * sin_a
        y_rot = x_single * sin_a + y_single * cos_a
        
        x_full.extend(x_rot)
        y_full.extend(y_rot)
    
    return np.array(x_full), np.array(y_full)

def calculate_curvature_radius(phi, x, y):
    """Calcule le rayon de courbure pour une courbe paramétrique"""
    dphi = phi[1] - phi[0]
    
    dx_dphi = np.gradient(x, dphi)
    dy_dphi = np.gradient(y, dphi)
    
    d2x_dphi2 = np.gradient(dx_dphi, dphi)
    d2y_dphi2 = np.gradient(dy_dphi, dphi)
    
    numerator = (dx_dphi**2 + dy_dphi**2)**(3/2)
    denominator = np.abs(dx_dphi * d2y_dphi2 - dy_dphi * d2x_dphi2)
    
    denominator = np.where(denominator < 1e-10, 1e-10, denominator)
    
    rho = numerator / denominator
    
    return rho, dx_dphi, dy_dphi, d2x_dphi2, d2y_dphi2

def find_constriction_simple(x_stator, y_stator, x_rotor, y_rotor, rho_stator, rho_rotor, clearance):
    """Trouve le point de constriction"""
    points_stator = np.column_stack([x_stator, y_stator])
    points_rotor = np.column_stack([x_rotor, y_rotor])
    
    distances = cdist(points_stator, points_rotor)
    
    min_idx = np.unravel_index(np.argmin(distances), distances.shape)
    idx_stator = min_idx[0]
    idx_rotor = min_idx[1]
    min_distance = distances[idx_stator, idx_rotor]
    
    rho_s = rho_stator[idx_stator]
    rho_r = rho_rotor[idx_rotor]
    
    if rho_s > 0 and rho_r > 0:
        Rc_harmonic = 2 * rho_s * rho_r / (rho_s + rho_r)
    else:
        Rc_harmonic = max(rho_s, rho_r)
    
    Rc_diff = abs(rho_s - rho_r)
    Rc_min = min(rho_s, rho_r)
    
    jeu = min_distance - clearance if min_distance > clearance else min_distance
    
    lambda_harmonic = jeu / Rc_harmonic if Rc_harmonic > 0 else np.inf
    lambda_diff = jeu / Rc_diff if Rc_diff > 0 else np.inf
    lambda_min = jeu / Rc_min if Rc_min > 0 else np.inf
    
    return {
        'min_distance': min_distance,
        'jeu': jeu,
        'idx_stator': idx_stator,
        'idx_rotor': idx_rotor,
        'x_stator': x_stator[idx_stator],
        'y_stator': y_stator[idx_stator],
        'x_rotor': x_rotor[idx_rotor],
        'y_rotor': y_rotor[idx_rotor],
        'rho_stator': rho_s,
        'rho_rotor': rho_r,
        'Rc_harmonic': Rc_harmonic,
        'Rc_diff': Rc_diff,
        'Rc_min': Rc_min,
        'lambda_harmonic': lambda_harmonic,
        'lambda_diff': lambda_diff,
        'lambda_min': lambda_min
    }

def find_chamber_boundaries(x_stator_full, y_stator_full, x_rotor_full, y_rotor_full, n_angles=3600):
    """Identifie automatiquement les frontières des chambres"""
    theta_sweep = np.linspace(0, 2*np.pi, n_angles)
    
    theta_stator = np.arctan2(y_stator_full, x_stator_full)
    r_stator = np.sqrt(x_stator_full**2 + y_stator_full**2)
    
    sort_idx_stator = np.argsort(theta_stator)
    theta_stator_sorted = theta_stator[sort_idx_stator]
    r_stator_sorted = r_stator[sort_idx_stator]
    
    theta_stator_ext = np.concatenate([theta_stator_sorted - 2*np.pi, 
                                       theta_stator_sorted, 
                                       theta_stator_sorted + 2*np.pi])
    r_stator_ext = np.concatenate([r_stator_sorted, r_stator_sorted, r_stator_sorted])
    
    interp_stator = interp1d(theta_stator_ext, r_stator_ext, kind='linear', 
                            bounds_error=False, fill_value='extrapolate')
    r_stator_sweep = interp_stator(theta_sweep)
    
    theta_rotor = np.arctan2(y_rotor_full, x_rotor_full)
    r_rotor = np.sqrt(x_rotor_full**2 + y_rotor_full**2)
    
    sort_idx_rotor = np.argsort(theta_rotor)
    theta_rotor_sorted = theta_rotor[sort_idx_rotor]
    r_rotor_sorted = r_rotor[sort_idx_rotor]
    
    theta_rotor_ext = np.concatenate([theta_rotor_sorted - 2*np.pi, 
                                      theta_rotor_sorted, 
                                      theta_rotor_sorted + 2*np.pi])
    r_rotor_ext = np.concatenate([r_rotor_sorted, r_rotor_sorted, r_rotor_sorted])
    
    interp_rotor = interp1d(theta_rotor_ext, r_rotor_ext, kind='linear', 
                           bounds_error=False, fill_value='extrapolate')
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

def calculate_chamber_area_with_Ac_corrected(theta_start, theta_end,
                                             x_stator_full, y_stator_full,
                                             x_rotor_full, y_rotor_full,
                                             x_rotor_original, y_rotor_original,
                                             excentricite, n_angles=500):
    
    if theta_end < theta_start:
        theta_end += 2 * np.pi
    theta_sector = np.linspace(theta_start, theta_end, n_angles)
    
    # A_o (STATOR)
    theta_stator = np.arctan2(y_stator_full, x_stator_full)
    r_stator = np.sqrt(x_stator_full**2 + y_stator_full**2)
    
    sort_idx = np.argsort(theta_stator)
    theta_stator_sorted = theta_stator[sort_idx]
    r_stator_sorted = r_stator[sort_idx]
    
    theta_stator_ext = np.concatenate([theta_stator_sorted - 2*np.pi, 
                                       theta_stator_sorted, 
                                       theta_stator_sorted + 2*np.pi])
    r_stator_ext = np.concatenate([r_stator_sorted, r_stator_sorted, r_stator_sorted])
    
    interp_stator = interp1d(theta_stator_ext, r_stator_ext, kind='linear', 
                            bounds_error=False, fill_value='extrapolate')
    r_stator_sector = interp_stator(theta_sector)
    
    A_o = 0.5 * trapezoid(r_stator_sector**2, theta_sector)
    
    # A_i (ROTOR)
    theta_rotor = np.arctan2(y_rotor_full, x_rotor_full)
    r_rotor = np.sqrt(x_rotor_full**2 + y_rotor_full**2)
    
    sort_idx = np.argsort(theta_rotor)
    theta_rotor_sorted = theta_rotor[sort_idx]
    r_rotor_sorted = r_rotor[sort_idx]
    
    theta_rotor_ext = np.concatenate([theta_rotor_sorted - 2*np.pi, 
                                      theta_rotor_sorted, 
                                      theta_rotor_sorted + 2*np.pi])
    r_rotor_ext = np.concatenate([r_rotor_sorted, r_rotor_sorted, r_rotor_sorted])
    
    interp_rotor = interp1d(theta_rotor_ext, r_rotor_ext, kind='linear', 
                           bounds_error=False, fill_value='extrapolate')
    r_rotor_sector = interp_rotor(theta_sector)
    
    A_i = 0.5 * trapezoid(r_rotor_sector**2, theta_sector)
    
    # A_c (correction d'asymétrie)
    theta_rotor_original = np.arctan2(y_rotor_original, x_rotor_original)
    
    theta_L = theta_start % (2 * np.pi)
    theta_F = theta_end % (2 * np.pi)
    
    diff_L = np.abs(theta_rotor_original - theta_L)
    diff_L_alt = np.abs(theta_rotor_original - (theta_L - 2*np.pi))
    diff_L_alt2 = np.abs(theta_rotor_original - (theta_L + 2*np.pi))
    diff_L = np.minimum(np.minimum(diff_L, diff_L_alt), diff_L_alt2)
    idx_L = np.argmin(diff_L)
    
    diff_F = np.abs(theta_rotor_original - theta_F)
    diff_F_alt = np.abs(theta_rotor_original - (theta_F - 2*np.pi))
    diff_F_alt2 = np.abs(theta_rotor_original - (theta_F + 2*np.pi))
    diff_F = np.minimum(np.minimum(diff_F, diff_F_alt), diff_F_alt2)
    idx_F = np.argmin(diff_F)
    
    x_L = x_rotor_original[idx_L]
    y_L = y_rotor_original[idx_L]
    x_F = x_rotor_original[idx_F]
    y_F = y_rotor_original[idx_F]
    
    term_L = x_L * np.sin(theta_start) + y_L * np.cos(theta_start)
    term_F = x_F * np.sin(theta_end) + y_F * np.cos(theta_end)
    A_c = (excentricite / 2) * (term_L - term_F)
    
    A_chamber = A_o - A_i - A_c
    
    x_stator_sector = r_stator_sector * np.cos(theta_sector)
    y_stator_sector = r_stator_sector * np.sin(theta_sector)
    x_rotor_sector = r_rotor_sector * np.cos(theta_sector)
    y_rotor_sector = r_rotor_sector * np.sin(theta_sector)
    
    return {
        'A_chamber': A_chamber,
        'A_o': A_o,
        'A_i': A_i,
        'A_c': A_c,
        'theta_start': theta_start,
        'theta_end': theta_end,
        'x_stator': x_stator_sector,
        'y_stator': y_stator_sector,
        'x_rotor': x_rotor_sector,
        'y_rotor': y_rotor_sector,
        'r_stator_sector': r_stator_sector,
        'r_rotor_sector': r_rotor_sector,
        'points_Ac': {
            'x_L': x_L,
            'y_L': y_L,
            'x_F': x_F,
            'y_F': y_F,
            'theta_L': theta_start,
            'theta_F': theta_end,
            'term_L': term_L,
            'term_F': term_F
        }
    }

def generate_gerotor_profiles(m_param, e_param, d_param, n_points=2000):
    n_param = m_param - 1
    me_param = m_param * e_param
    b_param = e_param - d_param
    
    # PROFIL STATOR
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
    
    x_stator = np.concatenate([x1, x2])
    y_stator = np.concatenate([y1, y2])
    phi_stator = np.concatenate([phi1, phi2])
    
    # PROFIL ROTOR
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
    
    x_rotor = np.concatenate([xi1, xi2])
    y_rotor = np.concatenate([eta1, eta2])
    phi_rotor = np.concatenate([phi1_Int, phi2_int])
    
    return {
        'x_stator': x_stator,
        'y_stator': y_stator,
        'phi_stator': phi_stator,
        'x_rotor': x_rotor,
        'y_rotor': y_rotor,
        'phi_rotor': phi_rotor,
        'm': m_param,
        'n': n_param,
        'e': e_param,
        'd': d_param
    }

def calculate_min_chamber_area_and_lambdas(m_param, e_param, d_param):
    """Calcule l'aire de la plus petite chambre et les paramètres λ"""
    try:
        me_param = m_param * e_param
        r_base_outer = me_param - d_param
        r_base_inner = (m_param - 1) * e_param - d_param
        rho_param = (r_base_outer + r_base_inner) / 2
        r_param = me_param
        
        lambda_d = d_param / rho_param
        lambda_r = r_param / rho_param
        lambda_e = e_param * m_param / abs((r_param - rho_param) * np.cos(np.pi * d_param / r_param) - r_param)
        
        profiles = generate_gerotor_profiles(m_param, e_param, d_param)
        
        x_stator_full, y_stator_full = generate_full_profile(
            profiles['x_stator'], profiles['y_stator'], m_param, 0.0
        )
        
        x_rotor_original, y_rotor_original = generate_full_profile(
            profiles['x_rotor'], profiles['y_rotor'], m_param - 1, 0.0
        )
        
        x_rotor_full = x_rotor_original + e_param
        y_rotor_full = y_rotor_original
        
        chamber_segments, _, _, _, _ = find_chamber_boundaries(
            x_stator_full, y_stator_full, x_rotor_full, y_rotor_full
        )
        
        if len(chamber_segments) == 0:
            return None
        
        chamber_areas = []
        for theta_start, theta_end in chamber_segments:
            result = calculate_chamber_area_with_Ac_corrected(
                theta_start, theta_end,
                x_stator_full, y_stator_full,
                x_rotor_full, y_rotor_full,
                x_rotor_original, y_rotor_original,
                e_param
            )
            if result['A_chamber'] > 0:
                chamber_areas.append(result['A_chamber'])
        
        if len(chamber_areas) == 0:
            return None
        
        A_min = min(chamber_areas)
        A_star = A_min / (rho_param ** 2)
        
        return {
            'A_min': A_min,
            'A_star': A_star,
            'lambda_d': lambda_d,
            'lambda_r': lambda_r,
            'lambda_e': lambda_e,
            'rho': rho_param
        }
    
    except:
        return None

# ========== CALCUL PRINCIPAL ==========

rotor_angle_offset = 0.0
stator_angle_offset = 0.0

x_stator_full, y_stator_full = generate_full_profile(x_stator_single, y_stator_single, m, stator_angle_offset)
x_rotor_original, y_rotor_original = generate_full_profile(x_rotor_single, y_rotor_single, n, rotor_angle_offset)
x_rotor_full = x_rotor_original + e
y_rotor_full = y_rotor_original

chamber_segments, theta_sweep, r_stator_sweep, r_rotor_sweep, diff = find_chamber_boundaries(
    x_stator_full, y_stator_full, x_rotor_full, y_rotor_full
)

chamber_areas = []
chamber_details = []

for i, (theta_start, theta_end) in enumerate(chamber_segments):
    result = calculate_chamber_area_with_Ac_corrected(
        theta_start, theta_end,
        x_stator_full, y_stator_full,
        x_rotor_full, y_rotor_full,
        x_rotor_original, y_rotor_original,
        e
    )
    
    if result['A_chamber'] > 0:
        chamber_areas.append(result['A_chamber'])
        chamber_details.append(result)

# Calculs de cylindrée
total_chamber_area = sum(chamber_areas)
V_displaced_total = total_chamber_area * h
max_chamber_area = max(chamber_areas)
V_displaced_max = max_chamber_area * h

# Calculer les rayons caractéristiques
r_base_outer = me - d
r_base_inner = (m - 1) * e - d
rho = (r_base_outer + r_base_inner) / 2
r = me

# Calculer les paramètres λ
lambda_d = d / rho
lambda_r = r / rho
lambda_e_simple = e*m / abs((r-rho)*np.cos(np.pi*d/r)-r)

# Aire adimensionnelle
A_min_current = min(chamber_areas)
A_star_current = A_min_current / (rho ** 2)

# Calculer les rayons de courbure
rho_stator_single, dx_stator, dy_stator, d2x_stator, d2y_stator = calculate_curvature_radius(
    phi_stator_single, x_stator_single, y_stator_single
)

rho_rotor_single, dx_rotor, dy_rotor, d2x_rotor, d2y_rotor = calculate_curvature_radius(
    phi_rotor_single, x_rotor_single, y_rotor_single
)

clearance = 0.002 * 2 * me

constriction = find_constriction_simple(
    x_stator_single, y_stator_single,
    x_rotor_single, y_rotor_single,
    rho_stator_single, rho_rotor_single,
    clearance
)

# ========== AFFICHAGE DES RÉSULTATS  ==========

print(f"\n{'='*100}")
print("PARAMÈTRES DU GEROTOR")
print(f"{'='*100}")
print(f"  Nombre de lobes stator (m): {m}")
print(f"  Nombre de lobes rotor (n):  {n}")
print(f"  Excentricité (e):           {e} mm")
print(f"  Paramètre d:                {d} mm")
print(f"  Paramètre b:                {b} mm")
print(f"  Hauteur (h):                {h} mm")
print(f"\n  Rayon dedendum rotor:       {r_base_inner} mm")
print(f"  Rayon addendum rotor:       {r_base_inner + 2*b} mm")
print(f"  Hauteur de dent rotor:      {2*b} mm")

print(f"\n{'='*100}")
print("ANALYSE DÉTAILLÉE DES AIRES DES CHAMBRES")
print(f"{'='*100}\n")

print(f"1. TABLEAU DES COMPOSANTES D'AIRE")
print(f"{'-'*100}")
print(f"{'Chambre':^10} {'A_o (mm²)':^14} {'A_i (mm²)':^14} {'A_c (mm²)':^14} {'A_total (mm²)':^16} {'Marqueur':^20}")
print(f"{'-'*100}")

total_A_o = 0
total_A_i = 0
total_A_c = 0

for i, (area, details) in enumerate(zip(chamber_areas, chamber_details)):
    marker = ""
    if area == max_chamber_area:
        marker += "← MAX"
    if area == A_min_current:
        marker += " ← MIN" if marker else "← MIN"
    
    total_A_o += details['A_o']
    total_A_i += details['A_i']
    total_A_c += details['A_c']
    
    print(f"{i+1:^10d} {details['A_o']:>13.3f} {details['A_i']:>13.3f} {details['A_c']:>13.3f} {area:>15.3f}  {marker:<20}")

print(f"{'-'*100}")
print(f"{'TOTAL':^10} {total_A_o:>13.3f} {total_A_i:>13.3f} {total_A_c:>13.3f} {total_chamber_area:>15.3f}")
print(f"{'-'*100}")

print(f"\n2. STATISTIQUES DES AIRES")
print(f"{'-'*100}")
print(f"   Somme A_o (secteurs stator):       {total_A_o:>12.3f} mm²")
print(f"   Somme A_i (secteurs rotor):        {total_A_i:>12.3f} mm²")
print(f"   Somme A_c (corrections):           {total_A_c:>12.3f} mm²")
print(f"   Aire totale (Σ A_total):           {total_chamber_area:>12.3f} mm²")
print(f"\n   Aire moyenne par chambre:          {np.mean(chamber_areas):>12.3f} mm²")
print(f"   Aire minimale:                     {min(chamber_areas):>12.3f} mm²")
print(f"   Aire maximale:                     {max(chamber_areas):>12.3f} mm²")
print(f"   Écart-type:                        {np.std(chamber_areas):>12.3f} mm²")

print(f"\n3. VÉRIFICATION DE LA FORMULE A_total = A_o - A_i - A_c")
print(f"{'-'*100}")
for i, details in enumerate(chamber_details):
    A_calculated = details['A_o'] - details['A_i'] - details['A_c']
    A_stored = details['A_chamber']
    error = abs(A_calculated - A_stored)
    error_pct = (error / A_stored * 100) if A_stored > 0 else 0
    print(f"   Chambre {i+1}: Calculée = {A_calculated:>10.3f} mm²  |  Stockée = {A_stored:>10.3f} mm²  |  Erreur = {error:>8.6f} mm² ({error_pct:.4f}%)")

print(f"\n4. ANALYSE DES TERMES A_c (Équation 4.7)")
print(f"{'-'*100}")
print(f"   Rappel: A_c = (e/2) × (term_L - term_F)")
print(f"   avec term_L = x_L × sin(θ_L) + y_L × cos(θ_L)")
print(f"   et   term_F = x_F × sin(θ_F) + y_F × cos(θ_F)\n")
print(f"{'Chambre':^10} {'θ_L (rad)':^12} {'θ_F (rad)':^12} {'term_L':^12} {'term_F':^12} {'Δterm':^12} {'A_c (mm²)':^12}")
print(f"{'-'*100}")

for i, details in enumerate(chamber_details):
    pts_Ac = details['points_Ac']
    delta_term = pts_Ac['term_L'] - pts_Ac['term_F']
    print(f"{i+1:^10d} {pts_Ac['theta_L']:>11.4f} {pts_Ac['theta_F']:>11.4f} {pts_Ac['term_L']:>11.4f} {pts_Ac['term_F']:>11.4f} {delta_term:>11.4f} {details['A_c']:>11.3f}")

print(f"\n{'='*100}")
print("PARAMÈTRES ADIMENSIONNELS")
print(f"{'='*100}")
print(f"  λ_d = d/ρ:                  {lambda_d:.6f}")
print(f"  λ_r = r/ρ:                  {lambda_r:.6f}")
print(f"  λ_e = e/ρ (simple):         {e/rho:.6f}")
print(f"  A* = A_min/ρ²:              {A_star_current:.6f}")

print(f"\n{'='*100}")
print("CYLINDRÉE")
print(f"{'='*100}")
print(f"  Nombre de chambres:         {len(chamber_areas)}")
print(f"  Cylindrée (méthode 1):      {V_displaced_total/1000:.3f} cm³ = {V_displaced_total:.3f} mm³")
print(f"  Cylindrée (méthode 2):      {V_displaced_max/1000:.3f} cm³ = {V_displaced_max:.3f} mm³")

# ========== ÉTUDE PARAMÉTRIQUE ADIMENSIONNELLE ==========
print(f"\n{'='*80}")
print("CALCUL DE L'ÉTUDE PARAMÉTRIQUE...")
print(f"{'='*80}")

e_ref = 3.75
d_ref = 2.5
m_ref = 7

# 1. Variation de λ_d (via d)
print("   Variation de λ_d...")
d_values = np.linspace(1.5, 5.5, 25)
lambda_d_values = []
A_star_vs_lambda_d = []

for d_val in d_values:
    result = calculate_min_chamber_area_and_lambdas(m_ref, e_ref, d_val)
    if result is not None:
        lambda_d_values.append(result['lambda_d'])
        A_star_vs_lambda_d.append(result['A_star'])
    else:
        lambda_d_values.append(np.nan)
        A_star_vs_lambda_d.append(np.nan)

# 2. Variation de λ_e SIMPLE (via e)
print("   Variation de λ_e (simple: e/ρ)...")
e_values = np.linspace(2.0, 8.0, 25)
lambda_e_simple_values = []
A_star_vs_lambda_e_simple = []

for e_val in e_values:
    result = calculate_min_chamber_area_and_lambdas(m_ref, e_val, d_ref)
    if result is not None:
        lambda_e_simple = e_val / result['rho']
        lambda_e_simple_values.append(lambda_e_simple)
        A_star_vs_lambda_e_simple.append(result['A_star'])
    else:
        lambda_e_simple_values.append(np.nan)
        A_star_vs_lambda_e_simple.append(np.nan)

# 3. Variation de λ_r (via m) 
print("   Variation de λ_r (via m)...")
m_values = np.arange(5, 13)
lambda_r_values = []
A_star_vs_lambda_r = []

for m_val in m_values:
    result = calculate_min_chamber_area_and_lambdas(m_val, e_ref, d_ref)
    if result is not None:
        lambda_r_values.append(result['lambda_r'])
        A_star_vs_lambda_r.append(result['A_star'])
    else:
        lambda_r_values.append(np.nan)
        A_star_vs_lambda_r.append(np.nan)

# 4. Variation du nombre de dents m
print("   Variation du nombre de dents m...")
A_star_vs_m = []

for m_val in m_values:
    result = calculate_min_chamber_area_and_lambdas(m_val, e_ref, d_ref)
    if result is not None:
        A_star_vs_m.append(result['A_star'])
    else:
        A_star_vs_m.append(np.nan)

print("\n✓ Calculs terminés")

# Calculer λ_e simple actuel
lambda_e_simple_current = e / rho

# ========== VISUALISATION ==========

# Figure 1: Géométrie du Rotor COMPLET
fig1 = plt.figure(figsize=(10, 10))
ax1 = fig1.add_subplot(111)
ax1.plot(x_rotor_original, y_rotor_original, 'b-', linewidth=2, label=f'Rotor complet (n={n})')
ax1.plot(0, 0, 'bo', markersize=10, label='Centre', zorder=5)
lobe_colors = plt.cm.tab10(np.linspace(0, 1, n))
for i in range(n):
    start_idx = i * len(x_rotor_single)
    end_idx = (i + 1) * len(x_rotor_single)
    if end_idx <= len(x_rotor_original):
        ax1.plot(x_rotor_original[start_idx:end_idx], 
                 y_rotor_original[start_idx:end_idx], 
                 color=lobe_colors[i], linewidth=1.5, alpha=0.7)
r_max_rotor = np.max(np.sqrt(x_rotor_original**2 + y_rotor_original**2))
margin = r_max_rotor * 1.15
ax1.set_xlim(-margin, margin)
ax1.set_ylim(-margin, margin)
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)
ax1.set_xlabel('x (mm)', fontsize=12, fontweight='bold')
ax1.set_ylabel('y (mm)', fontsize=12, fontweight='bold')
ax1.set_title(f'Profil COMPLET du ROTOR - {n} lobes', fontsize=14, fontweight='bold')
ax1.legend(fontsize=11)
plt.tight_layout()
plt.show()

# Figure 2: Géométrie du Stator COMPLET
fig2 = plt.figure(figsize=(10, 10))
ax2 = fig2.add_subplot(111)
ax2.plot(x_stator_full, y_stator_full, 'r-', linewidth=2, label=f'Stator complet (m={m})')
ax2.plot(0, 0, 'ro', markersize=10, label='Centre', zorder=5)
lobe_colors_stator = plt.cm.tab10(np.linspace(0, 1, m))
for i in range(m):
    start_idx = i * len(x_stator_single)
    end_idx = (i + 1) * len(x_stator_single)
    if end_idx <= len(x_stator_full):
        ax2.plot(x_stator_full[start_idx:end_idx], 
                 y_stator_full[start_idx:end_idx], 
                 color=lobe_colors_stator[i], linewidth=1.5, alpha=0.7)
r_max_stator = np.max(np.sqrt(x_stator_full**2 + y_stator_full**2))
margin = r_max_stator * 1.15
ax2.set_xlim(-margin, margin)
ax2.set_ylim(-margin, margin)
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)
ax2.set_xlabel('x (mm)', fontsize=12, fontweight='bold')
ax2.set_ylabel('y (mm)', fontsize=12, fontweight='bold')
ax2.set_title(f'Profil COMPLET du STATOR - {m} lobes', fontsize=14, fontweight='bold')
ax2.legend(fontsize=11)
plt.tight_layout()
plt.show()

# Figure 3: Géométrie Rotor + Stator assemblés (CENTRÉ)
fig3 = plt.figure(figsize=(12, 12))
ax3 = fig3.add_subplot(111)

ax3.plot(x_stator_full, y_stator_full, 'r-', linewidth=2.5, alpha=0.7, label=f'Stator (m={m})')
ax3.plot(x_rotor_full, y_rotor_full, 'b-', linewidth=2.5, alpha=0.7, label=f'Rotor (n={n})')

chamber_colors = plt.cm.rainbow(np.linspace(0, 1, len(chamber_details)))
for i, chamber in enumerate(chamber_details):
    ax3.plot(chamber['x_stator'], chamber['y_stator'], color=chamber_colors[i], linewidth=3, alpha=0.9)
    ax3.plot(chamber['x_rotor'], chamber['y_rotor'], color=chamber_colors[i], linewidth=3, linestyle='--', alpha=0.9)
    
    center_x = (np.mean(chamber['x_stator']) + np.mean(chamber['x_rotor'])) / 2
    center_y = (np.mean(chamber['y_stator']) + np.mean(chamber['y_rotor'])) / 2
    ax3.text(center_x, center_y, f'{i+1}', 
            fontsize=12, fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                     edgecolor=chamber_colors[i], linewidth=2, alpha=0.95))

ax3.plot(0, 0, 'ro', markersize=12, zorder=5, label='Centre stator')
ax3.plot(e, 0, 'bo', markersize=12, zorder=5, label=f'Centre rotor')
ax3.plot([0, e], [0, 0], 'g--', linewidth=2, alpha=0.5, label=f'Excentricité e={e} mm')

all_x = np.concatenate([x_stator_full, x_rotor_full])
all_y = np.concatenate([y_stator_full, y_rotor_full])
x_min, x_max = np.min(all_x), np.max(all_x)
y_min, y_max = np.min(all_y), np.max(all_y)

x_center = (x_min + x_max) / 2
y_center = (y_min + y_max) / 2
x_range = x_max - x_min
y_range = y_max - y_min
max_range = max(x_range, y_range) * 1.1

ax3.set_xlim(x_center - max_range/2, x_center + max_range/2)
ax3.set_ylim(y_center - max_range/2, y_center + max_range/2)
ax3.set_aspect('equal')
ax3.grid(True, alpha=0.3)
ax3.set_xlabel('x (mm)', fontsize=12, fontweight='bold')
ax3.set_ylabel('y (mm)', fontsize=12, fontweight='bold')
ax3.set_title(f'Assemblage STATOR + ROTOR - {len(chamber_areas)} chambres\nCylindrée: V = {V_displaced_total/1000:.2f} cm³ (somme) | {V_displaced_max/1000:.2f} cm³ (max)', 
             fontsize=14, fontweight='bold')
ax3.legend(fontsize=10, loc='upper right')
plt.tight_layout()
plt.show()

# Figure 4: Étude paramétrique adimensionnelle (4 graphiques en 2x2)
fig4 = plt.figure(figsize=(16, 12))

# Graphique 1: A* vs λ_d
ax1 = plt.subplot(2, 2, 1)
valid_idx = ~np.isnan(lambda_d_values) & ~np.isnan(A_star_vs_lambda_d)
ax1.plot(np.array(lambda_d_values)[valid_idx], np.array(A_star_vs_lambda_d)[valid_idx], 
         'o-', linewidth=2.5, markersize=8, color='blue', 
         markerfacecolor='lightblue', markeredgewidth=2)
ax1.axvline(lambda_d, color='red', linestyle='--', linewidth=2, alpha=0.7, 
            label=f'Actuel: λ_d = {lambda_d:.4f}')
ax1.set_xlabel('λ_d = d/ρ', fontsize=12, fontweight='bold')
ax1.set_ylabel('A* = A_min/ρ²', fontsize=12, fontweight='bold')
ax1.set_title(f'A* vs λ_d\n(m={m_ref}, e={e_ref} mm)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)

# Graphique 2: A* vs λ_e SIMPLE
ax2 = plt.subplot(2, 2, 2)
valid_idx = ~np.isnan(lambda_e_simple_values) & ~np.isnan(A_star_vs_lambda_e_simple)
ax2.plot(np.array(lambda_e_simple_values)[valid_idx], np.array(A_star_vs_lambda_e_simple)[valid_idx], 
         'o-', linewidth=2.5, markersize=8, color='green', 
         markerfacecolor='lightgreen', markeredgewidth=2)
ax2.axvline(lambda_e_simple_current, color='red', linestyle='--', linewidth=2, alpha=0.7, 
            label=f'Actuel: λ_e = {lambda_e_simple_current:.4f}')
ax2.set_xlabel('λ_e = e/ρ (simple)', fontsize=12, fontweight='bold')
ax2.set_ylabel('A* = A_min/ρ²', fontsize=12, fontweight='bold')
ax2.set_title(f'A* vs λ_e simple\n(m={m_ref}, d={d_ref} mm)', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)

# Graphique 3: A* vs λ_r 
ax3 = plt.subplot(2, 2, 3)
valid_idx = ~np.isnan(lambda_r_values) & ~np.isnan(A_star_vs_lambda_r)
ax3.plot(np.array(lambda_r_values)[valid_idx], np.array(A_star_vs_lambda_r)[valid_idx], 
         'o-', linewidth=2.5, markersize=8, color='orange', 
         markerfacecolor='lightyellow', markeredgewidth=2)
ax3.axvline(lambda_r, color='red', linestyle='--', linewidth=2, alpha=0.7, 
            label=f'Actuel: λ_r = {lambda_r:.4f}')
ax3.set_xlabel('λ_r = r/ρ (rapport de rayons)', fontsize=12, fontweight='bold')
ax3.set_ylabel('A* = A_min/ρ²', fontsize=12, fontweight='bold')
ax3.set_title(f'A* vs λ_r\n(e={e_ref} mm, d={d_ref} mm)', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.legend(fontsize=10)

# Graphique 4: A* vs m
ax4 = plt.subplot(2, 2, 4)
valid_idx = ~np.isnan(A_star_vs_m)
ax4.plot(m_values[valid_idx], np.array(A_star_vs_m)[valid_idx], 
         'o-', linewidth=2.5, markersize=10, color='purple', 
         markerfacecolor='plum', markeredgewidth=2)
ax4.axvline(m_ref, color='red', linestyle='--', linewidth=2, alpha=0.7, 
            label=f'Actuel: m = {m_ref}')
ax4.set_xlabel('Nombre de dents m', fontsize=12, fontweight='bold')
ax4.set_ylabel('A* = A_min/ρ²', fontsize=12, fontweight='bold')
ax4.set_title(f'A* vs nombre de dents\n(e={e_ref} mm, d={d_ref} mm)', fontsize=13, fontweight='bold')
ax4.set_xticks(m_values)
ax4.grid(True, alpha=0.3)
ax4.legend(fontsize=10)

plt.suptitle('ÉTUDE PARAMÉTRIQUE ADIMENSIONNELLE', 
             fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.show()

print(f"\n{'='*80}")
print("✓ TOUS LES CALCULS ET VISUALISATIONS SONT TERMINÉS")
print(f"{'='*80}")