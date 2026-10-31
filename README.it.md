# Webtop Custom (Desktop Cloud stile Windows 11)

🌐 **Lingua / Language:**
[🇧🇷 Português](README.md) &nbsp;|&nbsp;
[🇺🇸 English](README.en.md) &nbsp;|&nbsp;
[🇪🇸 Español](README.es.md) &nbsp;|&nbsp;
[🇩🇪 Deutsch](README.de.md) &nbsp;|&nbsp;
[🇫🇷 Français](README.fr.md) &nbsp;|&nbsp;
🇮🇹 Italiano (attuale)

---

Una versione personalizzata, leggera ed elegante di **Webtop** (Ubuntu XFCE) di [LinuxServer.io](https://fleet.linuxserver.io/image?name=linuxserver/webtop), trasformata in un desktop moderno accessibile via browser con interfaccia ispirata a **Windows 11**, autenticazione con schermata di blocco fluida, store grafico, task manager avanzato e ambiente Wine ottimizzato.

![Desktop Windows 11](docs/screenshots/03-desktop.png)

---

## 📸 Anteprima interfaccia

### 🔒 Schermata di blocco & Accesso
| Schermata di blocco | Accesso |
| :---: | :---: |
| ![Lockscreen](docs/screenshots/01-lockscreen.png) | ![Login](docs/screenshots/02-login.png) |

### 🪟 Menu Start & 📁 Gestione file
| Menu Start | Gestione file |
| :---: | :---: |
| ![Menu Start](docs/screenshots/04-start-menu.png) | ![File](docs/screenshots/07-file-manager.png) |

---

## 🚀 Funzionalità principali

- **🪟 Interfaccia stile Windows 11** con barra delle applicazioni centrata e menu Start categorizzato
- **🔒 Sicurezza robusta**: autenticazione Python + Nginx, anti-brute-force, sessioni HMAC-SHA256
- **🌐 Accesso diretto tramite IP** sulle porte 80/443 senza dominio proprio
- **🛍️ Microsoft Store integrato** con oltre 79.000 pacchetti APT
- **📊 Gestione attività** stile Windows con CPU, RAM, Disco e Rete in tempo reale
- **🍷 Wine ottimizzato** per eseguire file `.exe` di Windows
- **🌐 Sistema multilingue**: 🇧🇷 PT · 🇺🇸 EN · 🇪🇸 ES · 🇩🇪 DE · 🇫🇷 FR · 🇮🇹 IT

---

## 📋 Prerequisiti

- Docker (versione 20.10+)
- Docker Compose (v2+)

---

## 🛠️ Come iniziare

### ⚡ Opzione 1 – Installazione automatica con SSL (CONSIGLIATA)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
chmod +x setup.sh && sudo ./setup.sh
```

Lo script esegue **automaticamente**:
1. 🔍 Rileva l'IP pubblico del VPS
2. 🌐 Crea il dominio `<TUO_IP>.sslip.io` (senza dominio proprio)
3. 🔒 Emette un certificato **Let's Encrypt** reale (lucchetto verde)
4. 🐳 Avvia il container Docker con HTTPS configurato
5. 🎉 Mostra l'URL di accesso solo quando il sistema è **100% pronto**

> **Nota:** Le porte **80** e **443** devono essere aperte nel firewall del provider (Azure NSG / AWS Security Group / Hetzner).

---

### 🐳 Opzione 2 – Zero-Touch (`docker compose up -d`)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
docker compose up -d
```

---

### ⚙️ Opzione 3 – Configurazione manuale

```bash
cp .env.example .env
# Modifica .env con le tue credenziali
docker compose up -d
```

---

## 🌐 Come accedere

- **Con SSL:** `https://<TUO_IP>.sslip.io` — lucchetto verde ✅
- **HTTP:** `http://IP-DEL-TUO-VPS`

---

## 🌍 Sistema multilingue

Al **primo accesso**, si apre automaticamente un assistente per la selezione della lingua:

| Bandiera | Lingua |
|:---:|---|
| 🇧🇷 | Português (Brasil) |
| 🇺🇸 | English (United States) |
| 🇪🇸 | Español |
| 🇩🇪 | Deutsch |
| 🇫🇷 | Français |
| 🇮🇹 | Italiano |

La preferenza viene applicata automaticamente all'intera sessione e alle applicazioni del desktop.

---

## ⌨️ Scorciatoie utili

- **Blocca schermo:** `Ctrl + Alt + L`
- **Gestione attività:** `Ctrl + Maiusc + Esc`
- **Store:** collegamento nella barra delle applicazioni

---

## 📄 Licenza

Questo progetto è distribuito con licenza MIT — vedi il file [LICENSE](LICENSE).
