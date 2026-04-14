# Conception & Analyse Géorotor ⚙️

Une application de bureau développée en Python (avec CustomTkinter) permettant de générer, visualiser et exporter des profils de géorotors (pompes à lobes). 

L'application regroupe plusieurs moteurs mathématiques pour concevoir des profils selon trois méthodes distinctes : Paramétrique, Trochoïdale et Hybride.

## ✨ Fonctionnalités
* **Génération dynamique** des profils de stator et rotor avec retour visuel en temps réel.
* **3 méthodes mathématiques** :
  * Paramétrique (Circulaire, Elliptique, Sinusoïdal)
  * Trochoïde (Hypocycloïde, Épitrochoïde)
  * Hybride (Méthode des segments)
* **Exportation de données** :
  * Profil 2D en `.csv` (avec conservation des paramètres de génération)
  * Volume 3D extrudé en `.step` (via CadQuery) pour l'intégration CAO (SolidWorks, Catia, Fusion360...).

## 🛠️ Installation

Il est fortement recommandé d'utiliser un environnement virtuel Python pour éviter les conflits de dépendances.

**1. Cloner le dépôt :**
```bash
git clone [https://github.com/ton-nom-utilisateur/nom-du-repo.git](https://github.com/ton-nom-utilisateur/nom-du-repo.git)
cd nom-du-repo