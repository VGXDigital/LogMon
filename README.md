<p align="center">
  <a href="https://vgx.digital">
    <img src="https://vgx.digital/vgx_email_sig.png" alt="VGX Consulting" width="200">
  </a>
</p>

# 📋 LogMon

**Simple, automated log file monitoring with email notifications.**

[![Release](https://img.shields.io/github/v/release/VGXDigital/LogMon?style=flat-square)](https://github.com/VGXDigital/LogMon/releases/latest)
[![License](https://img.shields.io/badge/license-Proprietary-blue?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20x86__64-lightgrey?style=flat-square)]()

Scan your log files for errors, exceptions, and warnings — get instant email alerts when issues are detected.

---

## ✨ Features

| Feature                        | Description                                                                    |
| ------------------------------ | ------------------------------------------------------------------------------ |
| 🔍 **Smart Pattern Detection** | Detects errors, exceptions, warnings, timeouts, and more using optimized regex |
| 📧 **Email Notifications**     | Instant HTML email alerts via secure SMTP/SSL                                  |
| ⚡ **High Performance**         | Concurrent scanning with thread pools and compiled regex                       |
| ⏱️ **Incremental Scanning**    | Only scans new content since last check — efficient for cron                   |
| 📦 **Standalone Executable**   | No Python required on your servers                                             |
| 🔄 **Self-Updating**           | Automatically updates itself from GitHub Releases (once daily)                 |
| 🔧 **Flexible Configuration**  | Environment variables or config file                                           |

---

## 🆕 What's New in v1.4.2

- **Self-updating**: LogMon auto-updates itself from GitHub Releases (checks once daily)
- **One-line install**: `curl -sfL https://raw.githubusercontent.com/VGXDigital/LogMon/main/install.sh | bash`
- **Manual update**: `./log_monitor --update`
- **Smart config lookup**: finds `log_monitor.conf` next to the binary or in the current directory
- **Disable auto-update**: set `auto_update = false` in `[Settings]`
- Fix: Handle quoted values in config file

---

## 📦 Installation

### Option 1: One-Line Install (Recommended)

```bash
curl -sfL https://raw.githubusercontent.com/VGXDigital/LogMon/main/install.sh | bash
```

Or specify an install directory:
```bash
curl -sfL https://raw.githubusercontent.com/VGXDigital/LogMon/main/install.sh | bash -s -- /opt/logmon
```

Then configure and test:
```bash
cp log_monitor.conf.example log_monitor.conf
nano log_monitor.conf
./log_monitor --debug
```

### Option 2: Run with Python

```bash
# Clone the repository
git clone https://github.com/VGXDigital/LogMon.git
cd LogMon

# Configure
cp log_monitor.conf.example log_monitor.conf
nano log_monitor.conf

# Run
python3 log_monitor.py --debug
```

---

## 🔧 Configuration

Edit `log_monitor.conf` with your settings:

```ini
[SMTP]
server = smtp.example.com
port = 465
username = your_smtp_username
password = your_smtp_password
from_email = monitoring@example.com
to_email = admin@example.com

[Paths]
log_dir = /var/log/myapp

[Settings]
# Auto-update is on by default. Disable with:
auto_update = false
```

The config file is looked up in this order:
1. Current working directory
2. Same directory as the `log_monitor` binary

### Environment Variables

Environment variables override config file settings. Use the `VGX_LM_` prefix:

| Variable               | Description                       |
| ---------------------- | --------------------------------- |
| `VGX_LM_SMTP_SERVER`   | SMTP server hostname              |
| `VGX_LM_SMTP_PORT`     | SMTP port (default: 465)          |
| `VGX_LM_SMTP_USERNAME` | SMTP username                     |
| `VGX_LM_SMTP_PASSWORD` | SMTP password                     |
| `VGX_LM_SMTP_FROM`     | From email address                |
| `VGX_LM_SMTP_TO`       | Recipient email address           |
| `VGX_LM_LOG_DIR`       | Directory to scan for *.log files |

---

## 🔍 Detected Patterns

LogMon scans for these error indicators:

```
error, fail, exception, traceback, critical, fatal,
warning, not found, permission denied, connection refused,
timeout, unable to, could not, exit code, returned non-zero,
aborted, killed
```

---

## ⏰ Automation (Cron)

Add to crontab for automated monitoring:

```bash
# Edit crontab
crontab -e

# Run every 15 minutes
*/15 * * * * cd /path/to/logmon && ./log_monitor

# Or with debug logging
*/15 * * * * cd /path/to/logmon && ./log_monitor --debug >> /var/log/logmon.log 2>&1
```

---

## 📖 Usage

```bash
# Normal mode (silent unless errors found)
./log_monitor

# Debug mode (detailed output)
./log_monitor --debug

# Check for and install latest version
./log_monitor --update

# Show version
./log_monitor --version
```

---

## 📧 Email Alert Example

When errors are detected, you'll receive an HTML email like:

> **Log Monitor Alert: 3 error(s) detected**
> 
> | File                   | Line | Content                     | Timestamp           |
> | ---------------------- | ---- | --------------------------- | ------------------- |
> | /var/log/app/error.log | 142  | `ERROR: Connection timeout` | 2026-01-22 10:15:32 |
> | /var/log/app/app.log   | 89   | `Exception in thread main`  | 2026-01-22 10:15:32 |

---

## 🏗️ Building from Source

```bash
# Install build dependencies
pip install -r requirements.txt

# Build standalone executable
pyinstaller --onefile --name log_monitor log_monitor.py

# Executable will be at dist/log_monitor
```

---

## 📄 License

**Proprietary Software** — © 2026 [VGX Consulting](https://vgx.digital). All rights reserved.

Unauthorized copying, modification, distribution, or use of this software is strictly prohibited.

---

<p align="center">
  Made with ❤️ by <a href="https://vgx.digital">VGX Consulting</a>
</p>