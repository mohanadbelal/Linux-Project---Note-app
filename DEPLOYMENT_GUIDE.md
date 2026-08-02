# NoteVault – EC2 Deployment Guide

Complete step-by-step guide to deploy the note-taking app on your EC2 instance with MariaDB and EBS backup volume.

---

## Prerequisites

| Item | Details |
|---|---|
| EC2 Instance | Amazon Linux 2023, Ubuntu 22.04+, or RHEL 8/9 |
| Security Group | Inbound rules: **SSH (22)**, **HTTP (80)**, **App (5000)** |
| Additional EBS Volume | Attached to the instance (for backups) |

---

## Step 1 — Connect to Your EC2 Instance

```bash
ssh -i your-key.pem ec2-user@<YOUR_EC2_PUBLIC_IP>
```

> **Note:** Use `ubuntu` instead of `ec2-user` if you're running Ubuntu. On RHEL, the default user is also `ec2-user`.

---

## Step 2 — Install System Dependencies

### Amazon Linux 2023

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip mariadb105-server git
```

### RHEL 8 / 9 (Red Hat Enterprise Linux)

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip mariadb-server git
```

> **Note (RHEL 8 only):** If `mariadb-server` is not found, enable the AppStream module first:
> ```bash
> sudo dnf module enable mariadb:10.5 -y
> sudo dnf install -y mariadb-server
> ```

### Ubuntu 22.04+

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv mariadb-server git
```

---

## Step 3 — Start and Secure MariaDB

```bash
# Start MariaDB and enable on boot
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Run the security wizard
sudo mysql_secure_installation
```

During `mysql_secure_installation`:
- Set a **root password** (e.g. `MyR00tP@ss!`)
- Remove anonymous users → **Y**
- Disallow root login remotely → **Y**
- Remove test database → **Y**
- Reload privilege tables → **Y**

---

## Step 4 — Create the Database and App User

```bash
sudo mysql -u root -p
```

Run these SQL commands inside the MariaDB shell:

```sql
CREATE DATABASE notesdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'noteuser'@'localhost' IDENTIFIED BY 'notepassword';

GRANT ALL PRIVILEGES ON notesdb.* TO 'noteuser'@'localhost';

FLUSH PRIVILEGES;

EXIT;
```

> **⚠️ Warning:** Change `notepassword` to a strong password in production. If you change it, also update the `DB_PASS` environment variable in Step 6.

---

## Step 5 — Upload and Set Up the Application

### Option A: SCP from your local machine

```bash
# Run this from your LOCAL machine (not the EC2 instance)
scp -i your-key.pem -r "Linux Project - Note app/" ec2-user@<YOUR_EC2_PUBLIC_IP>:~/note-taking-app
```

### Option B: Clone from a Git repo (if you push the code)

```bash
# On the EC2 instance
git clone https://github.com/mohanadbelal/Linux-Project---Note-app ~/note-taking-app
```

### Install Python dependencies

```bash
cd ~/note-taking-app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

## Step 6 — Configure Environment Variables

Create an `.env` file or export variables directly:

```bash
export DB_USER="noteuser"
export DB_PASS="notepassword"
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_NAME="notesdb"
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

> **💡 Tip:** Add these exports to `~/.bashrc` so they persist across SSH sessions.

---

## Step 7 — Test the Application

```bash
cd ~/note-taking-app
source venv/bin/activate
python3 app.py
```

Visit `http://<YOUR_EC2_PUBLIC_IP>:5000` in your browser. You should see the NoteVault interface.

Press `Ctrl+C` to stop the dev server once you've confirmed it works.

---

## Step 8 — Run with Gunicorn (Production)

```bash
# Start Gunicorn (production WSGI server)
cd ~/note-taking-app
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 --workers 3 app:app
```

### Run as a systemd service (auto-restart on reboot)

```bash
sudo tee /etc/systemd/system/notevault.service > /dev/null <<EOF
[Unit]
Description=NoteVault Flask App
After=network.target mariadb.service

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/note-taking-app
Environment="PATH=/home/ec2-user/note-taking-app/venv/bin"
Environment="DB_USER=noteuser"
Environment="DB_PASS=notepassword"
Environment="DB_HOST=localhost"
Environment="DB_PORT=3306"
Environment="DB_NAME=notesdb"
Environment="SECRET_KEY=change-this-to-a-random-secret"
ExecStart=/home/ec2-user/note-taking-app/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

```bash
sudo systemctl daemon-reload
sudo systemctl start notevault
sudo systemctl enable notevault

# Check status
sudo systemctl status notevault
```

> **Note:** Replace `ec2-user` with `ubuntu` in the service file if you're on Ubuntu. The `User`/`Group` and all paths must match the user that owns the app files.

> **⚠️ RHEL/SELinux:** If the service fails with `status=203/EXEC`, SELinux is blocking Gunicorn. Fix it with:
> ```bash
> sudo chcon -R -t bin_t /home/ec2-user/note-taking-app/venv/bin/
> sudo systemctl restart notevault
> ```

---

## Step 9 — Mount the Additional EBS Volume for Backups

### 9a. Identify the volume

```bash
lsblk
```

You'll see something like:

```
NAME    MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
xvda    202:0    0  8G  0 disk
└─xvda1 202:1    0  8G  0 part /
xvdf    202:80   0 10G  0 disk             ← your backup volume
```

### 9b. Format the volume (only the first time!)

> **🚨 Caution:** Only run `mkfs` once on a new volume. Running it on an existing volume will **erase all data**.

```bash
sudo mkfs.ext4 /dev/xvdf
```

### 9c. Create mount point and mount

```bash
sudo mkdir -p /mnt/backup
sudo mount /dev/xvdf /mnt/backup
sudo chown ec2-user:ec2-user /mnt/backup
```

### 9d. Auto-mount on reboot

```bash
# Get the UUID
sudo blkid /dev/xvdf
# Example output: /dev/xvdf: UUID="a1b2c3d4-..." TYPE="ext4"

# Add to fstab (replace the UUID)
echo 'UUID=a1b2c3d4-your-uuid-here /mnt/backup ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab

# Verify fstab is valid
sudo mount -a
```

---

## Step 10 — Set Up MariaDB Backups

### 10a. Copy the backup script

```bash
cp ~/note-taking-app/backup_mariadb.sh ~/backup_mariadb.sh
chmod +x ~/backup_mariadb.sh
```

> **❗ Important:** If you changed the database password in Step 4, edit the `DB_PASS` variable in `backup_mariadb.sh` to match.

### 10b. Test the backup manually

```bash
~/backup_mariadb.sh
```

Expected output:

```
[Sun Aug 02 19:30:00 UTC 2026] Starting backup of 'notesdb'...
[Sun Aug 02 19:30:01 UTC 2026] Backup saved to: /mnt/backup/mariadb/notesdb_backup_20260802_193001.sql.gz
[Sun Aug 02 19:30:01 UTC 2026] Backup successful (4.0K).
[Sun Aug 02 19:30:01 UTC 2026] Cleaning up backups older than 7 days...
[Sun Aug 02 19:30:01 UTC 2026] Cleanup complete.
```

### 10c. Schedule automatic daily backups with cron

```bash
crontab -e
```

Add this line to run the backup every day at 2:00 AM:

```cron
* * * * * /home/ec2-user/backup_mariadb.sh >> /mnt/backup/mariadb/backup.log 2>&1
```

### 10d. Restore from a backup (if needed)

```bash
gunzip < /mnt/backup/mariadb/notesdb_backup_XXXXXXXX_XXXXXX.sql.gz | mysql -u noteuser -p notesdb
```

---

## Quick Reference

| Action | Command |
|---|---|
| Start the app | `sudo systemctl start notevault` |
| Stop the app | `sudo systemctl stop notevault` |
| View app logs | `sudo journalctl -u notevault -f` |
| Start MariaDB | `sudo systemctl start mariadb` |
| Stop MariaDB | `sudo systemctl stop mariadb` |
| Manual backup | `~/backup_mariadb.sh` |
| List backups | `ls -lh /mnt/backup/mariadb/` |
| MariaDB shell | `sudo mysql -u root -p` |
