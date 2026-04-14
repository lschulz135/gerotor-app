import csv
import math
import customtkinter as ctk
from tkinter import filedialog, messagebox

# ==========================================
# WIDGET PERSONNALISÉ UNIQUE
# ==========================================
class CTkSpinbox(ctk.CTkFrame):
    def __init__(self, *args, width=120, height=30, step_size=1, command=None, **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)
        self.step_size = step_size
        self.command = command

        self.grid_columnconfigure((0, 2), weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.btn_sub = ctk.CTkButton(self, text="-", width=height-6, height=height-6, command=self.subtract)
        self.btn_sub.grid(row=0, column=0, padx=(3, 0), pady=3)

        self.entry = ctk.CTkEntry(self, width=width-(2*height), height=height-6, border_width=0, justify="center")
        self.entry.grid(row=0, column=1, columnspan=1, padx=3, pady=3, sticky="ew")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<FocusOut>", self.on_enter)

        self.btn_add = ctk.CTkButton(self, text="+", width=height-6, height=height-6, command=self.add)
        self.btn_add.grid(row=0, column=2, padx=(0, 3), pady=3)

    def add(self):
        try:
            val = float(self.entry.get()) + self.step_size
            self.set(int(val) if isinstance(self.step_size, int) else val)
            if self.command: self.command()
        except ValueError: pass

    def subtract(self):
        try:
            val = float(self.entry.get()) - self.step_size
            self.set(int(val) if isinstance(self.step_size, int) else val)
            if self.command: self.command()
        except ValueError: pass

    def on_enter(self, event=None):
        if self.command: self.command()

    def get(self):
        return float(self.entry.get()) if not float(self.entry.get()).is_integer() else int(float(self.entry.get()))

    def set(self, value):
        self.entry.delete(0, "end")
        if isinstance(value, float):
            self.entry.insert(0, f"{value:.2f}".rstrip('0').rstrip('.'))
        else:
            self.entry.insert(0, str(value))

# ==========================================
# FONCTIONS D'EXPORTATION
# ==========================================
def exporter_csv(x_data, y_data, parametres_dict):
    if x_data is None or len(x_data) == 0:
        messagebox.showwarning("Avertissement", "Aucune donnée à exporter.")
        return

    chemin = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Fichiers CSV", "*.csv")])
    if chemin:
        try:
            with open(chemin, mode='w', newline='') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['# --- PARAMETRES DE GENERATION ---'])
                for cle, valeur in parametres_dict.items():
                    writer.writerow([f'# {cle}', valeur])
                writer.writerow(['# --------------------------------'])
                writer.writerow([]) 
                writer.writerow(['X', 'Y', 'Z'])
                for x, y in zip(x_data, y_data):
                    writer.writerow([round(x, 4), round(y, 4), 0.0])
            messagebox.showinfo("Succès", "Export CSV réussi !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export CSV : {e}")

def popup_export_step(x_data, y_data):
    if x_data is None or len(x_data) == 0:
        messagebox.showwarning("Avertissement", "Aucune donnée à exporter.")
        return

    popup = ctk.CTkToplevel()
    popup.title("Export STEP 3D")
    popup.geometry("350x200")
    popup.attributes('-topmost', 'true')
    popup.grab_set()

    ctk.CTkLabel(popup, text="Indiquez l'épaisseur de l'extrusion (mm) :", font=("Arial", 14)).pack(pady=(20, 15))
    epaisseur_entry = ctk.CTkEntry(popup, justify="center", width=100)
    epaisseur_entry.insert(0, "10.0")
    epaisseur_entry.pack(pady=5)

    def valider_export():
        try:
            epaisseur = float(epaisseur_entry.get())
            if epaisseur <= 0: raise ValueError
            popup.destroy()
            _executer_export_step(x_data, y_data, epaisseur)
        except ValueError:
            messagebox.showerror("Erreur", "Épaisseur invalide.", parent=popup)

    ctk.CTkButton(popup, text="Générer", command=valider_export).pack(pady=15)

def _executer_export_step(x_data, y_data, epaisseur):
    chemin = filedialog.asksaveasfilename(defaultextension=".step", filetypes=[("Fichiers STEP", "*.step"), ("Fichiers STP", "*.stp")])
    if chemin:
        try:
            import cadquery as cq
            points_bruts = list(zip(x_data[:-1], y_data[:-1]))
            points_propres = [points_bruts[0]]
            for x, y in points_bruts[1:]:
                last_x, last_y = points_propres[-1]
                if math.hypot(x - last_x, y - last_y) > 1e-4:
                    points_propres.append((x, y))
            
            volume_3d = cq.Workplane("XY").polyline(points_propres).close().extrude(epaisseur)
            cq.exporters.export(volume_3d, chemin)
            messagebox.showinfo("Succès", "Export STEP réussi !")
        except ImportError:
            messagebox.showwarning("Erreur", "Pip install cadquery requis.")