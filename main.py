import customtkinter as ctk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from tkinter import PhotoImage
from methodes.utils_app import CTkSpinbox, exporter_csv, popup_export_step
from methodes import modeles_georotor as modeles

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GeorotorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Conception & Analyse Géorotor")
        self.geometry("1400x800")

        self.charger_icone()

        self.donnees_actives_X = None
        self.donnees_actives_Y = None
        self.donnees_actives_X_rotor = None
        self.donnees_actives_Y_rotor = None
        self.parametres_actifs = {}

        self.setup_ui()
        self.charger_methode("Paramétrique") 

    def charger_icone(self):
        try:
            chemin_actuel = os.path.dirname(os.path.abspath(__file__))
            chemin_icone = os.path.join(chemin_actuel, "assets", "icone.png")
            if os.path.exists(chemin_icone):
                self.icone_image = PhotoImage(file=chemin_icone)
                self.iconphoto(True, self.icone_image) 
        except: pass

    def setup_ui(self):
        self.onglets = ctk.CTkTabview(self)
        self.onglets.pack(padx=10, pady=10, fill="both", expand=True)
        self.onglet_conception = self.onglets.add("Conception")
        self.onglet_analyse = self.onglets.add("Analyse")

        self.onglet_conception.grid_columnconfigure(0, weight=0)
        self.onglet_conception.grid_columnconfigure(1, weight=1)
        self.onglet_conception.grid_rowconfigure(1, weight=1)

        # --- 1. BARRE SUPÉRIEURE ---
        top_bar = ctk.CTkFrame(self.onglet_conception, height=50)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(top_bar, text="Méthode :", font=("Arial", 14, "bold")).pack(side="left", padx=(20, 10))
        
        self.methode_var = ctk.StringVar(value="Paramétrique")
        ctk.CTkOptionMenu(top_bar, variable=self.methode_var, 
                          values=["Paramétrique", "Trochoïde", "Hybride"],
                          command=self.charger_methode).pack(side="left", padx=10)

        # --- 2. BARRE LATÉRALE ---
        self.sidebar = ctk.CTkScrollableFrame(self.onglet_conception, width=350)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.inputs = {}
        self.label_erreur = ctk.CTkLabel(self.sidebar, text="", text_color="red")

        # --- 3. ZONE GRAPHIQUE (COMPARTIMENTÉE) ---
        graph_container = ctk.CTkFrame(self.onglet_conception, fg_color="transparent")
        graph_container.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=10)

        self.titre_dynamique = ctk.CTkLabel(graph_container, text="", font=("Arial", 18, "bold"), text_color="#1f538d")
        self.titre_dynamique.pack(side="top", pady=(0, 10))
        
        frames_graphs = ctk.CTkFrame(graph_container, fg_color="transparent")
        frames_graphs.pack(expand=True, fill="both")
        
        frames_graphs.grid_columnconfigure(0, weight=1)
        frames_graphs.grid_columnconfigure(1, weight=1)
        frames_graphs.grid_rowconfigure(0, weight=1)

        # Graphique 1 : Profil Principal
        frame_profil = ctk.CTkFrame(frames_graphs, fg_color="white", corner_radius=10)
        frame_profil.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(frame_profil, text="Graphique Principal (Profils)", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10,0))
        
        self.fig_profil = Figure(figsize=(5, 4), dpi=100, facecolor='#ffffff')
        self.fig_profil.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.10)
        self.ax_profil = self.fig_profil.add_subplot(111)
        self.canvas_profil = FigureCanvasTkAgg(self.fig_profil, master=frame_profil)
        self.canvas_profil.get_tk_widget().pack(expand=True, fill="both", padx=5, pady=5)

        # Graphique 2 : Schéma des paramètres
        frame_schema = ctk.CTkFrame(frames_graphs, fg_color="white", corner_radius=10)
        frame_schema.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(frame_schema, text="Schéma des Paramètres", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10,0))
        
        self.fig_schema = Figure(figsize=(5, 4), dpi=100, facecolor='#ffffff')
        self.fig_schema.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.10)
        self.ax_schema = self.fig_schema.add_subplot(111)
        self.canvas_schema = FigureCanvasTkAgg(self.fig_schema, master=frame_schema)
        self.canvas_schema.get_tk_widget().pack(expand=True, fill="both", padx=5, pady=5)

        # --- 4. RUBAN D'EXPORT ET PARAMÈTRES GLOBAUX ---
        ribbon = ctk.CTkFrame(self.onglet_conception, height=60, corner_radius=0)
        ribbon.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        # Le nombre de points est maintenant placé ici
        ctk.CTkLabel(ribbon, text="Nb de points :", font=("Arial", 12, "bold")).pack(side="left", padx=(20, 5))
        self.spinbox_pts = CTkSpinbox(ribbon, step_size=100, width=110, command=self.generer_et_afficher)
        self.spinbox_pts.set(2000)
        self.spinbox_pts.pack(side="left", padx=5)

        # Séparateur visuel
        ctk.CTkFrame(ribbon, width=2, height=30, fg_color="gray").pack(side="left", padx=20)

        ctk.CTkLabel(ribbon, text="Cible d'export :", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 5))
        self.cible_export_var = ctk.StringVar(value="Stator")
        ctk.CTkOptionMenu(ribbon, variable=self.cible_export_var, values=["Stator", "Rotor"], width=90).pack(side="left", padx=5)

        ctk.CTkButton(ribbon, text="Exporter (CSV)", fg_color="transparent", border_width=2, text_color=("gray10", "gray90"),
                      command=self.action_exporter_csv).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(ribbon, text="Exporter Volume (STEP)", fg_color="#2b7b46", hover_color="#1e5c33",
                      command=self.action_exporter_step).pack(side="left", padx=10, pady=10)

    def charger_methode(self, methode_nom):
        # Nettoyage de la barre latérale
        for widget in self.sidebar.winfo_children(): widget.destroy()
        self.inputs.clear()
        
        self.sous_mode_var = ctk.StringVar()
        if methode_nom == "Paramétrique":
            self.sous_mode_var.set("Circulaire")
            ctk.CTkSegmentedButton(self.sidebar, variable=self.sous_mode_var, values=["Circulaire", "Elliptique", "Sinusoïdal"], command=self.changement_sous_mode).pack(pady=10, fill="x", padx=5)
            self.spinbox_pts.set(2000)
        elif methode_nom == "Trochoïde":
            self.sous_mode_var.set("Hypocycloïde")
            ctk.CTkSegmentedButton(self.sidebar, variable=self.sous_mode_var, values=["Hypocycloïde", "Épitrochoïde"], command=self.changement_sous_mode).pack(pady=10, fill="x", padx=5)
            self.spinbox_pts.set(3000)
        elif methode_nom == "Hybride":
            self.spinbox_pts.set(2000)

        # --- MÀJ CONFIGS : Les éléments spécifiques et la résolution sont retirés ---
        configs_base = {
            "Hybride": [("Géométrie", [("N_lobes", "Lobes stator", 8, 1), ("R_prim", "R. Générateur (R)", 12.0, 0.5), ("d_param", "Paramètre (d)", 1.2, 0.1)])],
            "Trochoïde": [("Géométrie", [("N_lobes", "Dents Stator (N)", 6, 1), ("R_prim", "R. Primitif (R)", 22.0, 0.5), ("d_traceur", "Dist. traceur (d)", 3, 0.25), ("rho_env", "Enveloppe (\u03C1)", 4.0, 0.1)])],
            "Paramétrique": [("Globaux", [("N_lobes", "Nb de cavités", 5, 1), ("R_prim", "Rayon primitif", 13.0, 0.5), ("R_ext", "Rayon extérieur", 10.0, 0.5), ("phi_deg", "Angle (°)", 0.0, 5.0)])]
        }

        # Création des champs communs
        for cat, champs in configs_base[methode_nom]:
            ctk.CTkLabel(self.sidebar, text=cat, font=("Arial", 12, "bold"), text_color="gray").pack(pady=(15,5), anchor="w", padx=10)
            for k, l, d, s in champs:
                f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=l, width=130, anchor="w").pack(side="left", padx=5)
                spinbox = CTkSpinbox(f, step_size=s, command=self.generer_et_afficher)
                spinbox.set(d); spinbox.pack(side="right", padx=5); self.inputs[k] = spinbox

        # Conteneur pour les paramètres spécifiques aux sous-modes
        self.frame_specifique = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_specifique.pack(fill="x", pady=5)

        self.label_erreur = ctk.CTkLabel(self.sidebar, text="", text_color="red", font=("Arial", 12, "bold"))
        self.label_erreur.pack(pady=10)
        
        # Appel initial pour afficher les bons sous-paramètres
        self.changement_sous_mode(self.sous_mode_var.get() if methode_nom != "Hybride" else "")

    def changement_sous_mode(self, sm):
        # Nettoyer les inputs spécifiques précédents
        for widget in self.frame_specifique.winfo_children(): 
            widget.destroy()
            
        # Supprimer les clés du dictionnaire pour éviter les résidus
        cles_a_supprimer = ["r_cercle", "a_ell", "b_ell", "A_sin", "T_sin"]
        for cle in cles_a_supprimer:
            self.inputs.pop(cle, None)
            
        methode = self.methode_var.get()
        champs_specifiques = []
        
        # Conditionne l'affichage selon le sous-modèle activé
        if methode == "Paramétrique":
            ctk.CTkLabel(self.frame_specifique, text="Spécifiques au profil", font=("Arial", 12, "bold"), text_color="gray").pack(pady=(10,5), anchor="w", padx=10)
            if sm == "Circulaire":
                champs_specifiques = [("r_cercle", "Rayon r (Circ)", 5.0, 0.5)]
            elif sm == "Elliptique":
                champs_specifiques = [("a_ell", "Prof a (Ell)", 5.0, 0.1), ("b_ell", "Largeur b (Ell)", 4.0, 0.1)]
            elif sm == "Sinusoïdal":
                champs_specifiques = [("A_sin", "Ampli A (Sin)", 5.0, 0.5), ("T_sin", "Période T (Sin)", 150.0, 10)]

        # Création des nouveaux inputs
        for k, l, d, s in champs_specifiques:
            f = ctk.CTkFrame(self.frame_specifique, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=l, width=130, anchor="w").pack(side="left", padx=5)
            spinbox = CTkSpinbox(f, step_size=s, command=self.generer_et_afficher)
            spinbox.set(d); spinbox.pack(side="right", padx=5); self.inputs[k] = spinbox
            
        self.generer_et_afficher()

    def generer_et_afficher(self):
        try:
            self.label_erreur.configure(text="")
            methode = self.methode_var.get()
            sm = self.sous_mode_var.get() if methode != "Hybride" else ""
            X, Y, X_rotor, Y_rotor = None, None, None, None
            X_gen, Y_gen = None, None

            titre_full = f"Visualisation de la méthode : {methode.upper()}" + (f" - {sm}" if sm else "")
            self.titre_dynamique.configure(text=titre_full)
            
            # Récupère le nombre de points depuis le ruban
            pts = int(self.spinbox_pts.get())

            if methode == "Hybride":
                N_val = self.inputs['N_lobes'].get()
                R_val = self.inputs['R_prim'].get()
                d_val = self.inputs['d_param'].get()
                
                e_calc = R_val / N_val 
                
                X, Y, X_rotor, Y_rotor = modeles.modele_hybride(N_val, R_val, d_val, pts)
                self.parametres_actifs = {"Mode": "Hybride", "Lobes": N_val, "R_générateur": R_val, "Excentricité induite": e_calc, "Paramètre d": d_val}
            
            elif methode == "Trochoïde":
                N = self.inputs['N_lobes'].get()
                R_p = self.inputs['R_prim'].get()
                d_t = self.inputs['d_traceur'].get()
                rho_env = self.inputs['rho_env'].get()
                
                X, Y, X_gen, Y_gen = modeles.modele_trochoide(N, R_p, d_t, rho_env, pts, sm)
                self.parametres_actifs = {"Mode": f"Trochoïde - {sm}", "Lobes": N, "R_prim": R_p, "Dist. Traceur": d_t, "Rho": rho_env}
            
            elif methode == "Paramétrique":
                N = self.inputs['N_lobes'].get()
                Rp = self.inputs['R_prim'].get()
                Rext = self.inputs['R_ext'].get()
                phi = self.inputs['phi_deg'].get()
                pts_seg = max(2, pts // (2 * int(N)))
                
                # Vérifie que l'UI a fini de s'actualiser avant de calculer
                if sm == "Circulaire" and 'r_cercle' in self.inputs:
                    X, Y = modeles.modele_parametrique_circ(N, Rp, Rext, self.inputs['r_cercle'].get(), pts_seg, phi)
                elif sm == "Elliptique" and 'a_ell' in self.inputs and 'b_ell' in self.inputs:
                    X, Y = modeles.modele_parametrique_ell(N, Rp, Rext, self.inputs['a_ell'].get(), self.inputs['b_ell'].get(), pts_seg, phi)
                elif sm == "Sinusoïdal" and 'A_sin' in self.inputs and 'T_sin' in self.inputs:
                    X, Y = modeles.modele_parametrique_sin(N, Rp, Rext, self.inputs['A_sin'].get(), self.inputs['T_sin'].get(), pts_seg, phi)
                else:
                    return # Attend que les inputs soient totalement chargés
                    
                self.parametres_actifs = {"Mode": f"Paramétrique - {sm}", "Lobes": N, "Rayon Prim": Rp}

            self.donnees_actives_X, self.donnees_actives_Y = X, Y
            self.donnees_actives_X_rotor, self.donnees_actives_Y_rotor = X_rotor, Y_rotor

            self.ax_profil.clear(); self.ax_schema.clear()
            couleur_stator = 'darkorchid' if methode == "Paramétrique" else ('black' if methode == "Trochoïde" else 'red')
            
            if X_gen is not None:
                self.ax_profil.plot(X_gen, Y_gen, 'k--', alpha=0.4, label="Génératrice")
                self.ax_schema.plot(X_gen, Y_gen, 'k--', alpha=0.3)

            label_principal = "Enveloppe lissée" if methode == "Trochoïde" else ("Stator" if methode == "Hybride" else f"Profil {methode}")
            
            # Tracé principal (ax_profil)
            self.ax_profil.plot(X, Y, color=couleur_stator, lw=2, label=label_principal)
            self.ax_profil.fill(X, Y, color=couleur_stator, alpha=0.15)
            self.ax_profil.plot(0, 0, 'ko', markersize=4)

            # --- TRACÉ DU ROTOR ET DE L'EXCENTRICITÉ ---
            if X_rotor is not None:
                if methode == "Hybride":
                    e_val = self.inputs['R_prim'].get() / self.inputs['N_lobes'].get()
                    
                    # Graphique Principal : on trace QUE le rotor
                    self.ax_profil.plot(X_rotor + e_val, Y_rotor, color='blue', lw=2, label="Rotor")
                    self.ax_profil.fill(X_rotor + e_val, Y_rotor, color='blue', alpha=0.15)
                    
                    # Graphique Schéma : on trace le rotor transparent + les indicateurs d'excentricité
                    self.ax_schema.plot(X_rotor + e_val, Y_rotor, color='blue', alpha=0.3, label="Rotor")
                    self.ax_schema.plot(e_val, 0, 'bo', markersize=4)
                    self.ax_schema.plot([0, e_val], [0, 0], 'g--', lw=1.5, label=f"e = {e_val:.3f}")
                else:
                    e_val = float(self.inputs.get('e_excent', ctk.StringVar(value="0")).get()) if 'e_excent' in self.inputs else 0.0
                    self.ax_profil.plot(X_rotor + e_val, Y_rotor, color='blue', lw=2, label="Rotor")
                    self.ax_profil.fill(X_rotor + e_val, Y_rotor, color='blue', alpha=0.15)
                    self.ax_profil.plot(e_val, 0, 'bo', markersize=4)
                    self.ax_profil.plot([0, e_val], [0, 0], 'g--', lw=1.5, label=f"e = {e_val:.3f}")

            self.ax_profil.axis('equal'); self.ax_profil.grid(True, linestyle=':', alpha=0.6)
            self.ax_profil.legend(loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=3, frameon=False, fontsize=10)

            # --- DESSIN DU SCHÉMA (ax_schema) ---
            self.ax_schema.plot(X, Y, color='black', alpha=0.15, label=label_principal) 
            th = np.linspace(0, 2*np.pi, 200)
            
            if 'R_prim' in self.inputs: 
                self.ax_schema.plot(self.inputs['R_prim'].get()*np.cos(th), self.inputs['R_prim'].get()*np.sin(th), 'b--', alpha=0.4, label="R_primitif (R)")
            if 'R_ext' in self.inputs: 
                self.ax_schema.plot(self.inputs['R_ext'].get()*np.cos(th), self.inputs['R_ext'].get()*np.sin(th), 'r--', alpha=0.4, label="R_extérieur")
            
            if methode == "Trochoïde":
                R_p = self.inputs['R_prim'].get()
                N_val = self.inputs['N_lobes'].get()
                d_val = self.inputs['d_traceur'].get()
                
                r_r = R_p / N_val
                centre_r = R_p - r_r if sm == "Hypocycloïde" else R_p + r_r
                
                self.ax_schema.plot(centre_r + r_r*np.cos(th), r_r*np.sin(th), 'g--', alpha=0.5, label="r_roulant calculé")
                self.ax_schema.plot([centre_r, centre_r + d_val], [0, 0], 'g-', lw=2, label="Distance traceur (d)")
                self.ax_schema.plot(centre_r, 0, 'go', markersize=4)

            self.ax_schema.axis('equal'); self.ax_schema.grid(True, linestyle=':', alpha=0.6)
            if self.ax_schema.get_legend_handles_labels()[1]: 
                self.ax_schema.legend(loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=2, frameon=False, fontsize=10)

            self.canvas_profil.draw()
            self.canvas_schema.draw()
            
        except Exception as e: 
            self.label_erreur.configure(text=f"Saisie ou calcul invalide")

    def action_exporter_csv(self):
        d = (self.donnees_actives_X_rotor, self.donnees_actives_Y_rotor) if self.cible_export_var.get() == "Rotor" else (self.donnees_actives_X, self.donnees_actives_Y)
        exporter_csv(d[0], d[1], self.parametres_actifs)

    def action_exporter_step(self):
        d = (self.donnees_actives_X_rotor, self.donnees_actives_Y_rotor) if self.cible_export_var.get() == "Rotor" else (self.donnees_actives_X, self.donnees_actives_Y)
        popup_export_step(d[0], d[1])

if __name__ == "__main__":
    app = GeorotorApp(); app.mainloop()