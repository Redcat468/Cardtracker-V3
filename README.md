# Card Tracker V3.0  
**Memory Card Management for Film Productions**  

---

## 📌 Key Features  
- **Real-time tracking** of memory cards (geographic status, offload status, quarantine).  
- **Modular history** with operation timeline (movements, status changes).  
- **Centralized management** of users, cards, geographic/offload statuses.  
- **Dashboards** to view cards by status, user, or team.  
- **Secure rollback** of operations and change tracking.  
- **Responsive web interface** with authentication and access levels.  

---

## 🛠️ Technologies  
- **Backend**: Flask (Python), SQLite.  
- **Frontend**: HTML/CSS, Tailwind, JavaScript.  
- **Packaging**: PyInstaller (Windows executable).  
- **Deployment**: Windows service via NSSM.  

---

## 🚀 Installation  
### **NSSM-Specific Requirements**
1. Download the [`latest release`](https://github.com/Redcat468/Cardtracker-V3/releases)

3. **Install Service**  
   - Unzip the archive  
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
  - **Level < 48**: Limited access (Track/Spot)  
  - **Level ≥ 48**: Full access (Manage)  
- Data stored locally (optimized for offline use)  

--- 

*Developed by Félix Abt - Cairn Studios (CC BY-NC-SA 4.0 License)*