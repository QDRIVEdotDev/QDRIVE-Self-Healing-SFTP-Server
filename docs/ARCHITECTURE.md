# QDRIVE System Architecture

This document provides a deep-dive into the technical engineering behind the **QDRIVE Autonomous Infrastructure**, specifically the interplay between the Python-based management interface and the PowerShell-based system watchdog.

---

### 1. The Handshake Protocol (Self-Healing Loop)

The core reliability of the QDRIVE is maintained through a bidirectional "Handshake" designed to prevent process hangs and ensure the Discord interface remains online.

* **Heartbeat Generation**: The `qbot.py` service executes a perpetual loop every 60 seconds. 
* **Validation Check**: The bot verifies its own connection state via `client.is_ready()` before acting. 
* **The Health Signal**: Upon successful validation, it writes the current timestamp to `qbot_health.txt`, which is located in the system base directory. 
* **Active Monitoring**: The `Sync-ProtonPort.ps1` script monitors this file. 
* **Self-Healing Trigger**: If the Watchdog detects the timestamp is older than 10 minutes or the process is missing, it force-terminates all Python instances and restarts the bot via Task Scheduler.

---

### 2. Dynamic Port Synchronization

To manage VPN environments where port-forwarding assignments are dynamic, the system automates the network re-configuration process without human intervention.

* **Log Extraction**: `Sync-ProtonPort.ps1` utilizes regex to parse the absolute latest entry in the Proton VPN client logs. 
* **Validation**: It matches the current `sshd_config` port against the extracted value. 
* **System Update**: If a discrepancy is found, the script updates the `sshd_config` file using UTF8 encoding and backs up the previous configuration. 
* **Network Persistence**: The script automatically updates the "OpenSSH Server (ProtonVPN Dynamic)" firewall rule to match the new port. 
* **Service Refresh**: The `sshd` service is restarted to apply the changes, ensuring immediate availability.

---

### 3. Storage Portal & Isolation

The storage architecture is designed to support high-security SFTP requirements, including user isolation (Chroot) and multi-disk bridging.

* **The Chroot Portal**: A specialized directory at `C:\QDRIVE\Drive-Portal` serves as the mount point for external and internal storage arrays. 
* **Configuration**: The `sshd_config.example` defines strict `ChrootDirectory` paths for both the `QDRIVE` and `QDRIVEADMIN` users. 
* **Security Defaults**: Password authentication is strictly disabled in favor of Public Key (EdDSA/AES-GCM) standards. 
* **Access Control**: Discord-based ChatOps allows for real-time `icacls` permission manipulation to deny or allow access to specific folders on the array.

---

### 4. Surgical Maintenance (QLOCK)

The maintenance routine ensures system stability through automated deep-refreshes.

* **Handle Termination**: The `QLOCK.ps1` logic utilizes the `openfiles` utility to identify and disconnect active file handles targeting the storage array patterns. 
* **Log Rotation**: The `WeeklyMaintenance.ps1` script halts the SSH engine and deletes the `sshd.log` and `sftp-server.log` files to prevent disk bloat. 
* **Handshake Confirmation**: A `maintenance_status.txt` file is generated containing "SUCCESS" to signal the Bot that the intentional reboot is initiating. 
* **Full Reset**: A forced system restart clears residual RAM and finalizes maintenance every Sunday.

---

### 5. Repository Integrity Logic

The system is configured to be portable, using a unified base directory (`C:\QDRIVE-SYSTEM`) to store all logs, health signals, and configuration templates. 

* **Config Loader**: `qbot.py` utilizes relative pathing to locate the `config.json` at the repository root. 
* **Path Alignment**: PowerShell scripts utilize `$PSScriptRoot` to dynamically load sibling dependencies, such as `QLOCK.ps1`, ensuring the scripts can be moved to any folder while maintaining functionality.
