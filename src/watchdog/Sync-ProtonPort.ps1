# Requires -RunAsAdministrator
# ==============================================================================
# QDRIVE PORT WATCHDOG
# Portfolio Version 1.0
# ==============================================================================

# --- CONFIGURATION ---
# Users: Edit these variables to match your environment
$BasePath         = "C:\QDRIVE-SYSTEM"
$ConfigPath       = "C:\ProgramData\ssh\sshd_config"
$LogDir           = "$env:LOCALAPPDATA\Proton\Proton VPN\Logs"
$FirewallRuleName = "OpenSSH Server (ProtonVPN Dynamic)"
$BotTaskName      = "QBOT-Autostart"

# Derived Paths (Matches the structure in config.json)
$HealthFile       = Join-Path $BasePath "qbot_health.txt"

# ==============================================================================

function Get-ProtonPortFromClientLog {
    try {
        # Find the latest log file
        $LogFile = Get-ChildItem -Path $LogDir -Filter "client-logs.txt" -Recurse | 
                   Sort-Object LastWriteTime -Descending | 
                   Select-Object -First 1

        if ($null -eq $LogFile) {
            Write-Warning "Could not find 'client-logs.txt' in $LogDir"
            return $null
        }

        # Open file with 'ReadWrite' share mode to avoid locking issues
        $FileStream = New-Object System.IO.FileStream($LogFile.FullName, 'Open', 'Read', 'ReadWrite')
        $Reader = New-Object System.IO.StreamReader($FileStream)
        
        # Optimization: Only read the last 2000 characters to find the latest port
        if ($FileStream.Length -gt 2000) {
            $FileStream.Seek(-2000, [System.IO.SeekOrigin]::End) | Out-Null
        }
        $LogContent = $Reader.ReadToEnd()
        $Reader.Close(); $FileStream.Close()

        # Regex: Matches the first number in "Port pair 56105->56105"
        # Search RightToLeft to ensure we get the absolute latest entry
        $Pattern = 'Port pair\s+(\d+)->'
        $Match = [regex]::Match($LogContent, $Pattern, [System.Text.RegularExpressions.RegexOptions]::RightToLeft)

        if ($Match.Success) {
            return [int]$Match.Groups[1].Value
        }
    } catch {
        Write-Host "Error accessing logs: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $null
}

# --- Main Logic ---

# 1. Elevation Check
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator."
    return
}

Write-Host "Monitoring Proton VPN... Press Ctrl+C to stop." -ForegroundColor Yellow

while($true) {

    if ((Get-Service sshd).Status -ne 'Running') {
        Start-Service sshd -ErrorAction SilentlyContinue
        Write-Host "SSHD was stopped. Port Watcher has started it." -ForegroundColor Yellow
    }

    $NewPort = Get-ProtonPortFromClientLog

    if ($null -ne $NewPort) {
        if (-not (Test-Path $ConfigPath)) {
            Write-Error "SSH Config not found at $ConfigPath"
        } else {
            $ConfigContent = Get-Content $ConfigPath
            $CurrentLine = $ConfigContent | Select-String "^\s*#?\s*Port\s+(\S+)"
            $CurrentPort = if ($CurrentLine) { $CurrentLine.Matches.Groups[1].Value.Trim() } else { "22" }

            if ("$NewPort" -ne "$CurrentPort") {
                Write-Host "New Port Spotted, Captain! $NewPort (Current SSH: $CurrentPort)" -ForegroundColor Green
                
                # 2. Backup SSH Config
                Copy-Item $ConfigPath "$ConfigPath.bak.$(Get-Date -Format 'yyyyMMddHHmm')"
                
                # 3. Update SSH Config File (using UTF8 for modern OpenSSH compatibility)
                if ($CurrentLine) {
                    $ConfigContent = $ConfigContent -replace "^\s*#?\s*Port\s+\S+", "Port $NewPort"
                } else {
                    $ConfigContent = @("Port $NewPort") + $ConfigContent
                }
                $ConfigContent | Set-Content $ConfigPath -Encoding Utf8

                # 4. Update Windows Firewall
                $ExistingRule = Get-NetFirewallRule -DisplayName $FirewallRuleName -ErrorAction SilentlyContinue
                if ($ExistingRule) {
                    Set-NetFirewallRule -DisplayName $FirewallRuleName -LocalPort $NewPort
                    Write-Host "Firewall rule '$FirewallRuleName' updated to port $NewPort." -ForegroundColor Cyan
                } else {
                    New-NetFirewallRule -DisplayName $FirewallRuleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $NewPort
                    Write-Host "Created new firewall rule for port $NewPort." -ForegroundColor Cyan
                }

                # 5. Restart SSH Service
                if (Get-Service sshd -ErrorAction SilentlyContinue) {
                    Restart-Service sshd -Force
                    Write-Host "SSHD service restarted on port $NewPort." -ForegroundColor Green
                } else {
                    Write-Warning "SSHD service not found. Please ensure OpenSSH Server is installed."
                }
            } else {
                Write-Host "." -NoNewline -ForegroundColor Gray
            }
        }
    } else {
        Write-Warning "Failed to extract port. Check if Port Forwarding is active in Proton VPN."
        
        $ConfigContent = Get-Content $ConfigPath
        if ($ConfigContent -notmatch "^# Port OFFLINE") {
            $ConfigContent = $ConfigContent -replace "^\s*#?\s*Port\s+.*", "# Port OFFLINE"
            $ConfigContent | Set-Content $ConfigPath -Encoding Utf8
            Write-Host "Config updated to: # Port OFFLINE" -ForegroundColor Yellow
        }
    }

# --- QBot Handshake Watchdog ---
    
    $PythonProc = Get-Process -Name "python" -ErrorAction SilentlyContinue

    # 1. If the process is NOT running, start it.
    if ($null -eq $PythonProc) {
        Write-Warning "QBot process not found. Triggering startup task."
        Start-ScheduledTask -TaskName $BotTaskName
    }
    # 2. If the process IS running, check if it's "stale".
    elseif (Test-Path $HealthFile) {
        $LastHeartbeat = [datetime](Get-Content $HealthFile)
        $TimeDiff = (Get-Date) - $LastHeartbeat

        if ($TimeDiff.TotalMinutes -gt 10) { 
            Write-Host "ALERT: QBot heartbeat stale ($($TimeDiff.TotalMinutes) min). Restarting..." -ForegroundColor Red
            $PythonProc | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-ScheduledTask -TaskName $BotTaskName
        }
    }

    Start-Sleep -Seconds 60
}
