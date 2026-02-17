# QDRIVE: Technical Operations Manual

This manual is the primary reference for the QDRIVE’s physical setup and internal logic. It details the folder structure, drive mounting, and permissions required to keep the SFTP server secure and running autonomously.

---

### I. System Directory Structure

The QDRIVE environment is designed as a self-contained ecosystem. While the repository may be cloned anywhere, the following paths are the system standards for deployment:

* **System Root**: `C:\QDRIVE-SYSTEM` (Base directory for all operational logs, configuration, and health signals).
* **Watchdog Source**: `C:\QDRIVE-SYSTEM\src\watchdog\Sync-ProtonPort.ps1`.
* **Interface Source**: `C:\QDRIVE-SYSTEM\src\bot\qbot.py`.
* **Maintenance Source**: `C:\QDRIVE-SYSTEM\src\maintenance\WeeklyMaintenance.ps1`.
* **Handshake Files**: Located in the system root (`maintenance_status.txt` and `qbot_health.txt`).

> **Note**: Scripts must remain in their established relative subfolders to ensure interoperability and correct path resolution.

---

### II. The Storage Portal & SFTP Root

The SFTP server uses **`C:\QDRIVE`** as its functional root directory. All incoming user sessions are "Chrooted" to this path, meaning they are locked inside this folder and cannot see or access the rest of the Windows host system.

* **The SFTP Root**: `C:\QDRIVE` (The top-level directory for all incoming connections).
* **Physical Array**: Consists of one Internal SSD and one External SSD.
* **The Portal**: Located at `C:\QDRIVE\Drive-Portal`.
* **Mounting Requirement**: To avoid drive letter conflicts and permission errors, physical disks are mounted directly into the portal folder rather than being assigned a standard drive letter (like E: or Q:).
* **Chroot Support**: Mounting the External SSD as a directory within the portal allows it to work seamlessly with OpenSSH’s security requirements.



---

### III. User Access & Permission Hierarchy

The system enforces strict Role-Based Access Control (RBAC) using local Windows accounts.

#### 1. Account Roles
* **QDRIVEADMIN**: Administrative account with full **Read/Write** SFTP access to the entire `C:\QDRIVE` structure.
* **QDRIVE**: Standard user account with **Read-Only** access across the server. This user is strictly forbidden from uploading files to any directory, and can be restricted from any specific folders using **ICACLS**. 

#### 2. Isolation via ICACLS
The Discord interface utilizes `icacls` to programmatically deny or allow standard user access to specific sensitive folders.

* **To Deny Access**: Executes `icacls [path] /deny "QDRIVE:(OI)(CI)(F)"`.
* **To Restore Access**: Executes `icacls [path] /remove:d "QDRIVE"`.

---

### IV. Operational Workflow

#### The Handshake Protocol
1. **Watchdog Initialization**: Launched via Task Scheduler at boot, the Port Watcher extracts the active VPN port from LocalAppData logs.
2. **Health Monitoring**: Every 60 seconds, the Watchdog verifies the `qbot_health.txt` timestamp.
3. **Healing**: If the timestamp is >10 minutes old, the Watchdog force-restarts the Python interface.

#### Weekly Maintenance
* **Trigger**: Every Sunday at 06:00 (or via Discord `/qrestart`).
* **QLOCK**: Severing all active file handles on the SSD array using the `openfiles` utility.
* **Log Rotation**: Deletion of `sshd.log` and `sftp-server.log` to prevent disk bloat.
* **System Refresh**: A forced reboot to clear residual RAM and finalize system updates.

---

### V. Emergency Backup & Recovery

* **Configuration Backup**: The Port Watcher creates a timestamped `.bak` of `sshd_config` every time a port change is detected.
* **Emergency Restore**: In the event of a system failure, a zipped backup archive of the scripts and configuration should be maintained on a secure cloud drive.
* **Manual Stop**: The `/qlock` command can be used via Discord to immediately kill the Watchdog and stop all SSH services in a security event.
