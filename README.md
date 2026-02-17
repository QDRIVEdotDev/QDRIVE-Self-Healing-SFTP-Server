# QDRIVE: Self-Healing Secure SFTP Infrastructure

A robust, hybrid Python/PowerShell infrastructure designed to manage high-security, rotating-port SFTP servers with autonomous "Self-Healing" capabilities and Discord-based ChatOps management.

---

### **Project Overview**
The QDRIVE environment is engineered to handle dynamic network conditions, specifically targeting environments utilizing VPN port-forwarding (e.g., Proton VPN). It utilizes a "Handshake Protocol" between a Python interface and a PowerShell watchdog to ensure near 100% uptime and automatic port synchronization across firewall rules and SSH configurations.

---

### **Core Documentation**
For a deep dive into specific system components, refer to the following technical manuals:

* **[Technical Operations](docs/OPERATIONS.md)**: Deep dive into the `C:\QDRIVE` root, drive portal logic, and RBAC permissions.
* **[System Architecture](docs/ARCHITECTURE.md)**: Breakdown of the Handshake Protocol, self-healing loops, and log parsing.
* **[Infrastructure Setup](docs/QDRIVE-TaskScheduler-Setup.md)**: Mandatory Task Scheduler and system-level configuration.
* **[Client Connection Guide](docs/CONNECTION.md)**: Step-by-step instructions for whitelisting and WinSCP connectivity.
* **[Lore & Banner Protocol](docs/LOREBANNER.md)**: The narrative behind the "Mind Prison" and its use as a server-identity signature.

---

### **Key Features**
* **Watchdog Protocol**: Automated regex-based log parsing that monitors VPN logs for new port assignments and updates the system in real-time.
* **Self-Healing Handshake**: A bidirectional heartbeat loop; the Port Watcher monitors the bot's health timestamp and programmatically restarts the process if a hang or crash is detected.
* **ChatOps Management**: A full Discord command tree for remote server administration, including IP/Port reporting, storage health, and security whitelisting.
* **QLOCK Protocol**: A surgical maintenance function that terminates specific file handles on the storage array to allow for clean log rotation and system refreshes.
* **RBAC File Security**: Discord commands to immediately deny or restore user access to specific folders on the storage array using `icacls`.

---

### **Technical Architecture**

#### **The Handshake Protocol**
* **QBOT (Python)**: Updates `qbot_health.txt` every 60 seconds if the connection to Discord is active.
* **Sync-ProtonPort (PowerShell)**: Monitors the `qbot_health.txt` timestamp. If the file is missing or older than 10 minutes, it force-kills stale instances and restarts the bot via Task Scheduler.

#### **The Storage Portal**
The system utilizes a specialized mount point at `C:\QDRIVE\Drive-Portal` to bridge Internal and External SSDs while supporting OpenSSH `ChrootDirectory` requirements. This prevents mounting conflicts and ensures user permission integrity.

---

### **Installation & Deployment**

#### **Prerequisites**
* **OS**: Windows 10/11 with OpenSSH Server installed.
* **Global Flags**: Run `openfiles /local on` in an elevated prompt and reboot to enable the `QLOCK` protocol.
* **Accounts**: Create two non-administrator local Windows users named `QDRIVE` and `QDRIVEADMIN`.
* **Execution Policy**: Enable `RemoteSigned` for PowerShell scripts.

#### **Quick Start**
1.  **Clone the Repo**: Maintain the established folder structure for script interoperability.
2.  **Configure**: Rename `config.example.json` to `config.json` and input your Discord Bot Token and Admin ID.
3.  **Setup Tasks**: Create the mandatory Scheduled Tasks as outlined in the `docs/QDRIVE-TaskScheduler-Setup.md` guide.
4.  **Initialize**: Launch `Sync-ProtonPort.ps1` to begin the initial port synchronization and bot wake-up sequence.

---

### **Discord Command Tree**
* **`/qdrive`**: Reports current external IP and active SSH Port.
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
