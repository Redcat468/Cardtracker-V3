# Card Tracker V3.0  
**Gestion des cartes mémoires pour les tournages**  

---

## 📌 Fonctionnalités  
- **Suivi en temps réel** des cartes mémoires (statut géographique, statut d'offload, quarantaine).  
- **Historique modulaire** avec timeline des opérations (déplacements, changements de statut).  
- **Gestion centralisée** des utilisateurs, cartes, statuts géographiques et offload.  
- **Tableaux de bord** pour visualiser les cartes par statut, utilisateur ou équipe.  
- **Annulation sécurisée** des opérations et suivi des modifications.  
- **Interface web responsive** avec authentification et droits d'accès (niveaux utilisateur).  

---

## 🛠️ Technologies  
- **Backend** : Flask (Python), SQLite.  
- **Frontend** : HTML/CSS, Tailwind, JavaScript.  
- **Packaging** : PyInstaller (exécutable Windows).  
- **Déploiement** : Service Windows via NSSM.  

---

## 🚀 Installation  
Voici la section détaillée sur l'installation via NSSM, intégrée au README :

### **Prérequis spécifiques**
1. Téléchargez [`nssm.exe`](https://nssm.cc/download) (version Win64 recommandée)

3. **Installer le service**  
   - **Clique-droit** sur `install_service.bat` > **Exécuter en tant qu'administrateur**
   - Le script effectue automatiquement :
     - Vérification des droits admin
     - Suppression d'une ancienne version du service
     - Création d'un nouveau service Windows nommé `CardTracker`
     - Configuration automatique :
       ```bash
       nssm install CardTracker "C:\chemin\vers\dist\cardtracker.exe"
       nssm set CardTracker AppDirectory "C:\chemin\vers\dist"
       nssm set CardTracker Start SERVICE_AUTO_START
       ```

4. **Vérifier l'installation**
   - Ouvrez le *Gestionnaire de tâches* > Onglet *Services*
   - Cherchez `CardTracker` - Statut devrait être **En cours d'exécution**

5. **Accéder à l'application**  
   Ouvrez `http://localhost:10000` dans votre navigateur.

Cette méthode est recommandée pour une utilisation en production - l'application reste toujours active même sans utilisateur connecté.
### Prérequis  
- Windows 10/11.  
- [Python 3.9+](https://www.python.org/downloads/) (avec `pip`).  
- [nssm.exe](https://nssm.cc/download) (placé dans le dossier du projet pour l'installation en service).  

### Étapes  
1. **Cloner le dépôt** :  
   ```bash 
   git clone [URL_du_dépôt] 
   cd cardtracker-v3 
   ```  

2. **Installer les dépendances** :  
   ```bash 
   pip install -r requirements.txt  # Si un fichier existe, sinon : 
   pip install flask flask-login flask-sqlalchemy pyinstaller 
   ```  

3. **Compiler l'application** (via `build.bat`) :  
   - Exécutez `build.bat` pour générer l'exécutable dans `dist/`.  
   - Le dossier `dist/` contient `cardtracker.exe` et les assets nécessaires.  

4. **Installer en tant que service Windows** :  
   - Copiez `nssm.exe` dans le dossier `dist/`.  
   - Exécutez `install_service.bat` **en tant qu'Administrateur**.  
   - Le service `CardTracker` sera accessible via le *Gestionnaire de tâches*.  

5. **Désinstaller** (si besoin) :  
   - Exécutez `uninstall_service.bat` pour supprimer le service.  

---

## 🖥️ Lancement manuel  
- Depuis le dossier `dist/`, exécutez `cardtracker.exe`.  
- L'appli est accessible sur : [`http://localhost:10000`](http://localhost:10000).  

---

## 🔑 Première utilisation  
1. **Connexion** :  
   - **Admin par défaut** : `fabt` / `motdepasse` (à modifier après la première connexion).  
   - Les utilisateurs standard doivent être créés via l'onglet *User Manager*.  

2. **Workflow typique** :  
   - **Créer une carte** : Via *Manage > Card Manager*.  
   - **Déplacer une carte** : Via *Track* (choisir source, cible, et statut offload).  
   - **Suivre une carte** : Via *Spot > Card Focus* (timeline et détails techniques).  

---

## 📂 Structure des dossiers  
- `templates/` : Pages HTML (interface web).  
- `static/` : CSS, images, JS.  
- `instance/` : Base de données SQLite générée automatiquement.  
- `dist/` : Exécutable et fichiers déployables après compilation.  

---

## ⚠️ Notes importantes  
- Le statut **quarantaine** bloque les déplacements des cartes.  
- Les **niveaux utilisateur** :  
  - **Niveau < 48** : Accès limité (Track/Spot).  
  - **Niveau ≥ 48** : Accès complet (Manage).  
- Les données sont stockées localement (adapté pour un usage hors-ligne).  

--- 

*Développé par Félix Abt - Cairn Studios (Licence CC BY-NC-SA 4.0)*
