# ==============================================================================
# WEEKLY MAINTENANCE ROUTINE
# ==============================================================================

# --- CONFIGURATION ---
$BasePath = "C:\QDRIVE-SYSTEM"
$LogPath  = "C:\ProgramData\ssh\logs"

# Output Files (Aligned with config.json structure)
$ReportFile = Join-Path $BasePath "maintenance_report.txt"
$StatusFile = Join-Path $BasePath "maintenance_status.txt"

# 1. Start a transcript to record every action
Start-Transcript -Path $ReportFile -Append

try {
    # 2. Load the QLOCK function from the sibling file
    # Uses $PSScriptRoot so it always finds QLOCK.ps1 in the same folder
    $QLockScript = Join-Path $PSScriptRoot "QLOCK.ps1"
    
    if (Test-Path $QLockScript) {
        . $QLockScript
    } else {
        throw "QLOCK.ps1 not found at $QLockScript"
    }

    Write-Host "Initiating Maintenance. Starting QLOCK..." -ForegroundColor Yellow

    # 3. Run QLOCK (Loaded from the script above)
    QLOCK

    # 4. Delete the log files only after QLOCK has cleared the locks
    if (Test-Path $LogPath) {
        Remove-Item -Path "$LogPath\sshd.log", "$LogPath\sftp-server.log" -Force -ErrorAction SilentlyContinue
        Write-Host "SSH Logs successfully deleted." -ForegroundColor Green
    }

    # --- HANDSHAKE SIGNAL ---
    # This file tells the Python Bot that the reboot is intentional
    "SUCCESS" | Set-Content -Path $StatusFile -Encoding Utf8

    # 5. Final safety wait before restart
    Write-Host "Maintenance complete. Restarting in 15 seconds..." -ForegroundColor Cyan
    Start-Sleep -Seconds 15
    Restart-Computer -Force

} catch {
    Write-Error "Maintenance Failed: $($_.Exception.Message)"
} finally {
    Stop-Transcript
}
