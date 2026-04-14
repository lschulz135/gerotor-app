import customtkinter as ctk
import numpy as np
from matplotlib.figure import Figure # <-- Remplacer pyplot par Figure
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
        self.title("Conception & Analyse Géorotor - Unifié")
        self.geometry("1400x800")

        # --- GESTION DE L'ICÔNE ---
        self.charger_icone()

        self.donnees_actives_X = None
        self.donnees_actives_Y = None
        self.parametres_actifs = {}

        self.setup_ui()
        self.charger_methode("Paramétrique") # Chargement initial

    def charger_icone(self):
        try:
            chemin_actuel = os.path.dirname(os.path.abspath(__file__))
            chemin_icone = os.path.join(chemin_actuel, "assets", "icone.png")
            
            if os.path.exists(chemin_icone):
                self.icone_image = PhotoImage(file=chemin_icone)
                self.iconphoto(True, self.icone_image) 
            else:
                print(f"Info : assets/icone.png non trouvé au chemin : {chemin_icone}")
        except Exception as e:
            print(f"Info : Erreur lors du chargement de l'icône ({e})")

    def setup_ui(self):
        # --- ONGLETS ---
        self.onglets = ctk.CTkTabview(self)
        self.onglets.pack(padx=10, pady=10, fill="both", expand=True)
        self.onglet_conception = self.onglets.add("Conception")
        self.onglet_analyse = self.onglets.add("Analyse")

        # Grille principale de conception
        self.onglet_conception.grid_columnconfigure(0, weight=0) # Sidebar
        self.onglet_conception.grid_columnconfigure(1, weight=1) # Graphique
        self.onglet_conception.grid_rowconfigure(1, weight=1)    # Zone centrale extensible
        # On s'assure que la ligne 2 (le ruban) ne s'étire pas, c'est la ligne 1 qui prend la place
        self.onglet_conception.grid_rowconfigure(2, weight=0)    

        # --- 1. BARRE SUPÉRIEURE ---
        top_bar = ctk.CTkFrame(self.onglet_conception, height=50)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 0))
        ctk.CTkLabel(top_bar, text="Méthode :", font=("Arial", 14, "bold")).pack(side="left", padx=20, pady=10)
        
        self.methode_var = ctk.StringVar(value="Paramétrique")
        ctk.CTkOptionMenu(top_bar, variable=self.methode_var, 
                          values=["Paramétrique", "Trochoïde", "Hybride"],
                          command=self.charger_methode).pack(side="left", padx=10, pady=10)

        # --- 2. BARRE LATÉRALE ---
        self.sidebar = ctk.CTkScrollableFrame(self.onglet_conception, width=350)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.inputs = {}
        self.label_erreur = ctk.CTkLabel(self.sidebar, text="", text_color="red")

        # --- 3. ZONE GRAPHIQUE (CORRIGÉE SANS PYPLOT) ---
        graph_frame = ctk.CTkFrame(self.onglet_conception, fg_color="white")
        graph_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor='#ffffff')
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.15, wspace=0.3)
        
        self.ax_profil = self.fig.add_subplot(121)
        self.ax_schema = self.fig.add_subplot(122)

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")

        # --- 4. RUBAN D'EXPORT FIXE ---
        ribbon = ctk.CTkFrame(self.onglet_conception, height=60, corner_radius=0)
        # Il est placé en row=2 pour être tout en bas
        ribbon.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(ribbon, text="Options d'export :", font=("Arial", 12, "bold")).pack(side="left", padx=20)
        ctk.CTkButton(ribbon, text="Exporter Profil (CSV)", fg_color="transparent", border_width=2, text_color=("gray10", "gray90"),
                      command=lambda: exporter_csv(self.donnees_actives_X, self.donnees_actives_Y, self.parametres_actifs)).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(ribbon, text="Exporter Volume (STEP)", fg_color="#2b7b46", hover_color="#1e5c33",
                      command=lambda: popup_export_step(self.donnees_actives_X, self.donnees_actives_Y)).pack(side="left", padx=10, pady=10)
        
    # ==========================================
    # GESTION DYNAMIQUE DE L'INTERFACE
    # ==========================================
    def charger_methode(self, methode_nom):
        # Nettoyage
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        self.inputs.clear()
        self.sidebar.configure(label_text=f"Paramètres - {methode_nom}")

        # Sélecteur de sous-mode
        self.sous_mode_var = ctk.StringVar()
        if methode_nom == "Paramétrique":
            self.sous_mode_var.set("Circulaire")
            ctk.CTkSegmentedButton(self.sidebar, variable=self.sous_mode_var, values=["Circulaire", "Elliptique", "Sinusoïdal"], 
                                   command=lambda _: self.generer_et_afficher()).pack(pady=10, fill="x", padx=5)
        elif methode_nom == "Trochoïde":
            self.sous_mode_var.set("Hypocycloïde")
            ctk.CTkSegmentedButton(self.sidebar, variable=self.sous_mode_var, values=["Hypocycloïde", "Épitrochoïde"], 
                                   command=lambda _: self.generer_et_afficher()).pack(pady=10, fill="x", padx=5)

        # Configuration des champs standardisés
        configs = {
            "Hybride": [
                ("Géométrie", [("N_lobes", "Lobes stator", 8, 1), ("e_excent", "Excentricité (e)", 1.5, 0.25), ("d_param", "Paramètre (d)", 1.2, 0.1)]),
                ("Résolution", [("nb_points", "Nb de points", 2000, 200)])
            ],
            "Trochoïde": [
                ("Paramètres", [("N_lobes", "Dents Stator", 7, 1), ("R_prim", "Rayon primitif", 15.0, 0.5), ("R_traceur", "Rayon traceur", 1.0, 0.1)]),
                ("Résolution", [("nb_points", "Nb de points", 2000, 500)])
            ],
            "Paramétrique": [
                ("Globaux", [("N_lobes", "Nb de cavités", 5, 1), ("R_prim", "Rayon primitif", 13.0, 0.5), ("R_ext", "Rayon extérieur", 10.0, 0.5), ("phi_deg", "Angle (°)", 0.0, 5.0)]),
                ("Spécifiques (Varie)", [("r_cercle", "Rayon r (Circ)", 5.0, 0.5), ("a_ell", "Prof a (Ell)", 5.0, 0.5), ("b_ell", "Largeur b (Ell)", 4.0, 0.5), ("A_sin", "Ampli A (Sin)", 5.0, 0.5), ("T_sin", "Période T (Sin)", 150.0, 1.0)]),
                ("Résolution", [("nb_points", "Nb de points", 2000, 100)])
            ]
        }

        # Génération dynamique des Spinboxes
        for categorie, champs in configs[methode_nom]:
            ctk.CTkLabel(self.sidebar, text=categorie, font=("Arial", 12, "bold"), text_color="gray").pack(pady=(15,5), anchor="w", padx=10)
            for key, label, defaut, step in champs:
                f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=label, width=130, anchor="w").pack(side="left", padx=5)
                spinbox = CTkSpinbox(f, step_size=step, command=self.generer_et_afficher)
                spinbox.set(defaut)
                spinbox.pack(side="right", padx=5)
                self.inputs[key] = spinbox

        self.label_erreur = ctk.CTkLabel(self.sidebar, text="", text_color="red", font=("Arial", 12, "bold"))
        self.label_erreur.pack(pady=10)
        self.generer_et_afficher()

    # ==========================================
    # LOGIQUE DE ROUTAGE ET DESSIN
    # ==========================================
    def generer_et_afficher(self):
        try:
            self.label_erreur.configure(text="")
            methode = self.methode_var.get()
            X, Y = None, None

            # --- ROUTAGE VERS LE MOTEUR MATHÉMATIQUE ---
            if methode == "Hybride":
                X, Y = modeles.modele_hybride_stator(self.inputs['N_lobes'].get(), self.inputs['e_excent'].get(), self.inputs['d_param'].get(), self.inputs['nb_points'].get())
                self.parametres_actifs = {"Mode": "Hybride", "Lobes": self.inputs['N_lobes'].get(), "Excentricité": self.inputs['e_excent'].get()}
            
            elif methode == "Trochoïde":
                sm = self.sous_mode_var.get()
                X, Y, r_roulant = modeles.modele_trochoide(self.inputs['N_lobes'].get(), self.inputs['R_prim'].get(), self.inputs['R_traceur'].get(), self.inputs['nb_points'].get(), sm)
                self.parametres_actifs = {"Mode": f"Trochoïde - {sm}", "Lobes": self.inputs['N_lobes'].get(), "Rayon Prim": self.inputs['R_prim'].get()}
            
            elif methode == "Paramétrique":
                sm = self.sous_mode_var.get()
                N, Rp, Rext, pts, phi = self.inputs['N_lobes'].get(), self.inputs['R_prim'].get(), self.inputs['R_ext'].get(), max(2, int(self.inputs['nb_points'].get())//(2*int(self.inputs['N_lobes'].get()))), self.inputs['phi_deg'].get()
                if sm == "Circulaire":
                    X, Y = modeles.modele_parametrique_circ(N, Rp, Rext, self.inputs['r_cercle'].get(), pts, phi)
                elif sm == "Elliptique":
                    X, Y = modeles.modele_parametrique_ell(N, Rp, Rext, self.inputs['a_ell'].get(), self.inputs['b_ell'].get(), pts, phi)
                else:
                    X, Y = modeles.modele_parametrique_sin(N, Rp, Rext, self.inputs['A_sin'].get(), self.inputs['T_sin'].get(), pts, phi)
                self.parametres_actifs = {"Mode": f"Paramétrique - {sm}", "Lobes": N, "Rayon Prim": Rp}

            # --- SAUVEGARDE POUR L'EXPORT ---
            self.donnees_actives_X, self.donnees_actives_Y = X, Y

            # --- UN SEUL CODE POUR PLOTER ---
            self.ax_profil.clear()
            self.ax_schema.clear()

            couleur = 'darkorchid' if methode == "Paramétrique" else ('black' if methode == "Trochoïde" else 'red')
            
            # Tracé Graphique Principal
            self.ax_profil.plot(X, Y, color=couleur, lw=2, label=f"{methode}")
            self.ax_profil.fill(X, Y, color=couleur, alpha=0.15)
            self.ax_profil.plot(0, 0, 'ko', markersize=4)
            self.ax_profil.set_title(f"Profil : {methode}", fontweight="bold")
            self.ax_profil.axis('equal')
            self.ax_profil.grid(True, linestyle=':', alpha=0.6)
            self.ax_profil.legend()

            # Tracé du Schéma (Simplifié et universel)
            self.ax_schema.plot(X, Y, color='black', alpha=0.15) # Fantôme du profil
            th = np.linspace(0, 2*np.pi, 200)
            if 'R_prim' in self.inputs: # Si la méthode utilise un cercle primitif
                rp = self.inputs['R_prim'].get()
                self.ax_schema.plot(rp*np.cos(th), rp*np.sin(th), 'b--', alpha=0.5, label="Rayon primitif")
            if 'R_ext' in self.inputs:
                rext = self.inputs['R_ext'].get()
                self.ax_schema.plot(rext*np.cos(th), rext*np.sin(th), 'r--', alpha=0.5, label="Rayon extérieur")
            
            self.ax_schema.set_title("Schéma Géométrique", fontweight="bold")
            self.ax_schema.axis('equal')
            self.ax_schema.grid(True, linestyle=':', alpha=0.6)
            if self.ax_schema.get_legend_handles_labels()[1]: self.ax_schema.legend(fontsize=8)

            self.canvas.draw()
            
        except Exception as e:
            self.label_erreur.configure(text="Saisie ou calcul invalide")

if __name__ == "__main__":
    app = GeorotorApp()
    app.mainloop()