# Webtop Custom (Escritorio en la Nube estilo Windows 11)

🌐 **Idioma / Language:**
[🇧🇷 Português](README.md) &nbsp;|&nbsp;
[🇺🇸 English](README.en.md) &nbsp;|&nbsp;
🇪🇸 Español (actual) &nbsp;|&nbsp;
[🇩🇪 Deutsch](README.de.md) &nbsp;|&nbsp;
[🇫🇷 Français](README.fr.md) &nbsp;|&nbsp;
[🇮🇹 Italiano](README.it.md)

---

Una versión personalizada, ligera y elegante de **Webtop** (Ubuntu XFCE) de [LinuxServer.io](https://fleet.linuxserver.io/image?name=linuxserver/webtop), transformada en un escritorio moderno accesible desde el navegador con interfaz inspirada en **Windows 11**, autenticación con pantalla de bloqueo fluida, tienda de aplicaciones gráfica, administrador de tareas avanzado y entorno Wine optimizado.

![Escritorio Windows 11](docs/screenshots/03-desktop.png)

---

## 📸 Vista previa de la interfaz

### 🔒 Pantalla de bloqueo e inicio de sesión
| Pantalla de bloqueo | Inicio de sesión |
| :---: | :---: |
| ![Lockscreen](docs/screenshots/01-lockscreen.png) | ![Login](docs/screenshots/02-login.png) |

### 🪟 Menú Inicio & 📁 Administrador de archivos
| Menú Inicio | Administrador de archivos |
| :---: | :---: |
| ![Menú Inicio](docs/screenshots/04-start-menu.png) | ![Archivos](docs/screenshots/07-file-manager.png) |

---

## 🚀 Características principales

- **🪟 Interfaz estilo Windows 11** con barra de tareas centralizada y menú Inicio categorizado
- **🔒 Seguridad robusta**: autenticación Python + Nginx, anti-fuerza bruta, sesiones HMAC-SHA256
- **🌐 Acceso directo por IP** en puertos 80/443 sin necesidad de dominio propio
- **🛍️ Microsoft Store integrada** con 79.000+ paquetes APT
- **📊 Administrador de tareas** estilo Windows con CPU, RAM, Disco y Red en tiempo real
- **🍷 Wine optimizado** para ejecutar aplicativos `.exe` de Windows
- **🌐 Sistema multilingüe**: 🇧🇷 PT · 🇺🇸 EN · 🇪🇸 ES · 🇩🇪 DE · 🇫🇷 FR · 🇮🇹 IT

---

## 📋 Requisitos

- Docker (versión 20.10+)
- Docker Compose (v2+)

---

## 🛠️ Cómo empezar

### ⚡ Opción 1 – Instalación automática con SSL (RECOMENDADO)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
chmod +x setup.sh && sudo ./setup.sh
```

El script hace **automáticamente**:
1. 🔍 Detecta la IP pública de la VPS
2. 🌐 Crea el dominio `<TU_IP>.sslip.io` (sin necesidad de dominio propio)
3. 🔒 Emite un certificado **Let's Encrypt** real (candado verde)
4. 🐳 Inicia el contenedor Docker con HTTPS configurado
5. 🎉 Muestra la URL de acceso cuando el sistema está **100% listo**

> **Nota:** Los puertos **80** y **443** deben estar abiertos en el firewall de tu proveedor (Azure NSG / AWS Security Group / Hetzner).

---

### 🐳 Opción 2 – Zero-Touch (`docker compose up -d`)

```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
docker compose up -d
```

---

### ⚙️ Opción 3 – Configuración manual

```bash
cp .env.example .env
# Edita .env con tus credenciales
docker compose up -d
```

---

## 🌐 Cómo acceder

- **Con SSL:** `https://<TU_IP>.sslip.io` — candado verde ✅
- **HTTP:** `http://IP-DE-TU-VPS`

---

## 🌍 Sistema multilingüe

En el **primer inicio de sesión**, aparece automáticamente un asistente de idioma que permite elegir entre:

| Bandera | Idioma |
|:---:|---|
| 🇧🇷 | Português (Brasil) |
| 🇺🇸 | English (United States) |
| 🇪🇸 | Español |
| 🇩🇪 | Deutsch |
| 🇫🇷 | Français |
| 🇮🇹 | Italiano |

La preferencia se aplica automáticamente a toda la sesión y a las aplicaciones del escritorio.

---

## ⌨️ Atajos útiles

- **Bloquear pantalla:** `Ctrl + Alt + L`
- **Administrador de tareas:** `Ctrl + Shift + Esc`
- **Tienda de aplicaciones:** acceso directo en la barra de tareas

---

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT — consulta el archivo [LICENSE](LICENSE).
