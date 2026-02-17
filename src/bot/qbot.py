import discord
from discord import app_commands
from discord.ext import tasks 
import subprocess
import requests
import asyncio
import os
import shutil
import time
import json

# --- CONFIGURATION LOADER ---
try:
    # Looks for config.json two directories up (root of repo)
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.json'))
    
    with open(config_path, 'r') as f:
        CONFIG = json.load(f)
        
    print(f"✅ Configuration loaded from {config_path}")
except FileNotFoundError:
    print("❌ FATAL: config.json not found! Please rename 'config.example.json' and fill in your details.")
    exit()

# Setup Bot Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class QBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """
        Logic Path 1: Setup & Sync
        Ensures slash commands are synced.
        """
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

client = QBot()

# --- HEARTBEAT HANDSHAKE PROTOCOL ---

@tasks.loop(seconds=60)
async def heartbeat_check():
    """
    Logic Path 2: Handshake Protocol
    Updates the health file only if the gateway connection is active.
    """
    try:
        if client.is_ready(): 
            health_file = CONFIG['paths']['health_file']
            
            os.makedirs(os.path.dirname(health_file), exist_ok=True)
            
            with open(health_file, "w") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        print(f"Heartbeat report failed: {e}")

@client.event
async def on_ready():
    # Start the heartbeat loop ONLY after the bot is fully ready/connected
    if not heartbeat_check.is_running():
        heartbeat_check.start()
        
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Watchdog Heartbeat: ACTIVE')
    print('------')

# --- /QDRIVE ---

@client.tree.command(name="qdrive", description="Find QDRIVE's Current Coordinates")
async def qdrive(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
    except:
        ip = "Unknown (Internet Issues?)"

    port = "Not Found"
    try:
        with open(CONFIG['paths']['ssh_config'], 'r') as f:
            for line in f:
                if line.startswith('Port '):
                    port = line.split()[1]
                    break
    except Exception as e:
        port = f"Error reading config: {e}"

    status_cmd = subprocess.run(["powershell", "Get-Service sshd | Select-Object -ExpandProperty Status"], capture_output=True, text=True)
    svc_status = status_cmd.stdout.strip()
    
    if svc_status == "Running" and port.isdigit():
        qdrive_status = "Ready for connection"
    else:
        qdrive_status = "Service unreachable"

    embed = discord.Embed(title="Port Watcher", color=discord.Color.blue())
    embed.add_field(name="IP", value=ip, inline=False)
    embed.add_field(name="Port", value=port, inline=False)
    embed.add_field(name="QDRIVE Status", value=qdrive_status, inline=False)
    await interaction.followup.send(embed=embed)

# --- /QRESTART ---

class RestartVerification(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=30)
        self.interaction = interaction

    @discord.ui.button(label="YES", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🔄 **Authorization Confirmed.** Triggering maintenance...", view=None)
        await execute_qrestart(self.interaction)

    @discord.ui.button(label="NO", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ **Restart Aborted.**", view=None)

async def execute_qrestart(interaction: discord.Interaction):
    health_file = CONFIG['paths']['health_file']
    status_path = os.path.join(os.path.dirname(health_file), "maintenance_status.txt")
    
    if os.path.exists(status_path):
        os.remove(status_path)
    try:
        script_path = os.path.join(CONFIG['paths']['base_dir'], "WeeklyMaintenance", "WeeklyMaintenance.ps1")
        
        subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script_path])
        
        timeout, elapsed = 240, 0
        while elapsed < timeout:
            if os.path.exists(status_path):
                await interaction.followup.send("✅ **Reboot in 15 seconds...** QDRIVE will heal itself within 5 minutes.")
                return
            await asyncio.sleep(5)
            elapsed += 5
        await interaction.followup.send("❌ **maintenance failed**: Timeout.")
    except Exception as e:
        await interaction.followup.send(f"❌ **maintenance failed**: {e}")

@client.tree.command(name="qrestart", description="Manually Trigger Weekly Maintenance")
async def qrestart_trigger(interaction: discord.Interaction):
    if interaction.user.id != int(CONFIG['bot_settings']['admin_id']):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    view = RestartVerification(interaction)
    await interaction.response.send_message("⚠️ **Restart WORLDBOX?**", view=view, ephemeral=True)

# --- /QSTART ---

@client.tree.command(name="qstart", description="Awaken the Port Watcher")
async def qstart(interaction: discord.Interaction):
    if interaction.user.id != int(CONFIG['bot_settings']['admin_id']):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    TARGET_TITLE = "Administrator: C:\\WINDOWS\\SYSTEM32\\WindowsPowerShell\\v1.0\\powershell.exe"
    check_cmd = f'Get-Process | Where-Object {{$_.MainWindowTitle -eq "{TARGET_TITLE}"}}'
    
    check = subprocess.run(["powershell", "-Command", check_cmd], capture_output=True, text=True)
    if check.stdout.strip():
        await interaction.followup.send("⚠️ Port Watcher is already awake.")
        return
        
    try:
        subprocess.run(["powershell", "-Command", 'Start-ScheduledTask -TaskName "QDRIVE-Sync-ProtonPort"'], check=True)
        for _ in range(6):
            await asyncio.sleep(2)
            verify = subprocess.run(["powershell", "-Command", check_cmd], capture_output=True, text=True)
            if verify.stdout.strip():
                await interaction.followup.send("✅ **Port Watcher Awakened...**")
                return
        await interaction.followup.send("❌ **Start Failed**: Window did not appear.")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

# --- /QLOCK ---

@client.tree.command(name="qlock", description="Stop the QDRIVE")
async def qlock_stop(interaction: discord.Interaction):
    if interaction.user.id != int(CONFIG['bot_settings']['admin_id']):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    TARGET_TITLE = "Administrator: C:\\WINDOWS\\SYSTEM32\\WindowsPowerShell\\v1.0\\powershell.exe"
    PROFILE_PATH = CONFIG['paths']['powershell_profile']
    
    stop_logic = (
        f"Get-Process | Where-Object {{$_.MainWindowTitle -eq '{TARGET_TITLE}'}} | Stop-Process -Force -ErrorAction SilentlyContinue; "
        f". '{PROFILE_PATH}'; QLOCK"
    )
    
    try:
        process = await asyncio.create_subprocess_exec(
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", stop_logic,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        error_msg = stderr.decode().strip()
        
        if process.returncode == 0 and not error_msg:
            await interaction.followup.send("🔒 **QDRIVE Locked.** Port Watcher killed, **QDRIVE Offline.**")
        else:
            await interaction.followup.send(f"⚠️ **Lock Result**: {error_msg if error_msg else 'Done.'}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

# --- /QSTATUS ---

@client.tree.command(name="qstatus", description="QDRIVE System Status")
async def qreport(interaction: discord.Interaction):
    if interaction.user.id != int(CONFIG['bot_settings']['admin_id']):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)

    def get_disk_info(path, label):
        try:
            total, used, free = shutil.disk_usage(path)
            free_gb = free // (2**30)
            percent_free = (free / total) * 100
            return f"**{label}:** {free_gb} GB Free ({percent_free:.1f}%)"
        except:
            return f"**{label}:** Drive Unreachable"

    c_drive = get_disk_info("C:", "Internal (C)")
    ext_ssd_path = os.path.join(CONFIG['paths']['base_dir'], "Drive-Portal")
    q_drive = get_disk_info(ext_ssd_path, "External (SSD)")
    
    TARGET_TITLE = "Administrator: C:\\WINDOWS\\SYSTEM32\\WindowsPowerShell\\v1.0\\powershell.exe"
    check_cmd = f'Get-Process | Where-Object {{$_.MainWindowTitle -eq "{TARGET_TITLE}"}}'
    watchdog_check = subprocess.run(["powershell", "-Command", check_cmd], capture_output=True, text=True)
    watchdog_status = "🟢 ALIVE" if watchdog_check.stdout.strip() else "🔴 DEAD"

    embed = discord.Embed(title="📊 QDRIVE Dual-Storage Report", color=discord.Color.dark_grey())
    embed.add_field(name="Storage Levels", value=f"{c_drive}\n{q_drive}", inline=False)
    embed.add_field(name="Watchdog Status", value=watchdog_status, inline=True)
    await interaction.followup.send(embed=embed)

# --- /QADDKEY ---

class KeyVerification(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, vault: str, sshkey: str, target_path: str):
        super().__init__(timeout=30)
        self.interaction = interaction
        self.vault = vault
        self.sshkey = sshkey
        self.target_path = target_path

    @discord.ui.button(label="CONFIRM INJECTION", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            os.makedirs(os.path.dirname(self.target_path), exist_ok=True)
            with open(self.target_path, "a") as f:
                f.write(f"\n{self.sshkey.strip()}\n")
            await interaction.response.edit_message(content=f"✅ **Success:** Key injected into **{self.vault}**.", view=None)
        except Exception as e:
            await interaction.response.edit_message(content=f"❌ **Failed:** {e}", view=None)

    @discord.ui.button(label="CANCEL", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ **Injection Aborted.**", view=None)

@client.tree.command(name="qaddkey", description="Inject a key into a specific QDRIVE vault")
@app_commands.describe(vault="Target vault: 'qdrive' or 'qdriveadmin'", sshkey="The public SSH key")
async def qwhitelist(interaction: discord.Interaction, vault: str, sshkey: str):
    if interaction.user.id != int(CONFIG['bot_settings']['admin_id']):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    
    # SANITIZED: Load vaults explicitly from JSON
    vault_paths = {
        "qdrive": CONFIG['paths']['vault_qdrive'], 
        "qdriveadmin": CONFIG['paths']['vault_qdrive_admin']
    }
    
    target_path = vault_paths.get(vault.lower())
    if not target_path:
        await interaction.response.send_message("Invalid vault selection.", ephemeral=True)
        return
        
    view = KeyVerification(interaction, vault, sshkey, target_path)
    await interaction.response.send_message(f"⚠️ **Confirm SSH Key Injection?**\n**Target:** `{vault}`", view=view, ephemeral=True)

# --- /QDENY ---

@client.tree.command(name="qdeny", description="Deny QDRIVE user access to extSSD folder")
@app_commands.describe(foldername="Folder name inside Drive-Portal")
async def qdeny(interaction: discord.Interaction, foldername: str):
    if interaction.user.id != int(CONFIG['bot_settings']['admin_id']):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    target_path = os.path.join(CONFIG['paths']['base_dir'], "Drive-Portal", foldername)
    cmd = f'icacls "{target_path}" /deny "QDRIVE:(OI)(CI)(F)"'
    
    try:
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        if result.returncode == 0:
            await interaction.followup.send(f"🔒 **Success:** `{foldername}` locked for 'QDRIVE'.")
        else:
            await interaction.followup.send(f"❌ **Failed:** {result.stderr}")
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {e}")

# --- /QALLOW ---

@client.tree.command(name="qallow", description="Restore QDRIVE user access to extSSD folder")
@app_commands.describe(foldername="Folder name to unlock")
async def qallow(interaction: discord.Interaction, foldername: str):
    if interaction.user.id != int(CONFIG['bot_settings']['admin_id']):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    target_path = os.path.join(CONFIG['paths']['base_dir'], "Drive-Portal", foldername)
    cmd = f'icacls "{target_path}" /remove:d "QDRIVE"'
    
    try:
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        if result.returncode == 0:
            await interaction.followup.send(f"🔓 **Success:** `{foldername}` unlocked for 'QDRIVE'.")
        else:
            await interaction.followup.send(f"❌ **Failed:** {result.stderr}")
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {e}")

# --- STARTUP LOGIC (Simple Mode) ---

token = CONFIG['bot_settings'].get('token')

if not token or token == "INSERT_YOUR_TOKEN_HERE":
    print("❌ FATAL: You forgot to put your Bot Token in config.json!")
    exit()

print("✅ Token found. Launching QBOT...")
client.run(token)
