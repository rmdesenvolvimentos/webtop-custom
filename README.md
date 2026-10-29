# Webtop Custom (Windows 11 Style Cloud Desktop)

Uma versão customizada, leve e elegante do **Webtop** (Ubuntu XFCE) da [LinuxServer.io](https://fleet.linuxserver.io/image?name=linuxserver/webtop), transformada em um desktop moderno acessível via navegador com interface inspirada no **Windows 11**, autenticação com tela de bloqueio fluida, loja de aplicativos gráfica, gerenciador de tarefas avançado e ambiente Wine otimizado.

---

## 🚀 Principais Funcionalidades

- **🪟 Interface Estilo Windows 11**:
  - Barra de tarefas centralizada (Docklike) e menu Iniciar categorizado (Whisker Menu).
  - Papel de parede oficial do Windows 11 e tema escuro moderno.
- **🔒 Tela de Bloqueio & Autenticação Customizada**:
  - Login estilo Windows 11 com fundo em blur acrílico, relógio em tempo real e avatar do usuário.
  - Servidor de autenticação leve em Python integrado ao s6-overlay (`auth_server.py`).
  - Bloqueio manual por atalho (`Ctrl + Alt + L`) ou pelo botão Iniciar.
  - Bloqueio automático por inatividade configurável.
  - Painel gráfico de preferências de usuário e senha (`account-settings-gui`).
- **🛍️ Microsoft Store Integrada (`win-store`)**:
  - Interface gráfica amigável desenvolvida em Python/GTK3 para instalar, atualizar e remover softwares (VS Code, navegadores, utilitários, pacotes APT).
- **📊 Gerenciador de Tarefas no Estilo Windows (`win_taskmgr`)**:
  - Monitor em tempo real de uso de CPU, Memória RAM, Disco e Rede.
  - Árvore de processos com encerramento forçado e prioridades.
- **🍷 Suporte Otimizado a Wine**:
  - Launcher silencioso (`win-launcher`) pré-configurado com Esync/Fsync, ajuste de ptrace e dispositivo de áudio ALSA dummy para rodar executáveis Windows (`.exe`) sem travamentos ou dependências desnecessárias.
- **⚡ Alta Performance e Baixo Consumo**:
  - Serviços desnecessários desativados na inicialização (PulseAudio dummy, CUPS, AT-SPI, UDisks2).
  - Consumo mínimo de CPU e RAM em repouso.

---

## 📋 Pré-requisitos

- Docker instalado (versão 20.10+)
- Docker Compose (v2+)

---

## 🛠️ Como Iniciar

### 1. Clonar o repositório
```bash
git clone https://github.com/rmdesenvolvimentos/webtop-custom.git
cd webtop-custom
```

### 2. Configurar as variáveis de ambiente
Copie o arquivo de exemplo `.env.example` para `.env`:
```bash
cp .env.example .env
```

Edite o arquivo `.env` para definir suas credenciais e preferências:
```ini
# Usuário e Senha de Acesso
CUSTOM_USER=Admin
PASSWORD=SuaSenhaForteAqui123!

# Portas de Acesso
PORT_HTTP=3000
PORT_HTTPS=3001

# Fuso Horário e Idioma
TZ=America/Sao_Paulo
LANG=pt_BR.UTF-8
LANGUAGE=pt_BR:pt
LC_ALL=pt_BR.UTF-8

# Hostname e Título
HOSTNAME=cloud-vps
TITLE=Cloud Desktop
```

### 3. Subir o container
```bash
docker compose up -d
```

O container irá baixar a imagem base e, no primeiro boot, aplicar todas as configurações, scripts e utilitários de forma 100% automática.

---

## 🌐 Como Acessar

Abra o seu navegador web e acesse:
- **HTTP:** `http://localhost:3000` (ou IP da sua VPS/servidor)
- **HTTPS:** `https://localhost:3001`

Para destravar e entrar na área de trabalho, informe a senha configurada no arquivo `.env`.

---

## 📁 Estrutura do Repositório

```text
webtop-custom/
├── .env.example              # Exemplo de configuração de variáveis de ambiente
├── .gitignore                # Regras de exclusão do Git (ignora dados, caches e credenciais)
├── LICENSE                   # Licença MIT
├── README.md                 # Documentação do projeto
├── docker-compose.yml        # Definição do serviço Docker
├── custom-cont-init.d/       # Scripts de inicialização executados pelo s6-overlay
│   ├── 00-first-boot.sh      # Inicializa o volume persistente no primeiro boot
│   ├── 00-hostname.sh        # Configura hostname e resolução local
│   ├── 01-optimize.sh        # Otimiza o sistema desativando serviços pesados
│   ├── 10-install-apps.sh    # Instala utilitários essenciais (VS Code, Docklike, etc.)
│   ├── 20-auth-setup.sh      # Ativa tela de login, atalhos e daemon de autenticação
│   └── 30-wine-setup.sh      # Ajustes de desempenho para execução de programas Windows
└── config-template/          # Arquivos de modelo clonados para o volume do usuário
    ├── account_settings_gui.py
    ├── auth_server.py
    ├── lock_manager.js
    ├── login_assets/
    │   ├── login.html
    │   └── wallpaper.jpg
    ├── nginx-default.conf
    ├── selkies-index.html
    ├── store-64.png
    ├── win-store.py
    └── win_taskmgr.py
```

---

## ⌨️ Atalhos Úteis

- **Bloquear tela:** `Ctrl + Alt + L`
- **Gerenciador de Tarefas:** `Ctrl + Shift + Esc` (ou atalho no menu Iniciar)
- **Loja de Aplicativos:** Atalho na barra de tarefas ou menu Iniciar

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - consulte o arquivo [LICENSE](LICENSE) para obter mais detalhes.
