# Webtop Custom (Cloud-Desktop im Windows-11-Stil)

🌐 **Sprache / Language:**
[🇧🇷 Português](README.md) &nbsp;|&nbsp;
[🇺🇸 English](README.en.md) &nbsp;|&nbsp;
[🇪🇸 Español](README.es.md) &nbsp;|&nbsp;
🇩🇪 Deutsch (aktuell) &nbsp;|&nbsp;
[🇫🇷 Français](README.fr.md) &nbsp;|&nbsp;
[🇮🇹 Italiano](README.it.md)

---

Eine angepasste, leichte und elegante Version von **Webtop** (Ubuntu XFCE) von [LinuxServer.io](https://fleet.linuxserver.io/image?name=linuxserver/webtop), verwandelt in einen modernen, browserbasierten Desktop mit **Windows-11**-Oberfläche, flüssigem Sperrbildschirm, grafischem App-Store, erweitertem Task-Manager und optimierter Wine-Umgebung.

![Windows-11-Desktop](docs/screenshots/03-desktop.png)

---

## 📸 Oberflächen-Vorschau

### 🔒 Sperrbildschirm & Anmeldung
| Sperrbildschirm | Anmeldung |
| :---: | :---: |
| ![Lockscreen](docs/screenshots/01-lockscreen.png) | ![Login](docs/screenshots/02-login.png) |

### 🪟 Startmenü & 📁 Dateimanager
| Startmenü | Dateimanager |
| :---: | :---: |
| ![Startmenü](docs/screenshots/04-start-menu.png) | ![Dateimanager](docs/screenshots/07-file-manager.png) |

---

## 🚀 Hauptfunktionen

- **🪟 Windows-11-Oberfläche** mit zentrierter Taskleiste und kategorisiertem Startmenü
- **🔒 Robuste Sicherheit**: Python + Nginx-Authentifizierung, Anti-Brute-Force, HMAC-SHA256-Sitzungen
- **🌐 Direkter IP-Zugriff** auf Ports 80/443 ohne eigene Domain
- **🛍️ Integrierter Microsoft Store** mit 79.000+ APT-Paketen
- **📊 Task-Manager** im Windows-Stil mit Echtzeit-CPU, RAM, Disk und Netzwerk
- **🍷 Optimiertes Wine** zum Ausführen von Windows-`.exe`-Dateien
- **🌐 Mehrsprachiges System**: 🇧🇷 PT · 🇺🇸 EN · 🇪🇸 ES · 🇩🇪 DE · 🇫🇷 FR · 🇮🇹 IT

---

## 📋 Voraussetzungen

- Docker (Version 20.10+)
- Docker Compose (v2+)

---

## 🛠️ Erste Schritte

### ⚡ Option 1 – Automatische Installation mit SSL (EMPFOHLEN)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
chmod +x setup.sh && sudo ./setup.sh
```

Das Skript erledigt **automatisch**:
1. 🔍 Erkennt die öffentliche IP der VPS
2. 🌐 Erstellt die Domain `<DEINE_IP>.sslip.io` (ohne eigene Domain)
3. 🔒 Stellt ein echtes **Let's Encrypt**-Zertifikat aus (grünes Schloss)
4. 🐳 Startet den Docker-Container mit HTTPS
5. 🎉 Zeigt die Zugriffs-URL erst wenn das System **100% bereit** ist

> **Hinweis:** Die Ports **80** und **443** müssen in der Cloud-Firewall geöffnet sein (Azure NSG / AWS Security Group / Hetzner).

---

### 🐳 Option 2 – Zero-Touch (`docker compose up -d`)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
docker compose up -d
```

---

### ⚙️ Option 3 – Manuelle Konfiguration

```bash
cp .env.example .env
# .env mit deinen Zugangsdaten bearbeiten
docker compose up -d
```

---

## 🌐 Zugriff

- **Mit SSL:** `https://<DEINE_IP>.sslip.io` — grünes Schloss ✅
- **HTTP:** `http://IP-DEINER-VPS`

---

## 🌍 Mehrsprachiges System

Beim **ersten Login** öffnet sich automatisch ein Sprachassistent zur Auswahl:

| Flagge | Sprache |
|:---:|---|
| 🇧🇷 | Português (Brasil) |
| 🇺🇸 | English (United States) |
| 🇪🇸 | Español |
| 🇩🇪 | Deutsch |
| 🇫🇷 | Français |
| 🇮🇹 | Italiano |

Die Einstellung wird automatisch auf die gesamte Sitzung und alle Desktop-Apps angewendet.

---

## ⌨️ Nützliche Tastenkürzel

- **Bildschirm sperren:** `Strg + Alt + L`
- **Task-Manager:** `Strg + Umschalt + Esc`
- **App-Store:** Verknüpfung in der Taskleiste

---

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz — siehe [LICENSE](LICENSE).
