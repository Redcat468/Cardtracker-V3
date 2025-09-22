# Card Tracker V3.3  
**Centralized tracking dashboard for on-set media cards in high-volume film/TV productions**  

<img width="1154" height="831" alt="image" src="https://github.com/user-attachments/assets/a75ffe2e-2fde-457d-a18f-f9c25d72dad3" />

---

## 📌 Key Features  
- **Real-time tracking** of memory cards (geographic status, offload status, quarantine).  
- **Modular history** with operation timeline (movements, status changes).  
- **Centralized management** of users, teams, cards, and geographic/offload statuses.
- **Dashboards** to view cards by status, user, or team.  
- **Secure rollback** of operations and change tracking.  
- **Responsive web interface** with authentication and access levels.
- **Discord notifications** for new backup requests

---

## 🛠️ Technologies  
- **Backend**: Flask (Python), SQLite.  
- **Frontend**: HTML/CSS, Tailwind, JavaScript.  
- **Packaging**: PyInstaller (Windows executable).  
- **Deployment**: Windows service via NSSM.  

---

## 🚀 Installation  
### **NSSM-Specific Requirements**
1. Download the latest release available in the "dist" folder of this repo

3. **Install Service** 
   - **Right-click** on `install_service.bat` > **Run as administrator**  
   - The script automatically performs:  
     - Admin rights verification  
     - Removal of previous service versions  
     - Creation of new Windows service named `CardTracker`  
     - Automatic configuration:  
       ```bash
       nssm install CardTracker "C:\path\to\dist\cardtracker.exe"
       nssm set CardTracker AppDirectory "C:\path\to\dist"
       nssm set CardTracker Start SERVICE_AUTO_START
       ```

5. **Verify Installation**  
   - Open *Task Manager* > *Services* tab  
   - Look for `CardTracker` - Status should be **Running**  

6. **Access Application**  
   Open `http://localhost:10000` in your browser.  

---

## 🖥️ Manual Launch  
- From the `dist/` folder, run `cardtracker.exe`.  
- App available at: [`http://localhost:10000`](http://localhost:10000).  

---

## 🔑 First Use  
1. **Login**  
   - **Default admin**: `fabt` / `motdepasse` (change after first login)  
   - Standard users must be created via *User Manager*.  

2. **Typical Workflow**  
   - **Create card**: Via *Manage > Card Manager*  
   - **Move card**: Via *Track* (select source, target, offload status)  
   - **Track card**: Via *Spot > Card Focus* (timeline and technical details)  

---

## 📂 Folder Structure  
- `templates/`: HTML pages (web interface)  
- `static/`: CSS, images, JS  
- `instance/`: Auto-generated SQLite database  
- `dist/`: Compiled executable and deployment files  

---

## ⚠️ Important Notes  
- **Quarantine status** blocks card movements  
- **User levels**:
  - **Level =< 1**: Limited "shooting" access (Track/Spot no formatting or backup actions)  
  - **Level < 48**: Admin access (Track/Spot)  
  - **Level ≥ 48**: Full access (Manage)
- Data stored locally (optimized for offline use)
- Team management allow administrators (managers) to authorize actions on specific geo status only for team members.

## Screenshots 
<img width="374" height="499" alt="login page" src="https://github.com/user-attachments/assets/e39cd6c2-df0b-49e3-8df5-4725306bc3ed" />
<img width="1527" height="859" alt="card focus" src="https://github.com/user-attachments/assets/e38cd35d-c4d4-4d15-8de4-5977ff3e2bed" />


--- 

*Developed by Félix Abt - Cairn Studios (CC BY-NC-SA 4.0 License)*
