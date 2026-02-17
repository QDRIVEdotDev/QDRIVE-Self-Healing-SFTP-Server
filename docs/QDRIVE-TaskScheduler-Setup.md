# QDRIVE: Task Scheduler & Infrastructure Setup

This document outlines the mandatory configuration required to deploy the QDRIVE automation layer. To ensure the "Self-Healing" handshake protocol functions correctly, these tasks must be configured to match the logic defined in the source code.

---

### I. System Prerequisites
The host Windows environment must be prepared for administrative script execution and active file-handle monitoring.

1.  **Execution Policy**: Open an Administrative PowerShell terminal and run:
    `Set-ExecutionPolicy RemoteSigned -Force`
2.  **Global File Monitoring**: The `QLOCK` protocol requires the global "maintain objects list" flag to be active. Run:
    `openfiles /local on`
3.  **Reboot**: A full system restart is **REQUIRED** after enabling the `openfiles` flag for changes to take effect.
4.  **Local Accounts**: Create two non-administrator local Windows users named `QDRIVE` and `QDRIVEADMIN`.

---

### II. Task 1: The Port Watcher (Watchdog)
This task manages the `Sync-ProtonPort.ps1` script, which handles VPN port rotation, firewall updates, and monitoring the Discord bot's health.

* **Task Name**: `QDRIVE-Sync-ProtonPort`
* **Security Options**:
    * **User Account**: SYSTEM or Administrator.
    * **Run with highest privileges**: **REQUIRED**.
* **Triggers**:
    * **At System Startup** (or "At log on" for a visible console window).
* **Actions**:
    * **Action**: Start a program.
    * **Program/script**: `powershell.exe`
    * **Add arguments**: `-ExecutionPolicy Bypass -WindowStyle Normal -File "C:\QDRIVE-SYSTEM\src\watchdog\Sync-ProtonPort.ps1"`
* **Settings**:
    * Uncheck "Stop the task if it runs longer than..." (Must run 24/7).

---

### III. Task 2: The Bot Interface (Self-Healing)
This task is managed programmatically by the Watchdog. It launches the `qbot.py` interface and is automatically re-triggered if a process hang is detected.

* **Task Name**: `QBOT-Autostart`
* **Security Options**:
    * **Run with highest privileges**: **YES**.
* **Triggers**:
    * None (Triggered automatically by the Watchdog script).
* **Actions**:
    * **Action**: Start a program.
    * **Program/script**: `python.exe`
    * **Add arguments**: `"C:\QDRIVE-SYSTEM\src\bot\qbot.py"`
* **Settings**:
    * **"Allow task to be run on demand"**: YES.
    * **"If the task is already running"**: **Stop the existing instance** (Ensures clean restarts during healing events).

---

### IV. Automated Weekly Maintenance
This task ensures system stability by clearing file handles, rotating logs, and refreshing the OS environment.

* **Task Name**: `QDRIVE-Weekly-Maintenance`
* **Trigger**: Weekly (Recommended: **Sunday 06:00**).
* **Actions**:
    * **Action**: Start a program.
    * **Program/script**: `powershell.exe`
    * **Add arguments**: `-ExecutionPolicy Bypass -File "C:\QDRIVE-SYSTEM\src\maintenance\WeeklyMaintenance.ps1"`
* **Result**: Executes `QLOCK.ps1` to sever active file locks, deletes OpenSSH logs, and issues a `Restart-Computer -Force`.

---

### V. System Architecture Logic Flow

```mermaid
graph TD
    subgraph "External Control"
    A[User / Discord] -->|Commands| B(QBOT - Python)
    end

    subgraph "The Handshake Loop"
    B -->|Update Timestamp| C[qbot_health.txt]
    D[Sync-ProtonPort - PowerShell] -->|Watchdog: Check Heartbeat| C
    D -->|If Stale: Restart| B
    end

    subgraph "System Logic"
    D -->|Monitor VPN Logs| E{New Port?}
    E -->|Yes| F[Update sshd_config & Firewall]
    B -->|/qlock| G[QLOCK.ps1 - Terminate Locks]
    B -->|/qrestart| H[WeeklyMaintenance.ps1]
    H -->|Handshake| I[maintenance_status.txt]
    I -->|Confirm| B
    end

    subgraph "The Storage Portal"
    F -->|Enable Access| J[SFTP Server]
    J -->|Chroot| K[C:\QDRIVE\Drive-Portal]
    K -->|Mount| L[Internal/External SSDs]
    end
