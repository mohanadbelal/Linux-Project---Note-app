# NoteVault – Note-Taking Web Application

A full-stack note-taking web application built with Python (Flask) and MariaDB, featuring a modern dark glassmorphism design system, REST API, systemd service integration, and automated MariaDB backups to a secondary EBS volume.

---

## 📄 Documentation

- **[Full Documentation & Architecture Guide (DOCUMENTATION.md)](./DOCUMENTATION.md)** — Detailed technical specification, architecture diagrams, component details, local environment setup, EC2 deployment, and disaster recovery procedures.
- **[Step-by-Step EC2 Deployment Guide (DEPLOYMENT_GUIDE.md)](./DEPLOYMENT_GUIDE.md)** — Quick reference guide for deploying on Red Hat Enterprise Linux (RHEL), Amazon Linux 2023, and Ubuntu.

---

## 🚀 Quick Local Run

1. **Clone repository:**
   ```bash
   git clone https://github.com/mohanadbelal/Linux-Project---Note-app.git
   cd "Linux-Project---Note-app"
   ```

2. **Create virtual environment & install requirements:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Start MariaDB & create database:**
   ```sql
   CREATE DATABASE notesdb;
   CREATE USER 'noteuser'@'localhost' IDENTIFIED BY 'notepassword';
   GRANT ALL PRIVILEGES ON notesdb.* TO 'noteuser'@'localhost';
   ```

4. **Run Application:**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

---

## 🛠️ Main Tech Stack

- **Backend:** Python 3.11+, Flask 3.1, SQLAlchemy 3.1, PyMySQL, Gunicorn 23.0
- **Database:** MariaDB 10.5+ / 12.x
- **OS & Cloud:** RHEL 8/9 / Amazon Linux 2023 / Ubuntu, AWS EC2, AWS EBS
- **DevOps:** systemd, cron, bash, SELinux policies, ext4 filesystem
