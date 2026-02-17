# QDRIVE: Client Connection Guide

This guide explains how to connect to the QDRIVE storage archive. While mobile connection is possible (via Termius on Android/iOS), this guide focuses on the Desktop setup. Because the server uses a dynamic VPN and enforces strict security, you must use an SSH key. Passwords are disabled.

---

### Phase 1: Install WinSCP
WinSCP is the recommended client for accessing the QDRIVE on a desktop.

1. **Download**: Get the installer from the [official WinSCP site](https://winscp.net/eng/download.php).
2. **Setup**: Run the installer and keep the default settings.

---

### Phase 2: Generate Your Security Key
The QDRIVE does not use passwords. You will create a "Public Key" to send to the admin and keep a "Private Key" on your own computer.

1.  **Open PuTTYgen**: In WinSCP’s login window, click **Tools** (bottom-left) and select **Run PuTTYgen**.
2.  **Key Type**: At the bottom, change the type to **EdDSA** (Scheme: Ed25519).
3.  **Generate**: Click **Generate** and move your mouse around the blank area until the bar is full.
4.  **Save Private Key**: Click **Save private key**. Name it `QDRIVE-KEY`. **Keep this safe.** If you lose it, you lose access.
5.  **Copy Public Key**: 
    * **STOP:** Do **NOT** click "Save public key". That format will not work.
    * **ACTION:** Look at the text box at the very top labeled *"Public key for pasting into OpenSSH authorized_keys file"*.
    * **COPY:** Select and copy that entire block of text (starts with `ssh-ed25519...`).
6.  **Whitelisting**: Send that copied text to the Admin via Discord private DM, Email, or any secure communication method.

---

### Phase 3: Connecting to the Archive
The QDRIVE is hosted behind a VPN, so the IP address and Port change often. Before logging in, you must use the Discord `/qdrive` command to get the current "coordinates."

1. **New Site**: In WinSCP, click **New Site**.
2. **Connection Info**:
   * **File Protocol**: SFTP.
   * **Host Name**: The IP provided by the bot.
   * **Port Number**: The Port provided by the bot.
   * **User name**: `QDRIVE`.
   * **Password**: Leave this empty.
3. **Attach Your Key**:
   * Click **Advanced...** and go to **SSH** > **Authentication**.
   * Under **Private key file**, select the key you saved in Phase 2.
4. **Login**: Click **OK**, then **Save**, and then **Login**.

---

### Phase 4: Server Verification (The Banner)
Because the IP and Port change, your computer might warn you that the "Host Key" has changed. This is normal for the QDRIVE.

To verify you are connecting to the correct server and not a spoofed one, look for the **"Mind Prison"** banner text in the terminal window upon connection. If you see the warning regarding a "Space Judge" and "Mind Prison," you have successfully reached the QDRIVE root at **`C:\QDRIVE`**.

---

### Troubleshooting
* **Connection Failed**: Double-check the Port number, and IP address in Discord (using `/qdrive`). The VPN rotations happen automatically, and the old port and IP will stop working immediately.
* **Access Denied**: Ensure your private key is correctly attached to your WinSCP profile and that you haven't typed anything into the password field.
