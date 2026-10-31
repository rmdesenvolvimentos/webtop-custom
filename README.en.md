# Webtop Custom (Windows 11 Style Cloud Desktop)

🌐 **Language / Idioma:**
[🇧🇷 Português](README.md) &nbsp;|&nbsp;
🇺🇸 English (current) &nbsp;|&nbsp;
[🇪🇸 Español](README.es.md) &nbsp;|&nbsp;
[🇩🇪 Deutsch](README.de.md) &nbsp;|&nbsp;
[🇫🇷 Français](README.fr.md) &nbsp;|&nbsp;
[🇮🇹 Italiano](README.it.md)

---

A customized, lightweight and elegant version of **Webtop** (Ubuntu XFCE) by [LinuxServer.io](https://fleet.linuxserver.io/image?name=linuxserver/webtop), transformed into a modern browser-accessible desktop with a **Windows 11** inspired interface, fluid lock screen authentication, graphical app store, advanced task manager, and an optimized Wine environment.

![Windows 11 Desktop](docs/screenshots/03-desktop.png)

---

## 📸 Interface Preview

### 🔒 Lock Screen & Login (Acrylic Blur)
| Lock Screen | Login Screen |
| :---: | :---: |
| ![Lockscreen](docs/screenshots/01-lockscreen.png) | ![Login](docs/screenshots/02-login.png) |

### 🪟 Start Menu & 📁 File Manager
| Start Menu (Whisker Menu) | File Manager (Thunar) |
| :---: | :---: |
| ![Start Menu](docs/screenshots/04-start-menu.png) | ![File Manager](docs/screenshots/07-file-manager.png) |

### 🛍️ Microsoft Store & 📊 Task Manager
| Microsoft Store (`win-store`) | Task Manager (`win_taskmgr`) |
| :---: | :---: |
| ![Microsoft Store](docs/screenshots/05-store.png) | ![Task Manager](docs/screenshots/06-taskmgr.png) |

---

## 🚀 Key Features

- **🪟 Windows 11 Style Interface**:
  - Centered taskbar (Docklike) and categorized Start Menu (Whisker Menu).
  - Official Windows 11 Bloom Dark wallpaper and modern dark theme.
- **🔒 Robust Security & Authentication**:
  - Windows 11 style login with acrylic blur background, real-time clock and user avatar.
  - Python authentication server (`auth_server.py`) integrated with Nginx subrequest auth.
  - **Anti-Brute-Force Protection**: Automatic IP lockout after 5 consecutive failed attempts.
  - **Nginx Rate Limiting**: Request-per-second limits against automated brute-force attacks.
  - **Timing Attack Protection**: Constant-time credential verification (`hmac.compare_digest`).
  - **Cryptographic Sessions**: HMAC-SHA256 tokens with timestamp, random nonce and 256-bit signature.
  - Manual lock via shortcut (`Ctrl + Alt + L`) or Start Menu button.
  - Configurable automatic lock on inactivity.
  - Graphical user preferences panel (`account-settings-gui`).
- **🌐 Direct IP Access on VPS (Ports 80 / 443)**:
  - No domain required: access by typing `http://<VPS-IP>` in the browser without specifying a port.
- **🛍️ Integrated Microsoft Store (`win-store`)**:
  - Friendly graphical interface built in Python/GTK3 to install, update and remove software.
- **📊 Windows-style Task Manager (`win_taskmgr`)**:
  - Real-time monitor for CPU, RAM, Disk and Network usage.
  - Process tree with forced termination and priority control.
- **📁 Stylized File Manager**:
  - Thunar with Eleven-Dark theme, modern Windows 11 icons and quick shortcuts.
- **🍷 Optimized Wine Support**:
  - Silent launcher (`win-launcher`) pre-configured with Esync/Fsync for running Windows `.exe` files.
- **⚡ High Performance & Low Footprint**:
  - Unnecessary services disabled at startup (PulseAudio dummy, CUPS, AT-SPI, UDisks2).
  - Minimal CPU and RAM usage at rest.

---

## 📋 Prerequisites

- Docker installed (version 20.10+)
- Docker Compose (v2+)

---

## 🛠️ How to Get Started

### ⚡ Option 1 – Automatic Setup with SSL (RECOMMENDED)

> Works on any clean VPS. Detects the IP, issues an **official Let's Encrypt certificate** and brings everything up in ~20 seconds.

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
chmod +x setup.sh && sudo ./setup.sh
```

The script **automatically**:
1. 🔍 Detects the public IP of the VPS
2. 🌐 Forms the domain `<YOUR_IP>.sslip.io` (no domain name required)
3. 🔒 Issues a real **Let's Encrypt** certificate (green padlock in browser)
4. 🐳 Starts the Docker container with HTTPS already configured
5. 🎉 Prints the final access URL

Final result:
```
✅  Desktop installed successfully and 100% secure!
🔒  Access now: https://123.456.7.890.sslip.io
```

> **Note:** Ports **80** and **443** must be open in your cloud provider's firewall (Azure NSG / AWS Security Group / Hetzner Firewall) before running setup.sh.

---

### 🐳 Option 2 – Zero-Touch (just `docker compose up -d`)

If you prefer not to run `setup.sh`, the container itself detects the IP and generates the SSL certificate on first boot:

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
docker compose up -d
```

> **Note:** Port 80 must be free at boot time for Let's Encrypt validation.

---

### ⚙️ Option 3 – Manual Setup

#### 1. Clone the repository
```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
```

#### 2. Configure environment variables
Copy the example file to `.env`:
```bash
cp .env.example .env
```

Edit `.env` to set your credentials and preferences:
```ini
# Login credentials
CUSTOM_USER=Admin
PASSWORD=AltereSuaSenhaForte123!

# Host ports (80 HTTP and 443 HTTPS for direct IP access)
PORT_HTTP=80
PORT_HTTPS=443

# Timezone and language
TZ=America/Sao_Paulo
LANG=pt_BR.UTF-8
LANGUAGE=pt_BR:pt
LC_ALL=pt_BR.UTF-8

# Hostname and title
HOSTNAME=cloud-vps
TITLE=Cloud Desktop
```

#### 3. Start the container
```bash
docker compose up -d
```

The container will pull the base image and, on first boot, automatically apply all configurations, themes, scripts and utilities.

---

## 🌐 How to Access

Open your browser and navigate to:
- **With SSL (setup.sh):** `https://<YOUR_IP>.sslip.io` — green padlock active ✅
- **HTTP:** `http://YOUR-VPS-IP`
- **HTTPS:** `https://YOUR-VPS-IP`

To unlock and enter the desktop, enter the password configured in the `.env` file.

---

## 🛡️ Security Layers

| Layer | Mechanism | Protection |
| :--- | :--- | :--- |
| **Nginx Ingress** | `limit_req_zone rate=5r/s` | DoS mitigation and automated scanner blocking. |
| **Anti-Brute Force** | Dynamic IP lockout | Temporary block after 5 incorrect passwords with intentional delay. |
| **Timing Attacks** | `hmac.compare_digest` | Constant-time hash verification preventing timing enumeration. |
| **Session Integrity** | HMAC-SHA256 Token | Cookies with `HttpOnly`, `SameSite=Lax` flags and 256-bit private key. |
| **Admin Privileges** | Authenticated Session | Sensitive endpoints require a valid active token. |
| **HTTP Headers** | Security Headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`. |

---

## 📁 Repository Structure

```text
webtop-custom/
├── .env.example              # Environment variable configuration example
├── .gitignore                # Git exclusion rules (ignores data, caches and credentials)
├── LICENSE                   # MIT License
├── README.md                 # Documentation (Português)
├── README.en.md              # Documentation (English)
├── setup.sh                  # One-command SSL installer
├── docker-compose.yml        # Docker service definition (ports 80 and 443)
├── docs/
│   └── screenshots/          # Demonstration screenshots
├── custom-cont-init.d/       # Startup scripts executed by s6-overlay
│   ├── 00-first-boot.sh      # Initializes themes and configs on first boot
│   ├── 00-hostname.sh        # Configures hostname and local DNS resolution
│   ├── 01-optimize.sh        # Optimizes system by disabling heavy services
│   ├── 10-install-apps.sh    # Installs essential utilities
│   ├── 20-auth-setup.sh      # Sets up secure Nginx, auth daemon and lock screen
│   └── 30-wine-setup.sh      # Wine performance tuning for running Windows apps
└── config-template/          # Template files copied to the user volume
    ├── account_settings_gui.py
    ├── auth_server.py
    ├── lock_manager.js
    ├── login_assets/
    │   ├── login.html
    │   └── wallpaper.jpg
    ├── nginx-default.conf
    ├── win-store.py
    ├── win_taskmgr.py
    └── win11-theme-pack.tar.gz
```

---

## ⌨️ Useful Shortcuts

- **Lock screen:** `Ctrl + Alt + L`
- **Task Manager:** `Ctrl + Shift + Esc` (or shortcut in Start Menu)
- **App Store:** Shortcut in taskbar or Start Menu

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
