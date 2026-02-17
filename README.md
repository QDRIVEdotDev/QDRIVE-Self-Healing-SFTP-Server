# QDRIVE: Self-Healing Secure SFTP Infrastructure

> **Build your own Cloud.**
> **A fully autonomous, self-healing SFTP infrastructure designed for dynamic network environments.**

A robust, hybrid Python/PowerShell engine designed to manage high-security, rotating-port SFTP servers. It bridges the gap between complex VPN networking and accessible file storage using autonomous "Self-Healing" capabilities and Discord-based ChatOps.
---

### **Project Overview**
The QDRIVE environment is engineered to handle dynamic network conditions, specifically targeting environments utilizing VPN port-forwarding (Proton VPN in this case). It utilizes a custom **"Handshake Protocol"** between a Python interface and a PowerShell watchdog to ensure near 100% uptime and automatic port synchronization across firewall rules, SSH configurations, and discord reporting.

### **Key Features**
* **Watchdog Protocol**: Automated regex-based log parsing that monitors VPN logs for new port assignments and updates the `sshd_config` and Windows Firewall in real-time.
* **SRE Self-Healing**: A bidirectional heartbeat loop; the Port Watcher monitors the bot's health timestamp and programmatically kills/restarts the process if a hang or crash is detected.
* **ChatOps Management**: A full Discord command tree for remote server administration, including IP/Port reporting, storage health, and security whitelisting.
* **QLOCK Protocol**: A surgical maintenance function that terminates specific file handles on the storage array to allow for clean log rotation and system refreshes without reboots.
* **RBAC File Security**: Discord commands to immediately deny or restore user access to specific folders on the storage array using native Windows `icacls`.

---

### **Technical Architecture**

#### **The Handshake Protocol**
* **QBOT (Python)**: Updates `qbot_health.txt` every 60 seconds if the connection to the Discord Gateway is active.
* **Sync-ProtonPort (PowerShell)**: Monitors the `qbot_health.txt` timestamp. If the file is missing or older than 10 minutes, it assumes a process failure, force-kills stale instances, and restarts the bot via Task Scheduler.

#### **The Storage Portal**
The system utilizes a specialized mount point at `C:\QDRIVE\Drive-Portal` to bridge Internal and External SSDs while supporting OpenSSH `ChrootDirectory` requirements. This prevents mounting conflicts and ensures user permission integrity.

---

### **Core Documentation**
For a deep dive into specific system components, refer to the following technical manuals:

* **[System Architecture](docs/ARCHITECTURE.md)**: Breakdown of the Handshake Protocol, self-healing loops, and log parsing.
* **[Technical Operations](docs/OPERATIONS.md)**: Deep dive into the `C:\QDRIVE` root, drive portal logic, and RBAC permissions.
* **[Infrastructure Setup](docs/QDRIVE-TaskScheduler-Setup.md)**: Mandatory Task Scheduler and system-level configuration.
* **[Client Connection Guide](docs/CONNECTION.md)**: Step-by-step instructions for whitelisting and WinSCP connectivity.
* **[Lore & Banner Protocol](docs/LOREBANNER.md)**: The narrative behind the "Mind Prison" and its use as a server-identity signature.

---

### **Installation & Deployment**

#### **Prerequisites**
* **OS**: Windows 10/11 with OpenSSH Server installed.
* **Global Flags**: Run `openfiles /local on` in an elevated prompt and reboot to enable the `QLOCK` protocol.
* **Accounts**: Create two non-administrator local Windows users named `QDRIVE` and `QDRIVEADMIN`.
* **Execution Policy**: Enable `RemoteSigned` for PowerShell scripts.

#### **1. The Filesystem Architecture**
This system requires a specific two-folder structure on your `C:` drive to function correctly.
* **`C:\QDRIVE-SYSTEM`**: Contains the "Brain" (Scripts, Configs, Logs).
* **`C:\QDRIVE`**: The "Body" (The actual SFTP root where data lives).

* **CRITICAL: "chrooting" the SFTP Server, and OpenSSH Config**
  
    You must replace the default Windows SSH config with the hardened QDRIVE template.
    1.  Navigate to the hidden folder: `C:\ProgramData\ssh`.
    2.  Rename the original existing `sshd_config` to `sshd_config.bak` (Always have a backup).
    3.  Copy the file `C:\QDRIVE-SYSTEM\docs\sshd_config.example` into `C:\ProgramData\ssh`.
    4.  Rename the copied file to `sshd_config`.
    5.  Copy the NEW `sshd_config`, paste it alongside the old backup, and rename the new backup to `sshd_config2.bak` (Always have a backup of your original, and configured versions).
    6.  **Restart the Service:** Open PowerShell as Admin and run: `Restart-Service sshd`.

#### **2. Deployment Steps**
1.  **Clone the Repository**: Download this repo or `git clone` it.

2.  **Create the System Root**:
    * Create a folder named `C:\QDRIVE-SYSTEM`.
    * **CRITICAL:** Copy the **entire contents** of your cloned repo (the `src` folder, `config.example.json`, etc.) directly into `C:\QDRIVE-SYSTEM`.
    * *Verification:* You must have `C:\QDRIVE-SYSTEM\src\bot\qbot.py` for the relative paths to function.
    
3.  **Create the SFTP Root**:
    * Create a folder named `C:\QDRIVE`.
    * Create any desired subfolders such as `C:\QDRIVE\QDRIVEADMINUPLOAD`, or `C:\QDRIVE\ADMINUP-USERDOWN`.
   
    * **NOTE:** If you wish to utilize an external SSD within the QDRIVE to expand its storage, create an empty folder inside the root `C:\QDRIVE` named `Drive-Portal`. (`C:\QDRIVE\Drive-Portal`)
    * **Mount the Drive:** Open **Disk Management** (`diskmgmt.msc`).
        * Right-click your target External SSD partition and select **Change Drive Letter and Paths**.
        * **Remove** any existing drive letter (e.g., `D:` or `E:`).
        * Click **Add** -> **Mount in the following empty NTFS folder**.
        * Browse to and select `C:\QDRIVE\Drive-Portal`.
    * *Why?* This allows the drive to exist inside the SFTP "chrooted jail" without a drive letter, preventing permission conflicts and ensuring the `QLOCK` protocol can correctly identify file handles.
    
4.  **Configuration & Security**:
    Before initializing, you must establish the "Digital Identity" (Bot) and "Physical Security" (Permissions).

    **4.1 The Discord Link (Bot Setup)**
    1.  Go to the **Discord Developer Portal** and click **New Application**. Name it (`QDRIVE-Uplink`, or `QBOT`).
    2.  Click the **Bot** tab on the left -> **Add Bot**.
    3.  **CRITICAL:** Scroll down to **Privileged Gateway Intents** and toggle **ON** the `MESSAGE CONTENT INTENT`. (Without this, the bot cannot read your commands). Save Changes.
    4.  **Get Token:** Scroll up to the "Token" section, click **Reset Token**, and copy it.
    5.  **Invite Bot:** Click **OAuth2** -> **URL Generator**. Check `bot` scope and `Administrator` permissions. Copy the URL and invite it to your server.
    6.  **Get Admin ID:** In Discord settings, enable **Developer Mode**. Right-click your own username and select **Copy User ID**.

    **4.2 System Configuration (`config.json`)**
    1.  Inside `C:\QDRIVE-SYSTEM`, rename `config.example.json` to `config.json`.
    2.  Open the file and update the following fields:
        * `"discord_token"`: Paste the token from Step 4.1.
        * `"admin_id"`: Paste your User ID from Step 4.1.
        * `"powershell_profile"`: **IMPORTANT.** Update this path to match your actual Windows user. 
            * *Default:* `C:\\Users\\YOUR_USER\\Documents\\WindowsPowerShell\\Microsoft.PowerShell_profile.ps1`
            * *Action:* Change `YOUR_USER` to your actual Windows username. Ensure you keep the double backslashes (`\\`) for valid JSON formatting.

    **4.3 Permission Hardening (Role-Based Access Control)**
    You must restrict the standard `QDRIVE` user to Read-Only access while giving `QDRIVEADMIN` full control.
    1.  Right-click `C:\QDRIVE` -> **Properties** -> **Security** -> **Advanced**.
    2.  **Disable Inheritance:** Select "Convert inherited permissions into explicit permissions."
    3.  **Remove** generic groups like "Users" or "Authenticated Users". (Keep SYSTEM and Administrators).
    4.  **Add `QDRIVE` User:**
        * Click Add -> Select Principal -> Type `QDRIVE`.
        * Grant: **Read & execute**, **List folder contents**, **Read**.
        * *Ensure "Write" is UNCHECKED.*
    5.  **Add `QDRIVEADMIN` User:**
        * Click Add -> Select Principal -> Type `QDRIVEADMIN`.
        * Grant: **Full control**.
    6.  **Apply:** Check "Replace all child object permission entries..." and click Apply.

    **4.4 Configuring Folder Roles (ChatOps)**
    Now that the baseline is set (QDRIVE = Read Only, QDRIVEADMIN = Read + Write), you can use the Discord Bot to strictly enforce specific folder behaviors.

    **Example 1: The Private Vault (`QDRIVEADMINUPLOAD`)**
    *Goal:* Only admins can enter this folder. The non-admin users cannot access it at all.
    1.  Create the folder: `C:\QDRIVE\QDRIVEADMINUPLOAD`.
    2.  **Go to Discord** and run:
        `/qdeny foldername:QDRIVEADMINUPLOAD`
    3.  *Result:* The bot executes `icacls /deny`, effectively making this folder invisible/inaccessible to the non-admin user (local user "QDRIVE"), while admins (local user "QDRIVEADMIN") retain full access.

    **Example 2: The Public Drop (ADMINUP-USERDOWN)**
    *Goal:* admin users can upload files here, and the non-admin users can download them (Default Behavior).
    1.  Create the folder: `C:\QDRIVE\ADMINUP-USERDOWN`.
    2.  **Do nothing.**
    3.  *Result:* Because of the "Permission Hardening" in Step 4.3, this folder automatically inherits "Read Only" for the Public. You can upload files here, and users can download them, but they cannot delete them.

    **Example 3: restoring Access (The Unlock)**
    *Goal:* You locked a folder previously and want to open it back up to the public.
    1.  **Go to Discord** and run:
        `/qallow foldername:QDRIVEADMINUPLOAD`
    2.  *Result:* The bot removes the explicit "Deny" rule, restoring the default "Read Only" access.
    
5.  **Initialize**:
    * Create the mandatory Scheduled Tasks as outlined in `docs/QDRIVE-TaskScheduler-Setup.md`.
    * Launch `src\watchdog\Sync-ProtonPort.ps1` to begin the initial port synchronization and bot wake-up sequence.

---

### **Discord Command Tree**
* **`/qdrive`**: Reports current external IP and active SSH Port.
    > *Note: This is the ONLY command executable by non-admin users.*
* **`/qstatus`**: Comprehensive system report including disk usage and Watchdog health status.
* **`/qstart`**: Manually awakens the Port Watcher (Watchdog) via Task Scheduler.
* **`/qaddkey`**: Programmatically injects public SSH keys into specific user vaults.
* **`/qdeny`**: Instantly restricts standard user access to specific storage subfolders via `icacls`.
* **`/qallow`**: Restores standard user access to previously locked storage subfolders.
* **`/qlock`**: Emergency lockout; terminates file locks, kills the Watchdog, and stops the SSH service.
* **`/qrestart`**: Triggers the full Weekly Maintenance routine and issues a system reboot.

---

### **Repository Structure**
```text
QDRIVE/
├── config.json              # (User Created) Private settings & paths
├── config.example.json      # Template for configuration
├── src/
│   ├── bot/
│   │   └── qbot.py          # Discord Management Interface
│   ├── watchdog/
│   │   └── Sync-ProtonPort.ps1  # Self-Healing Port Watcher
│   └── maintenance/
│       ├── WeeklyMaintenance.ps1 # Sunday Refresh Routine
│       └── QLOCK.ps1        # Surgical File-Lock Termination
└── docs/
    ├── ARCHITECTURE.md
    ├── CONNECTION.md
    ├── LOREBANNER.md
    ├── OPERATIONS.md
    ├── sshd_config.example
    └── QDRIVE-TaskScheduler-Setup.md
```
Disclaimer: Project QDRIVE is an independent open-source automation tool developed by QDRIVEdotDev and is not affiliated with any third-party vendors, official systems, or commercial entities.
