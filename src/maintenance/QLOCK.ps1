function QLOCK {
    <#
    .SYNOPSIS
    Stops SSH services and surgically clears file locks on the Storage Array.
    Portfolio Version 1.0
    #>
    [CmdletBinding()]
    param()

    # --- CONFIGURATION ---
    # Default: Unlocks Q: (External) and C:\QDRIVE\Drive-Portal (Internal)
    $LockPattern = "Q:\\|C:\\QDRIVE\\Drive-Portal"

    # 1. Elevate check
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error "QLOCK requires Administrator privileges."
        return
    }

    try {
        Write-Host "QLOCK PROTOCOL INITIATED..." -ForegroundColor Magenta

        # 2. Stop the SSH Engine (Prevents new incoming locks)
        $SshService = Get-Service sshd -ErrorAction SilentlyContinue
        if ($null -ne $SshService -and $SshService.Status -ne 'Stopped') {
            Stop-Service sshd -Force -ErrorAction Stop
            Write-Host "SSH Service Halted." -ForegroundColor Yellow
        }

        # 3. Terminate residual SSH processes
        Get-Process sshd -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

        # 4. Handle File Locks (The Surgical Target)
        $RawLocks = openfiles /query /fo csv | Select-String -Pattern $LockPattern
        $LocksCleared = 0

        if ($RawLocks) {
            $RawLocks | ForEach-Object {
                # Parse the ID from the CSV output
                $Id = ($_.ToString() -split ',')[0].Trim('"')
                if ($Id -as [int]) {
                    openfiles /disconnect /id $Id > $null
                    $LocksCleared++
                }
            }
        }

        # 5. Verification Delay
        Start-Sleep -Seconds 2
        $RemainingLocks = openfiles /query /fo csv | Select-String -Pattern $LockPattern

        if ($RemainingLocks) {
            throw "Residual locks detected on the storage array after cleanup. Manual intervention required."
        }

        # 6. Success Report
        Write-Host "QLOCK COMPLETE. Locks Cleared: $LocksCleared" -ForegroundColor Green
    }
    catch {
        Write-Error "CRITICAL FAILURE: $($_.Exception.Message)"
    }
}
