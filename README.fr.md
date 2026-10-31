# Webtop Custom (Bureau Cloud style Windows 11)

🌐 **Langue / Language:**
[🇧🇷 Português](README.md) &nbsp;|&nbsp;
[🇺🇸 English](README.en.md) &nbsp;|&nbsp;
[🇪🇸 Español](README.es.md) &nbsp;|&nbsp;
[🇩🇪 Deutsch](README.de.md) &nbsp;|&nbsp;
🇫🇷 Français (actuel) &nbsp;|&nbsp;
[🇮🇹 Italiano](README.it.md)

---

Une version personnalisée, légère et élégante de **Webtop** (Ubuntu XFCE) par [LinuxServer.io](https://fleet.linuxserver.io/image?name=linuxserver/webtop), transformée en un bureau moderne accessible via navigateur avec une interface inspirée de **Windows 11**, une authentification fluide avec écran de verrouillage, une boutique d'applications graphique, un gestionnaire des tâches avancé et un environnement Wine optimisé.

![Bureau Windows 11](docs/screenshots/03-desktop.png)

---

## 📸 Aperçu de l'interface

### 🔒 Écran de verrouillage & Connexion
| Écran de verrouillage | Connexion |
| :---: | :---: |
| ![Lockscreen](docs/screenshots/01-lockscreen.png) | ![Login](docs/screenshots/02-login.png) |

### 🪟 Menu Démarrer & 📁 Gestionnaire de fichiers
| Menu Démarrer | Gestionnaire de fichiers |
| :---: | :---: |
| ![Menu Démarrer](docs/screenshots/04-start-menu.png) | ![Fichiers](docs/screenshots/07-file-manager.png) |

---

## 🚀 Fonctionnalités principales

- **🪟 Interface style Windows 11** avec barre des tâches centrée et menu Démarrer catégorisé
- **🔒 Sécurité robuste** : authentification Python + Nginx, anti-brute-force, sessions HMAC-SHA256
- **🌐 Accès direct par IP** sur les ports 80/443 sans nom de domaine
- **🛍️ Microsoft Store intégré** avec plus de 79 000 paquets APT
- **📊 Gestionnaire des tâches** style Windows avec CPU, RAM, Disque et Réseau en temps réel
- **🍷 Wine optimisé** pour exécuter des fichiers `.exe` Windows
- **🌐 Système multilingue** : 🇧🇷 PT · 🇺🇸 EN · 🇪🇸 ES · 🇩🇪 DE · 🇫🇷 FR · 🇮🇹 IT

---

## 📋 Prérequis

- Docker (version 20.10+)
- Docker Compose (v2+)

---

## 🛠️ Démarrage

### ⚡ Option 1 – Installation automatique avec SSL (RECOMMANDÉE)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
chmod +x setup.sh && sudo ./setup.sh
```

Le script fait **automatiquement** :
1. 🔍 Détecte l'IP publique du VPS
2. 🌐 Crée le domaine `<VOTRE_IP>.sslip.io` (sans nom de domaine)
3. 🔒 Émet un certificat **Let's Encrypt** réel (cadenas vert)
4. 🐳 Lance le conteneur Docker avec HTTPS configuré
5. 🎉 Affiche l'URL d'accès uniquement quand le système est **100% prêt**

> **Note :** Les ports **80** et **443** doivent être ouverts dans le pare-feu de votre hébergeur (Azure NSG / AWS Security Group / Hetzner).

---

### 🐳 Option 2 – Zero-Touch (`docker compose up -d`)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
docker compose up -d
```

---

### ⚙️ Option 3 – Configuration manuelle

```bash
cp .env.example .env
# Éditez .env avec vos identifiants
docker compose up -d
```

---

## 🌐 Accès

- **Avec SSL :** `https://<VOTRE_IP>.sslip.io` — cadenas vert ✅
- **HTTP :** `http://IP-DE-VOTRE-VPS`

---

## 🌍 Système multilingue

Au **premier démarrage**, un assistant de langue s'ouvre automatiquement :

| Drapeau | Langue |
|:---:|---|
| 🇧🇷 | Português (Brasil) |
| 🇺🇸 | English (United States) |
| 🇪🇸 | Español |
| 🇩🇪 | Deutsch |
| 🇫🇷 | Français |
| 🇮🇹 | Italiano |

La préférence est appliquée automatiquement à toute la session et aux applications du bureau.

---

## ⌨️ Raccourcis utiles

- **Verrouiller l'écran :** `Ctrl + Alt + L`
- **Gestionnaire des tâches :** `Ctrl + Shift + Échap`
- **Boutique d'applications :** raccourci dans la barre des tâches

---

## 📄 Licence

Ce projet est sous licence MIT — voir le fichier [LICENSE](LICENSE).
