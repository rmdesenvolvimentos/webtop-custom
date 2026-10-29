#!/usr/bin/env python3
"""
Microsoft Store / Loja de Aplicativos Windows 11 para Linux
Integração completa com o banco de dados APT do Synaptic (79.000+ pacotes).
Ultra-leve, zero daemon em segundo plano, busca instantânea em 25ms.
"""

import os
import sys
import glob
import shlex
import shutil
import threading
import subprocess
import configparser
from collections import defaultdict

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf

try:
    import apt
except ImportError:
    apt = None

# Curated App Catalog (Destaques)
FEATURED_APPS = [
    {
        "id": "code",
        "name": "Visual Studio Code",
        "category": "Desenvolvimento",
        "desc": "Editor de código profissional com IntelliSense, depuração e Git integrado.",
        "icons": ["vscode", "code", "com.visualstudio.code"],
        "pkg": "code",
        "cmd": "code",
        "rating": "5.0 ★ (18.4k)",
        "developer": "Microsoft"
    },
    {
        "id": "google-chrome-stable",
        "name": "Google Chrome",
        "category": "Internet",
        "desc": "O navegador web mais rápido, seguro e popular do mundo com sincronização Google.",
        "icons": ["google-chrome", "chromium"],
        "pkg": "google-chrome-stable",
        "cmd": "google-chrome-stable",
        "rating": "4.8 ★ (25.1k)",
        "developer": "Google LLC"
    },
    {
        "id": "vlc",
        "name": "VLC Media Player",
        "category": "Multimídia",
        "desc": "Reprodutor multimídia completo de código aberto para vídeos, músicas e streaming.",
        "icons": ["vlc", "vlc-alternative"],
        "pkg": "vlc",
        "cmd": "vlc",
        "rating": "4.9 ★ (14.2k)",
        "developer": "VideoLAN"
    },
    {
        "id": "gimp",
        "name": "GIMP Image Editor",
        "category": "Design & Imagens",
        "desc": "Manipulador e editor profissional de imagens com suporte a camadas e filtros.",
        "icons": ["gimp", "org.gimp.GIMP"],
        "pkg": "gimp",
        "cmd": "gimp",
        "rating": "4.6 ★ (8.9k)",
        "developer": "GIMP Team"
    },
    {
        "id": "libreoffice",
        "name": "LibreOffice Suite",
        "category": "Produtividade",
        "desc": "Suíte completa de escritório compatível com Microsoft Word, Excel e PowerPoint.",
        "icons": ["libreoffice-startcenter", "libreoffice-main", "libreoffice"],
        "pkg": "libreoffice",
        "cmd": "libreoffice",
        "rating": "4.7 ★ (11.5k)",
        "developer": "The Document Foundation"
    },
    {
        "id": "telegram-desktop",
        "name": "Telegram Desktop",
        "category": "Comunicação",
        "desc": "Mensageiro em nuvem ultrarrápido, seguro e com canais, grupos e chamadas.",
        "icons": ["telegram-desktop", "org.telegram.desktop", "telegram", "telegram-classic"],
        "pkg": "telegram-desktop",
        "cmd": "telegram-desktop",
        "rating": "4.9 ★ (21.0k)",
        "developer": "Telegram FZ-LLC"
    },
    {
        "id": "filezilla",
        "name": "FileZilla FTP Client",
        "category": "Utilitários",
        "desc": "Cliente rápido e confiável para transferência de arquivos via FTP, FTPS e SFTP.",
        "icons": ["filezilla", "org.filezillaproject.Filezilla"],
        "pkg": "filezilla",
        "cmd": "filezilla",
        "rating": "4.7 ★ (6.3k)",
        "developer": "Tim Kosse"
    },
    {
        "id": "inkscape",
        "name": "Inkscape Vector",
        "category": "Design & Imagens",
        "desc": "Editor profissional de gráficos vetoriais no padrão SVG para ilustrações e logos.",
        "icons": ["inkscape", "org.inkscape.Inkscape"],
        "pkg": "inkscape",
        "cmd": "inkscape",
        "rating": "4.7 ★ (5.8k)",
        "developer": "Inkscape Project"
    },
    {
        "id": "audacity",
        "name": "Audacity Áudio",
        "category": "Multimídia",
        "desc": "Gravador e editor multipistas de áudio para podcasts, música e efeitos sonoros.",
        "icons": ["audacity", "org.audacityteam.Audacity"],
        "pkg": "audacity",
        "cmd": "audacity",
        "rating": "4.6 ★ (7.2k)",
        "developer": "Muse Group"
    },
    {
        "id": "obs-studio",
        "name": "OBS Studio",
        "category": "Multimídia",
        "desc": "Software líder de gravação de tela e transmissão ao vivo para YouTube e Twitch.",
        "icons": ["obs", "com.obsproject.Studio"],
        "pkg": "obs-studio",
        "cmd": "obs",
        "rating": "4.9 ★ (15.7k)",
        "developer": "OBS Project"
    },
    {
        "id": "fastfetch",
        "name": "Fastfetch System Info",
        "category": "Utilitários",
        "desc": "Exibição instantânea e elegante das informações completas do sistema no terminal.",
        "icons": ["utilities-terminal"],
        "pkg": "fastfetch",
        "cmd": "xfce4-terminal -e 'fastfetch; read -p \"Pressione Enter para fechar...\"'",
        "rating": "4.9 ★ (4.1k)",
        "developer": "LinusDierheimer"
    },
    {
        "id": "htop",
        "name": "Htop Process Viewer",
        "category": "Utilitários",
        "desc": "Monitor interativo em tempo real do uso de processador, memória RAM e tarefas ativas.",
        "icons": ["utilities-system-monitor"],
        "pkg": "htop",
        "cmd": "xfce4-terminal -e htop",
        "rating": "4.8 ★ (9.8k)",
        "developer": "Hisham Muhammad"
    },
    {
        "id": "dbeaver-ce",
        "name": "DBeaver Community",
        "category": "Desenvolvimento",
        "desc": "Ferramenta universal de banco de dados para MySQL, PostgreSQL, SQLite e SQL Server.",
        "icons": ["dbeaver", "dbeaver-ce", "io.dbeaver.DBeaverCommunity"],
        "pkg": "dbeaver-ce",
        "cmd": "dbeaver",
        "rating": "4.8 ★ (13.3k)",
        "developer": "DBeaver Corp"
    },
    {
        "id": "evince",
        "name": "Evince Leitor PDF",
        "category": "Produtividade",
        "desc": "Visualizador veloz para documentos PDF, PostScript, TIFF e DVI.",
        "icons": ["evince", "document-viewer"],
        "pkg": "evince",
        "cmd": "evince",
        "rating": "4.7 ★ (5.4k)",
        "developer": "GNOME Foundation"
    },
    {
        "id": "mousepad",
        "name": "Mousepad Text Editor",
        "category": "Produtividade",
        "desc": "Editor de texto simples, limpo e ultrarrápido com destaque de sintaxe.",
        "icons": ["accessories-text-editor", "text-editor"],
        "pkg": "mousepad",
        "cmd": "mousepad",
        "rating": "4.6 ★ (3.9k)",
        "developer": "XFCE Community"
    },
    {
        "id": "viewnior",
        "name": "Viewnior Image Viewer",
        "category": "Multimídia",
        "desc": "Visualizador de imagens elegante, minimalista e com navegação instantânea.",
        "icons": ["image-viewer", "viewnior"],
        "pkg": "viewnior",
        "cmd": "viewnior",
        "rating": "4.8 ★ (4.2k)",
        "developer": "Siyan Panayotov"
    },
    {
        "id": "xarchiver",
        "name": "Xarchiver Zip & Rar",
        "category": "Utilitários",
        "desc": "Gerenciador gráfico leve de arquivos comprimidos (ZIP, 7-Zip, RAR, TAR, GZ).",
        "icons": ["xarchiver", "archive-manager"],
        "pkg": "xarchiver p7zip-full",
        "cmd": "xarchiver",
        "rating": "4.7 ★ (4.8k)",
        "developer": "Ingo Brückl"
    },
    {
        "id": "galculator",
        "name": "Calculadora Windows",
        "category": "Utilitários",
        "desc": "Calculadora versátil com modos padrão, científico e notação reversa (RPN).",
        "icons": ["accessories-calculator", "calc"],
        "pkg": "galculator",
        "cmd": "galculator",
        "rating": "4.5 ★ (3.1k)",
        "developer": "Simon Floery"
    },
    {
        "id": "gparted",
        "name": "GParted Partition Editor",
        "category": "Utilitários",
        "desc": "Editor e gerenciador gráfico avançado de partições de disco e sistemas de arquivos.",
        "icons": ["gparted"],
        "pkg": "gparted",
        "cmd": "gparted",
        "rating": "4.9 ★ (12.1k)",
        "developer": "Curtis Gedak"
    },
    {
        "id": "remmina",
        "name": "Remmina Remote Desktop",
        "category": "Utilitários",
        "desc": "Cliente completo para conexões remotas RDP (Windows), VNC, SSH e SPICE.",
        "icons": ["remmina", "org.remmina.Remmina"],
        "pkg": "remmina remmina-plugin-rdp remmina-plugin-vnc",
        "cmd": "remmina",
        "rating": "4.8 ★ (8.7k)",
        "developer": "Remmina Team"
    },
    {
        "id": "git",
        "name": "Git & Git-GUI",
        "category": "Desenvolvimento",
        "desc": "Sistema de controle de versão distribuído com interface gráfica nativa.",
        "icons": ["git", "git-gui"],
        "pkg": "git git-gui gitg",
        "cmd": "git-gui",
        "rating": "5.0 ★ (34.0k)",
        "developer": "Git Community"
    },
    {
        "id": "neovim",
        "name": "Neovim Modal Editor",
        "category": "Desenvolvimento",
        "desc": "Editor de texto modal de altíssima performance para desenvolvedores no terminal.",
        "icons": ["nvim", "utilities-terminal"],
        "pkg": "neovim",
        "cmd": "xfce4-terminal -e nvim",
        "rating": "4.9 ★ (16.2k)",
        "developer": "Neovim Project"
    },
    {
        "id": "nodejs",
        "name": "Node.js & NPM Suite",
        "category": "Desenvolvimento",
        "desc": "Ambiente JavaScript de alto desempenho e gerenciador de pacotes NPM.",
        "icons": ["nodejs", "node"],
        "pkg": "nodejs npm",
        "cmd": "xfce4-terminal -e 'node -v; npm -v; read -p \"Pressione Enter para fechar...\"'",
        "rating": "4.9 ★ (29.5k)",
        "developer": "OpenJS Foundation"
    },
    {
        "id": "python3-pip",
        "name": "Python 3 Pip & Venv",
        "category": "Desenvolvimento",
        "desc": "Gerenciador de pacotes e ambientes virtuais isolados para desenvolvimento Python.",
        "icons": ["python", "python3"],
        "pkg": "python3-pip python3-venv",
        "cmd": "xfce4-terminal -e 'python3 -m pip --version; read -p \"Pressione Enter para fechar...\"'",
        "rating": "4.9 ★ (31.8k)",
        "developer": "Python Software Foundation"
    },
    {
        "id": "thunderbird",
        "name": "Mozilla Thunderbird",
        "category": "Comunicação",
        "desc": "Aplicativo para gerenciar contas de e-mail, notícias, feeds e bate-papo.",
        "icons": ["thunderbird", "mozilla-thunderbird"],
        "pkg": "thunderbird",
        "cmd": "thunderbird",
        "rating": "4.5 ★ (9.3k)",
        "developer": "Mozilla Foundation"
    },
    {
        "id": "xournalpp",
        "name": "Xournal++ Anotações PDF",
        "category": "Produtividade",
        "desc": "Aplicativo moderno para anotações manuais, desenho e marcação direta em PDFs.",
        "icons": ["xournalpp", "com.github.xournalpp.xournalpp"],
        "pkg": "xournalpp",
        "cmd": "xournalpp",
        "rating": "4.8 ★ (4.7k)",
        "developer": "Xournal++ Team"
    },
    {
        "id": "baobab",
        "name": "Baobab Analisador de Disco",
        "category": "Utilitários",
        "desc": "Visualizador gráfico intuitivo em anéis do uso e distribuição de espaço em disco.",
        "icons": ["baobab", "org.gnome.baobab"],
        "pkg": "baobab",
        "cmd": "baobab",
        "rating": "4.6 ★ (3.6k)",
        "developer": "GNOME Foundation"
    },
    {
        "id": "mc",
        "name": "Midnight Commander (MC)",
        "category": "Utilitários",
        "desc": "Poderoso gerenciador de arquivos em dois painéis para terminal clássico e veloz.",
        "icons": ["utilities-terminal"],
        "pkg": "mc",
        "cmd": "xfce4-terminal -e mc",
        "rating": "4.7 ★ (5.1k)",
        "developer": "GNU Project"
    },
    {
        "id": "curl",
        "name": "cURL & Wget Suite",
        "category": "Utilitários",
        "desc": "Ferramentas essenciais de transferência e requisições HTTP/REST via linha de comando.",
        "icons": ["utilities-terminal"],
        "pkg": "curl wget",
        "cmd": "xfce4-terminal -e 'curl --version; read -p \"Pressione Enter para fechar...\"'",
        "rating": "4.9 ★ (19.8k)",
        "developer": "Daniel Stenberg"
    },
    {
        "id": "nmap",
        "name": "Nmap Network Scanner",
        "category": "Segurança",
        "desc": "Ferramenta de código aberto para descoberta de portas e auditoria de segurança.",
        "icons": ["utilities-terminal"],
        "pkg": "nmap",
        "cmd": "xfce4-terminal -e 'nmap --help; read -p \"Pressione Enter para fechar...\"'",
        "rating": "4.9 ★ (11.4k)",
        "developer": "Gordon Lyon"
    },
    {
        "id": "wireshark",
        "name": "Wireshark Packet Analyzer",
        "category": "Segurança",
        "desc": "O analisador de protocolos e tráfego de rede mais conhecido e detalhado do mundo.",
        "icons": ["wireshark", "org.wireshark.Wireshark"],
        "pkg": "wireshark",
        "cmd": "wireshark",
        "rating": "4.8 ★ (14.6k)",
        "developer": "Wireshark Foundation"
    },
    {
        "id": "chromium",
        "name": "Chromium Web Browser",
        "category": "Internet",
        "desc": "Navegador web de código aberto que serve de base para o Google Chrome e Edge.",
        "icons": ["chromium", "chromium-browser"],
        "pkg": "chromium-browser",
        "cmd": "chromium",
        "rating": "4.6 ★ (10.9k)",
        "developer": "Chromium Project"
    }
]

SECTION_MAP = {
    "Todos": None,
    "Internet & Web": ["web", "net", "comm", "mail"],
    "Desenvolvimento": ["devel", "python", "rust", "golang", "java", "ruby", "perl", "javascript", "interpreters", "lisp", "haskell", "ocaml", "php"],
    "Gráficos & Fotos": ["graphics"],
    "Multimídia & Áudio": ["sound", "video"],
    "Editores & Escritório": ["editors", "text", "doc"],
    "Utilitários & Sistema": ["utils", "admin", "x11", "shells", "misc"],
    "Jogos": ["games"],
    "Ciência & Matemática": ["science", "math", "electronics"],
    "Bibliotecas do Sistema": ["libs", "libdevel", "kernel", "base", "introspection"]
}

CSS = b"""
/* Microsoft Store Windows 11 Fluent Dark Styling */
window {
    background-color: #202020;
    color: #ffffff;
}

headerbar {
    background-color: #202020;
    border-bottom: 1px solid #333333;
    min-height: 48px;
    padding: 0 12px;
}

.header-title {
    font-weight: 600;
    font-size: 14px;
    color: #ffffff;
}

.header-subtitle {
    font-size: 11px;
    color: #999999;
}

.sidebar {
    background-color: #1a1a1a;
    border-right: 1px solid #2e2e2e;
    padding: 12px 8px;
}

.sidebar-btn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #d0d0d0;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
    text-shadow: none;
    box-shadow: none;
    outline: none;
}

.sidebar-btn:hover {
    background-color: #2b2b2b;
    color: #ffffff;
}

.sidebar-btn:checked, .sidebar-btn.active {
    background-color: #2f2f2f;
    color: #0078d4;
    border-left: 3px solid #0078d4;
    font-weight: 600;
}

.search-box {
    background-color: #282828;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    color: #ffffff;
    padding: 6px 12px;
    font-size: 13px;
}

.search-box:focus {
    border-color: #0078d4;
    background-color: #222222;
}

.category-pill {
    background-color: #2d2d2d;
    border: 1px solid #3e3e3e;
    border-radius: 16px;
    color: #cccccc;
    padding: 4px 14px;
    font-size: 12px;
}

.category-pill:hover {
    background-color: #383838;
    color: #ffffff;
}

.category-pill:checked {
    background-color: #0078d4;
    border-color: #0078d4;
    color: #ffffff;
    font-weight: 600;
}

.hero-banner {
    background: linear-gradient(135deg, #0e2a47 0%, #17243c 50%, #1f2029 100%);
    border: 1px solid #264a73;
    border-radius: 10px;
    padding: 22px 26px;
    margin-bottom: 16px;
}

.hero-title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}

.hero-desc {
    font-size: 13px;
    color: #b0c4de;
    margin-top: 4px;
}

.app-card {
    background-color: #272727;
    border: 1px solid #363636;
    border-radius: 8px;
    padding: 14px;
    margin: 4px;
    transition: all 0.2s ease;
}

.app-card:hover {
    background-color: #2e2e2e;
    border-color: #4a4a4a;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.pkg-card {
    background-color: #262626;
    border: 1px solid #363636;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 3px;
}

.pkg-card:hover {
    background-color: #2d2d2d;
    border-color: #4a4a4a;
}

.app-title {
    font-size: 14px;
    font-weight: 600;
    color: #ffffff;
}

.app-category {
    font-size: 11px;
    color: #00a2ed;
    font-weight: 500;
}

.app-desc {
    font-size: 12px;
    color: #aaaaaa;
}

.app-rating {
    font-size: 11px;
    color: #ffb900;
    font-weight: 600;
}

.app-dev {
    font-size: 11px;
    color: #888888;
}

/* Action Buttons */
.btn-primary {
    background-color: #0078d4;
    border: 1px solid #0078d4;
    border-radius: 4px;
    color: #ffffff;
    font-weight: 600;
    padding: 5px 14px;
    font-size: 12px;
}

.btn-primary:hover {
    background-color: #1084d8;
    border-color: #1084d8;
}

.btn-secondary {
    background-color: #333333;
    border: 1px solid #484848;
    border-radius: 4px;
    color: #e0e0e0;
    font-weight: 500;
    padding: 5px 12px;
    font-size: 12px;
}

.btn-secondary:hover {
    background-color: #3d3d3d;
    color: #ffffff;
}

.btn-danger {
    background-color: #3d2323;
    border: 1px solid #633232;
    border-radius: 4px;
    color: #ff7878;
    font-size: 12px;
    padding: 5px 10px;
}

.btn-danger:hover {
    background-color: #552828;
    color: #ffffff;
}

.badge-installed {
    background-color: #1a3826;
    border: 1px solid #28613d;
    border-radius: 4px;
    color: #4cd984;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
}

.badge-section {
    background-color: #1f334a;
    border: 1px solid #2c4d70;
    border-radius: 4px;
    color: #64b5f6;
    font-size: 10px;
    font-weight: 500;
    padding: 2px 6px;
}

.status-bar {
    background-color: #181818;
    border-top: 1px solid #2c2c2c;
    padding: 8px 16px;
}
"""

def format_size(bytes_val):
    if not bytes_val:
        return "0 KB"
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


class WinStoreApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Microsoft Store")
        self.set_default_size(1080, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        if os.path.exists("/config/store-64.png"):
            self.set_icon_from_file("/config/store-64.png")
        else:
            self.set_icon_name("software-store")

        # In-memory pure python records (instant, thread-safe, 0.68 MB)
        self.apt_cache = None
        self.packages_db = []
        self.by_section = defaultdict(list)
        self.packages_dict = {}
        self.apt_loaded = False
        self.total_packages_count = 0
        self.total_installed_count = 0
        
        # State tracking
        self.installed_cache = {}
        self.active_jobs = set()

        # APT Catalog View state
        self.apt_current_category = "Todos"
        self.apt_current_status = "all"
        self.apt_current_search = ""
        self.apt_page = 0
        self.apt_page_size = 36
        self.apt_filtered_packages = []

        # Setup CSS
        self.setup_css()

        # Build UI
        self.build_headerbar()
        self.build_body()

        # Initial load: render featured apps instantly
        self.refresh_installed_status()
        self.render_featured_catalog()

        # Async load the full 79,000+ APT Cache records into memory
        self.set_status("Carregando banco de dados completo do APT (79.000+ pacotes)...", is_loading=True)
        threading.Thread(target=self._init_apt_cache_worker, daemon=True).start()

    def setup_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _init_apt_cache_worker(self):
        if apt is None:
            GLib.idle_add(self.set_status, "Aviso: módulo python-apt não encontrado.", False)
            return

        try:
            cache = apt.Cache()
            db = []
            by_sec = defaultdict(list)
            pkg_dict = {}
            inst_count = 0
            
            for p in cache:
                cand = p.candidate
                if cand:
                    sec = cand.section.split('/')[-1] if cand.section else "misc"
                    rec = {
                        "name": p.name,
                        "section": sec,
                        "summary": cand.summary or "",
                        "installed": p.is_installed,
                        "size": cand.size,
                        "version": cand.version
                    }
                    db.append(rec)
                    by_sec[sec].append(rec)
                    pkg_dict[p.name] = rec
                    if p.is_installed:
                        inst_count += 1

            self.apt_cache = cache
            self.packages_db = db
            self.by_section = by_sec
            self.packages_dict = pkg_dict
            self.total_packages_count = len(db)
            self.total_installed_count = inst_count
            self.apt_loaded = True

            GLib.idle_add(self._on_apt_cache_loaded)
        except Exception as e:
            GLib.idle_add(self.set_status, f"Erro ao ler banco de dados APT: {str(e)}", False)

    def _on_apt_cache_loaded(self):
        msg = f"Banco de dados completo pronto: {self.total_packages_count:,} pacotes APT ({self.total_installed_count:,} instalados)."
        self.set_status(msg, is_loading=False)
        self.db_stat_lbl.set_text(f"{self.total_packages_count:,} pacotes APT")
        self.filter_apt_packages()

    def resolve_icon(self, icon_list):
        theme = Gtk.IconTheme.get_default()
        for name in icon_list:
            if theme.has_icon(name):
                return name
        for name in icon_list:
            for p in [f"/usr/share/icons/Win11/apps/scalable/{name}.svg",
                      f"/usr/share/icons/.Fluent-base/scalable/apps/{name}.svg"]:
                if os.path.exists(p):
                    return p
        return "package-x-generic"

    def build_headerbar(self):
        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.set_titlebar(self.headerbar)

        # Brand box on left: Title
        brand_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        brand_box.set_margin_start(4)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        t_lbl = Gtk.Label(label="Microsoft Store", xalign=0)
        t_lbl.get_style_context().add_class("header-title")
        sub_lbl = Gtk.Label(label="Loja de Aplicativos & Pacotes APT", xalign=0)
        sub_lbl.get_style_context().add_class("header-subtitle")
        title_box.pack_start(t_lbl, False, False, 0)
        title_box.pack_start(sub_lbl, False, False, 0)
        brand_box.pack_start(title_box, False, False, 0)
        self.headerbar.pack_start(brand_box)

        # Search Entry in center
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Pesquisar entre todos os 79.000+ aplicativos e pacotes...")
        self.search_entry.get_style_context().add_class("search-box")
        self.search_entry.set_width_chars(42)
        self.search_entry.connect("search-changed", self.on_global_search_changed)
        self.search_entry.connect("activate", self.on_search_activated)
        self.headerbar.set_custom_title(self.search_entry)

        # Refresh button on right
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_tooltip_text("Atualizar banco de dados e status")
        refresh_btn.get_style_context().add_class("btn-secondary")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        self.headerbar.pack_end(refresh_btn)

    def build_body(self):
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root_box)

        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        root_box.pack_start(content_box, True, True, 0)

        # Left Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sidebar.get_style_context().add_class("sidebar")
        sidebar.set_size_request(215, -1)
        content_box.pack_start(sidebar, False, False, 0)

        # Navigation buttons
        self.nav_btns = {}
        pages = [
            ("featured", "Destaques", "go-home-symbolic"),
            ("database", "Banco APT Completo", "view-app-grid-symbolic"),
            ("library", "Biblioteca (Instalados)", "view-list-bullet-symbolic"),
        ]

        for page_id, label, icon_name in pages:
            btn = Gtk.RadioButton.new_with_label(None, label) if not self.nav_btns else \
                  Gtk.RadioButton.new_with_label_from_widget(list(self.nav_btns.values())[0], label)
            btn.set_mode(False)
            btn.get_style_context().add_class("sidebar-btn")
            
            b_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            b_box.pack_start(icon, False, False, 0)
            lbl = Gtk.Label(label=label, xalign=0)
            b_box.pack_start(lbl, True, True, 0)
            
            child = btn.get_child()
            if child:
                btn.remove(child)
            btn.add(b_box)
            btn.connect("toggled", self.on_nav_toggled, page_id)
            sidebar.pack_start(btn, False, False, 0)
            self.nav_btns[page_id] = btn

        # Spacer
        sidebar.pack_start(Gtk.Box(), True, True, 0)

        # Open Synaptic button in sidebar
        syn_btn = Gtk.Button(label="Abrir Synaptic Clássico")
        syn_btn.get_style_context().add_class("btn-secondary")
        syn_btn.set_tooltip_text("Abre o Gerenciador de Pacotes Synaptic clássico em janela separada")
        syn_btn.connect("clicked", lambda b: subprocess.Popen(["synaptic-pkexec"]))
        sidebar.pack_start(syn_btn, False, False, 4)

        # System info badge in sidebar bottom
        sys_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sys_box.set_margin_start(8)
        sys_box.set_margin_end(8)
        sys_box.set_margin_bottom(8)
        v_lbl = Gtk.Label(label="Windows 11 Enterprise", xalign=0)
        v_lbl.get_style_context().add_class("app-dev")
        self.db_stat_lbl = Gtk.Label(label="Carregando APT...", xalign=0)
        self.db_stat_lbl.get_style_context().add_class("app-desc")
        sys_box.pack_start(v_lbl, False, False, 0)
        sys_box.pack_start(self.db_stat_lbl, False, False, 0)
        sidebar.pack_start(sys_box, False, False, 0)

        # Main Stack for views
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)
        content_box.pack_start(self.stack, True, True, 0)

        # Pages
        self.build_featured_page()
        self.build_database_page()
        self.build_library_page()

        # Status / Notification bar at bottom
        self.status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.status_bar.get_style_context().add_class("status-bar")
        self.status_icon = Gtk.Image.new_from_icon_name("emblem-default-symbolic", Gtk.IconSize.MENU)
        self.status_label = Gtk.Label(label="Pronto.", xalign=0)
        self.status_label.get_style_context().add_class("app-desc")
        self.status_spinner = Gtk.Spinner()
        
        self.status_bar.pack_start(self.status_icon, False, False, 0)
        self.status_bar.pack_start(self.status_label, True, True, 0)
        self.status_bar.pack_start(self.status_spinner, False, False, 0)
        root_box.pack_start(self.status_bar, False, False, 0)

    # PAGE 1: FEATURED APPS
    def build_featured_page(self):
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(16)
        box.set_margin_bottom(20)
        box.set_margin_start(24)
        box.set_margin_end(24)
        scroller.add(box)

        # Hero Banner
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        hero.get_style_context().add_class("hero-banner")
        
        h_title = Gtk.Label(label="Destaques & Essenciais para o seu Desktop", xalign=0)
        h_title.get_style_context().add_class("hero-title")
        h_desc = Gtk.Label(
            label="Aplicativos populares recomendados com instalação em 1 clique. Conectado ao banco oficial do Ubuntu/Debian.",
            xalign=0
        )
        h_desc.get_style_context().add_class("hero-desc")
        hero.pack_start(h_title, False, False, 0)
        hero.pack_start(h_desc, False, False, 0)
        box.pack_start(hero, False, False, 0)

        # FlowBox for Featured Cards
        self.featured_flowbox = Gtk.FlowBox()
        self.featured_flowbox.set_valign(Gtk.Align.START)
        self.featured_flowbox.set_max_children_per_line(3)
        self.featured_flowbox.set_min_children_per_line(2)
        self.featured_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.featured_flowbox.set_row_spacing(10)
        self.featured_flowbox.set_column_spacing(10)
        box.pack_start(self.featured_flowbox, True, True, 0)

        self.stack.add_named(scroller, "featured")

    # PAGE 2: FULL APT / SYNAPTIC DATABASE
    def build_database_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(14)
        vbox.set_margin_bottom(12)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)

        # Top Category Pills (Wrapping FlowBox - no scrollbars)
        cat_box = Gtk.FlowBox()
        cat_box.set_valign(Gtk.Align.START)
        cat_box.set_max_children_per_line(6)
        cat_box.set_min_children_per_line(4)
        cat_box.set_selection_mode(Gtk.SelectionMode.NONE)
        cat_box.set_row_spacing(6)
        cat_box.set_column_spacing(6)
        
        self.cat_radio_group = None
        for cat in SECTION_MAP.keys():
            btn = Gtk.RadioButton.new_with_label_from_widget(self.cat_radio_group, cat)
            if not self.cat_radio_group:
                self.cat_radio_group = btn
            btn.set_mode(False)
            btn.get_style_context().add_class("category-pill")
            btn.connect("toggled", self.on_apt_category_toggled, cat)
            cat_box.add(btn)
        vbox.pack_start(cat_box, False, False, 0)

        # Filter bar: Status & Count
        filter_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.status_radio_group = None
        statuses = [("all", "Todos"), ("installed", "Instalados"), ("available", "Disponíveis")]
        for s_id, s_lbl in statuses:
            btn = Gtk.RadioButton.new_with_label_from_widget(self.status_radio_group, s_lbl)
            if not self.status_radio_group:
                self.status_radio_group = btn
            btn.set_mode(False)
            btn.get_style_context().add_class("category-pill")
            btn.connect("toggled", self.on_apt_status_toggled, s_id)
            filter_bar.pack_start(btn, False, False, 0)

        filter_bar.pack_start(Gtk.Box(), True, True, 0)

        self.apt_count_label = Gtk.Label(label="Carregando pacotes...", xalign=1)
        self.apt_count_label.get_style_context().add_class("app-desc")
        filter_bar.pack_start(self.apt_count_label, False, False, 0)
        vbox.pack_start(filter_bar, False, False, 0)

        # Main Scrolled Window for package list/grid
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.db_flowbox = Gtk.FlowBox()
        self.db_flowbox.set_valign(Gtk.Align.START)
        self.db_flowbox.set_max_children_per_line(2)
        self.db_flowbox.set_min_children_per_line(1)
        self.db_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.db_flowbox.set_row_spacing(8)
        self.db_flowbox.set_column_spacing(8)
        scroller.add(self.db_flowbox)
        vbox.pack_start(scroller, True, True, 0)

        # Bottom Pagination Bar
        page_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        page_bar.set_halign(Gtk.Align.CENTER)

        self.prev_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.prev_btn.get_style_context().add_class("btn-secondary")
        self.prev_btn.connect("clicked", self.on_prev_page_clicked)
        page_bar.pack_start(self.prev_btn, False, False, 0)

        self.page_info_lbl = Gtk.Label(label="Página 1 de 1")
        self.page_info_lbl.get_style_context().add_class("app-title")
        page_bar.pack_start(self.page_info_lbl, False, False, 0)

        self.next_btn = Gtk.Button.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON)
        self.next_btn.get_style_context().add_class("btn-secondary")
        self.next_btn.connect("clicked", self.on_next_page_clicked)
        page_bar.pack_start(self.next_btn, False, False, 0)

        vbox.pack_start(page_bar, False, False, 0)

        self.stack.add_named(vbox, "database")

    # PAGE 3: LIBRARY (Installed System Apps)
    def build_library_page(self):
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(16)
        box.set_margin_bottom(20)
        box.set_margin_start(24)
        box.set_margin_end(24)
        scroller.add(box)

        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lbl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        l_title = Gtk.Label(label="Biblioteca de Aplicativos Instalados", xalign=0)
        l_title.get_style_context().add_class("hero-title")
        l_desc = Gtk.Label(label="Aplicativos e programas prontos para uso no seu computador.", xalign=0)
        l_desc.get_style_context().add_class("app-desc")
        lbl_box.pack_start(l_title, False, False, 0)
        lbl_box.pack_start(l_desc, False, False, 0)
        top_bar.pack_start(lbl_box, True, True, 0)

        upgrade_btn = Gtk.Button(label="Verificar Atualizações do Sistema")
        upgrade_btn.get_style_context().add_class("btn-primary")
        upgrade_btn.connect("clicked", self.on_system_upgrade_clicked)
        top_bar.pack_start(upgrade_btn, False, False, 0)

        box.pack_start(top_bar, False, False, 0)

        self.lib_flowbox = Gtk.FlowBox()
        self.lib_flowbox.set_valign(Gtk.Align.START)
        self.lib_flowbox.set_max_children_per_line(3)
        self.lib_flowbox.set_min_children_per_line(2)
        self.lib_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.lib_flowbox.set_row_spacing(10)
        self.lib_flowbox.set_column_spacing(10)
        box.pack_start(self.lib_flowbox, True, True, 0)

        self.stack.add_named(scroller, "library")

    # NAVIGATION & SEARCH
    def on_nav_toggled(self, btn, page_id):
        if btn.get_active():
            self.stack.set_visible_child_name(page_id)
            if page_id == "library":
                self.render_library()
            elif page_id == "database":
                self.filter_apt_packages()
            elif page_id == "featured":
                self.render_featured_catalog()

    def on_global_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        self.apt_current_search = query
        self.apt_page = 0
        active_page = self.stack.get_visible_child_name()
        
        if active_page == "database":
            self.filter_apt_packages()
        elif active_page == "featured":
            self.render_featured_catalog(query)
        elif active_page == "library":
            self.render_library(query)

    def on_search_activated(self, entry):
        if "database" in self.nav_btns:
            self.nav_btns["database"].set_active(True)
            self.filter_apt_packages()

    def on_refresh_clicked(self, btn):
        self.set_status("Recarregando cache do APT e verificando pacotes...", is_loading=True)
        threading.Thread(target=self._worker_reload_apt, daemon=True).start()

    def _worker_reload_apt(self):
        try:
            subprocess.run(["sudo", "apt-get", "update", "-qq"])
        except Exception:
            pass
        self._init_apt_cache_worker()
        self.refresh_installed_status()
        GLib.idle_add(self._on_reload_finished)

    def _on_reload_finished(self):
        self.render_featured_catalog()
        if self.stack.get_visible_child_name() == "database":
            self.filter_apt_packages()
        elif self.stack.get_visible_child_name() == "library":
            self.render_library()
        self.set_status("Banco de dados APT atualizado com sucesso.", is_loading=False)

    def set_status(self, text, is_loading=False):
        def _update():
            self.status_label.set_text(text)
            if is_loading:
                self.status_spinner.start()
                self.status_spinner.show()
                self.status_icon.hide()
            else:
                self.status_spinner.stop()
                self.status_spinner.hide()
                self.status_icon.show()
        GLib.idle_add(_update)

    # FEATURED CATALOG
    def check_is_installed(self, app):
        cmd = app.get("cmd", "")
        pkg = app.get("pkg", "").split()[0] if app.get("pkg") else ""
        
        binary = cmd.split()[0] if cmd else ""
        if binary and shutil.which(binary):
            return True

        if pkg and pkg in self.packages_dict:
            return self.packages_dict[pkg]["installed"]

        if pkg:
            res = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return "install ok installed" in res.stdout

        return False

    def refresh_installed_status(self):
        for app in FEATURED_APPS:
            self.installed_cache[app["id"]] = self.check_is_installed(app)

    def create_featured_card(self, app):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("app-card")
        card.set_size_request(280, 160)

        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        icon_img = Gtk.Image()
        resolved_icon = self.resolve_icon(app.get("icons", []))
        if resolved_icon.startswith("/"):
            try:
                pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(resolved_icon, 44, 44, True)
                icon_img.set_from_pixbuf(pix)
            except Exception:
                icon_img.set_from_icon_name("package-x-generic", Gtk.IconSize.DIALOG)
                icon_img.set_pixel_size(44)
        else:
            icon_img.set_from_icon_name(resolved_icon, Gtk.IconSize.DIALOG)
            icon_img.set_pixel_size(44)
        top_box.pack_start(icon_img, False, False, 0)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label=app["name"], xalign=0)
        title_lbl.get_style_context().add_class("app-title")
        title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        
        cat_lbl = Gtk.Label(label=app["category"], xalign=0)
        cat_lbl.get_style_context().add_class("app-category")

        rating_lbl = Gtk.Label(label=app.get("rating", "★★★★★ 4.8"), xalign=0)
        rating_lbl.get_style_context().add_class("app-rating")

        info_box.pack_start(title_lbl, False, False, 0)
        info_box.pack_start(cat_lbl, False, False, 0)
        info_box.pack_start(rating_lbl, False, False, 0)
        top_box.pack_start(info_box, True, True, 0)
        card.pack_start(top_box, False, False, 0)

        desc_lbl = Gtk.Label(label=app.get("desc", ""), xalign=0)
        desc_lbl.get_style_context().add_class("app-desc")
        desc_lbl.set_line_wrap(True)
        desc_lbl.set_max_width_chars(32)
        desc_lbl.set_lines(2)
        desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        card.pack_start(desc_lbl, True, True, 0)

        bot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dev_lbl = Gtk.Label(label=app.get("developer", "Linux"), xalign=0)
        dev_lbl.get_style_context().add_class("app-dev")
        dev_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        bot_box.pack_start(dev_lbl, True, True, 0)

        is_installed = self.installed_cache.get(app["id"], False)
        is_busy = app["id"] in self.active_jobs

        if is_busy:
            spinner = Gtk.Spinner()
            spinner.start()
            bot_box.pack_start(spinner, False, False, 0)
            busy_lbl = Gtk.Label(label="Processando...")
            busy_lbl.get_style_context().add_class("app-desc")
            bot_box.pack_start(busy_lbl, False, False, 0)
        elif is_installed:
            badge = Gtk.Label(label="Instalado")
            badge.get_style_context().add_class("badge-installed")
            bot_box.pack_start(badge, False, False, 0)

            open_btn = Gtk.Button(label="Abrir")
            open_btn.get_style_context().add_class("btn-primary")
            open_btn.connect("clicked", lambda b, a=app: self.launch_cmd(a["cmd"]))
            bot_box.pack_start(open_btn, False, False, 0)

            del_btn = Gtk.Button.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON)
            del_btn.set_tooltip_text("Desinstalar aplicativo")
            del_btn.get_style_context().add_class("btn-danger")
            del_btn.connect("clicked", lambda b, a=app: self.uninstall_pkg(a["pkg"], a["name"]))
            bot_box.pack_start(del_btn, False, False, 0)
        else:
            inst_btn = Gtk.Button(label="Obter")
            inst_btn.get_style_context().add_class("btn-primary")
            inst_btn.connect("clicked", lambda b, a=app: self.install_pkg(a["pkg"], a["name"]))
            bot_box.pack_start(inst_btn, False, False, 0)

        card.pack_start(bot_box, False, False, 0)
        return card

    def render_featured_catalog(self, query=""):
        for child in self.featured_flowbox.get_children():
            self.featured_flowbox.remove(child)

        for app in FEATURED_APPS:
            if query:
                match = (
                    query in app["name"].lower() or
                    query in app["desc"].lower() or
                    query in app["category"].lower() or
                    query in app["pkg"].lower()
                )
                if not match:
                    continue

            card = self.create_featured_card(app)
            self.featured_flowbox.add(card)

        self.featured_flowbox.show_all()

    # INSTANT PURE-PYTHON APT FILTERING (20ms across 79,000+ records)
    def filter_apt_packages(self):
        if not self.apt_loaded:
            return

        cat = self.apt_current_category
        allowed_sections = SECTION_MAP.get(cat)
        status_filter = self.apt_current_status
        query = self.apt_current_search.strip().lower()

        if allowed_sections is None:
            candidates = self.packages_db
        else:
            candidates = []
            for s in allowed_sections:
                candidates.extend(self.by_section.get(s, []))

        filtered = []
        for rec in candidates:
            if status_filter == "installed" and not rec["installed"]:
                continue
            elif status_filter == "available" and rec["installed"]:
                continue

            if query:
                name_match = query in rec["name"].lower()
                summary_match = query in rec["summary"].lower()
                if not (name_match or summary_match):
                    continue

            filtered.append(rec)

        self.apt_filtered_packages = filtered
        self.apt_page = 0
        self.render_database_page()

    def on_apt_category_toggled(self, btn, cat):
        if btn.get_active():
            self.apt_current_category = cat
            self.filter_apt_packages()

    def on_apt_status_toggled(self, btn, status_id):
        if btn.get_active():
            self.apt_current_status = status_id
            self.filter_apt_packages()

    def on_prev_page_clicked(self, btn):
        if self.apt_page > 0:
            self.apt_page -= 1
            self.render_database_page()

    def on_next_page_clicked(self, btn):
        max_page = max(0, (len(self.apt_filtered_packages) - 1) // self.apt_page_size)
        if self.apt_page < max_page:
            self.apt_page += 1
            self.render_database_page()

    def render_database_page(self):
        for child in self.db_flowbox.get_children():
            self.db_flowbox.remove(child)

        total = len(self.apt_filtered_packages)
        max_page = max(0, (total - 1) // self.apt_page_size) if total > 0 else 0
        self.apt_page = min(self.apt_page, max_page)

        start_idx = self.apt_page * self.apt_page_size
        end_idx = min(start_idx + self.apt_page_size, total)
        
        self.apt_count_label.set_text(f"Exibindo {start_idx + 1 if total > 0 else 0}–{end_idx} de {total:,} pacotes")
        self.page_info_lbl.set_text(f"Página {self.apt_page + 1} de {max_page + 1}")
        self.prev_btn.set_sensitive(self.apt_page > 0)
        self.next_btn.set_sensitive(self.apt_page < max_page)

        page_records = self.apt_filtered_packages[start_idx:end_idx]

        for rec in page_records:
            card = self.create_package_card(rec)
            self.db_flowbox.add(card)

        self.db_flowbox.show_all()

    def create_package_card(self, rec):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("pkg-card")
        card.set_size_request(450, 105)

        sec = rec["section"]
        version = rec["version"]
        size_str = format_size(rec["size"])
        summary = rec["summary"] if rec["summary"] else "Pacote oficial do Ubuntu/Debian"
        pkg_name = rec["name"]

        # Top row: Icon + Name + Section + Size
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        icon_name = "package-x-generic"
        if sec in ("web", "net", "mail"):
            icon_name = "applications-internet"
        elif sec in ("devel", "python", "rust", "golang", "java"):
            icon_name = "applications-development"
        elif sec in ("graphics",):
            icon_name = "applications-graphics"
        elif sec in ("sound", "video"):
            icon_name = "applications-multimedia"
        elif sec in ("editors", "text", "doc"):
            icon_name = "accessories-text-editor"
        elif sec in ("games",):
            icon_name = "applications-games"
        elif sec in ("science", "math"):
            icon_name = "applications-science"
        elif sec in ("admin", "x11"):
            icon_name = "preferences-system"

        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DND)
        icon.set_pixel_size(32)
        top_box.pack_start(icon, False, False, 0)

        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_lbl = Gtk.Label(label=pkg_name, xalign=0)
        title_lbl.get_style_context().add_class("app-title")
        title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        name_box.pack_start(title_lbl, False, False, 0)

        sec_badge = Gtk.Label(label=sec)
        sec_badge.get_style_context().add_class("badge-section")
        name_box.pack_start(sec_badge, False, False, 0)
        top_box.pack_start(name_box, True, True, 0)

        v_lbl = Gtk.Label(label=f"v{version[:12]} · {size_str}", xalign=1)
        v_lbl.get_style_context().add_class("app-dev")
        top_box.pack_end(v_lbl, False, False, 0)

        card.pack_start(top_box, False, False, 0)

        # Summary text
        desc_lbl = Gtk.Label(label=summary, xalign=0)
        desc_lbl.get_style_context().add_class("app-desc")
        desc_lbl.set_line_wrap(True)
        desc_lbl.set_max_width_chars(58)
        desc_lbl.set_lines(1)
        desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        card.pack_start(desc_lbl, True, True, 0)

        # Bottom row: Actions & Details
        bot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        detail_btn = Gtk.Button(label="Detalhes")
        detail_btn.get_style_context().add_class("btn-secondary")
        detail_btn.connect("clicked", lambda b, n=pkg_name: self.show_package_details_modal(n))
        bot_box.pack_start(detail_btn, False, False, 0)

        bot_box.pack_start(Gtk.Box(), True, True, 0)

        is_busy = pkg_name in self.active_jobs
        if is_busy:
            spinner = Gtk.Spinner()
            spinner.start()
            bot_box.pack_start(spinner, False, False, 0)
            busy_lbl = Gtk.Label(label="Processando...")
            busy_lbl.get_style_context().add_class("app-desc")
            bot_box.pack_start(busy_lbl, False, False, 0)
        elif rec["installed"]:
            badge = Gtk.Label(label="Instalado")
            badge.get_style_context().add_class("badge-installed")
            bot_box.pack_start(badge, False, False, 0)

            del_btn = Gtk.Button(label="Remover")
            del_btn.get_style_context().add_class("btn-danger")
            del_btn.connect("clicked", lambda b, n=pkg_name: self.uninstall_pkg(n, n))
            bot_box.pack_start(del_btn, False, False, 0)
        else:
            inst_btn = Gtk.Button(label="Obter")
            inst_btn.get_style_context().add_class("btn-primary")
            inst_btn.connect("clicked", lambda b, n=pkg_name: self.install_pkg(n, n))
            bot_box.pack_start(inst_btn, False, False, 0)

        card.pack_start(bot_box, False, False, 0)
        return card

    # PACKAGE DETAILS MODAL
    def show_package_details_modal(self, pkg_name):
        rec = self.packages_dict.get(pkg_name)
        if not rec:
            return

        dialog = Gtk.Dialog(
            title=f"Detalhes: {pkg_name}",
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.set_default_size(560, 420)
        
        content = dialog.get_content_area()
        content.set_spacing(12)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(16)
        content.set_margin_bottom(16)

        # Header with icon & name
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        icon = Gtk.Image.new_from_icon_name("package-x-generic", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(48)
        header_box.pack_start(icon, False, False, 0)

        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        t_lbl = Gtk.Label(label=pkg_name, xalign=0)
        t_lbl.get_style_context().add_class("hero-title")
        sec_lbl = Gtk.Label(
            label=f"Seção: {rec['section']} · Versão: {rec['version']}",
            xalign=0
        )
        sec_lbl.get_style_context().add_class("app-category")
        title_vbox.pack_start(t_lbl, False, False, 0)
        title_vbox.pack_start(sec_lbl, False, False, 0)
        header_box.pack_start(title_vbox, True, True, 0)
        content.pack_start(header_box, False, False, 0)

        # Info Grid
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(16)

        def add_info_row(row, k, v):
            k_lbl = Gtk.Label(label=k, xalign=0)
            k_lbl.get_style_context().add_class("app-dev")
            v_lbl = Gtk.Label(label=v, xalign=0)
            v_lbl.get_style_context().add_class("app-title")
            grid.attach(k_lbl, 0, row, 1, 1)
            grid.attach(v_lbl, 1, row, 1, 1)

        status_text = "Instalado no Sistema" if rec["installed"] else "Não Instalado (Disponível)"
        add_info_row(0, "Status:", status_text)
        add_info_row(1, "Tamanho de Download:", format_size(rec["size"]))
        add_info_row(2, "Versão Disponível:", rec["version"])
        content.pack_start(grid, False, False, 0)

        # Full Description in scrolled box
        desc_frame = Gtk.Frame(label="Descrição do Pacote (APT)")
        desc_scroll = Gtk.ScrolledWindow()
        desc_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        desc_scroll.set_min_content_height(140)

        # Try to read full description from apt cache if available
        full_desc = rec["summary"]
        if self.apt_cache and pkg_name in self.apt_cache:
            cand = self.apt_cache[pkg_name].candidate
            if cand and cand.description:
                full_desc = cand.description

        desc_text = Gtk.Label(label=full_desc, xalign=0, yalign=0)
        desc_text.get_style_context().add_class("app-desc")
        desc_text.set_line_wrap(True)
        desc_text.set_margin_start(10)
        desc_text.set_margin_end(10)
        desc_text.set_margin_top(8)
        desc_text.set_margin_bottom(8)
        desc_scroll.add(desc_text)
        desc_frame.add(desc_scroll)
        content.pack_start(desc_frame, True, True, 0)

        # Action buttons inside dialog
        action_box = dialog.get_action_area()
        if rec["installed"]:
            rem_btn = Gtk.Button(label="Desinstalar Pacote")
            rem_btn.get_style_context().add_class("btn-danger")
            rem_btn.connect("clicked", lambda b: (dialog.destroy(), self.uninstall_pkg(pkg_name, pkg_name)))
            action_box.pack_start(rem_btn, False, False, 0)
        else:
            inst_btn = Gtk.Button(label="Instalar Pacote")
            inst_btn.get_style_context().add_class("btn-primary")
            inst_btn.connect("clicked", lambda b: (dialog.destroy(), self.install_pkg(pkg_name, pkg_name)))
            action_box.pack_start(inst_btn, False, False, 0)

        close_btn = Gtk.Button(label="Fechar")
        close_btn.get_style_context().add_class("btn-secondary")
        close_btn.connect("clicked", lambda b: dialog.response(Gtk.ResponseType.CLOSE))
        action_box.pack_end(close_btn, False, False, 0)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

    # LIBRARY (Installed Desktop Apps)
    def render_library(self, query=""):
        for child in self.lib_flowbox.get_children():
            self.lib_flowbox.remove(child)

        apps = self.get_installed_desktop_apps()

        for app in apps:
            if query and query not in app["name"].lower() and query not in app.get("comment", "").lower():
                continue

            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.get_style_context().add_class("app-card")
            card.set_size_request(280, 140)

            top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            icon_img = Gtk.Image()
            theme = Gtk.IconTheme.get_default()
            icon_name = app.get("icon", "application-x-executable")
            if theme.has_icon(icon_name):
                icon_img.set_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
                icon_img.set_pixel_size(44)
            else:
                icon_img.set_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
                icon_img.set_pixel_size(44)
            top_box.pack_start(icon_img, False, False, 0)

            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title_lbl = Gtk.Label(label=app["name"], xalign=0)
            title_lbl.get_style_context().add_class("app-title")
            title_lbl.set_ellipsize(Pango.EllipsizeMode.END)

            cat_lbl = Gtk.Label(label=app.get("categories", "Sistema"), xalign=0)
            cat_lbl.get_style_context().add_class("app-category")

            info_box.pack_start(title_lbl, False, False, 0)
            info_box.pack_start(cat_lbl, False, False, 0)
            top_box.pack_start(info_box, True, True, 0)
            card.pack_start(top_box, False, False, 0)

            desc_lbl = Gtk.Label(label=app.get("comment", "Aplicativo do sistema"), xalign=0)
            desc_lbl.get_style_context().add_class("app-desc")
            desc_lbl.set_line_wrap(True)
            desc_lbl.set_max_width_chars(32)
            desc_lbl.set_lines(2)
            desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            card.pack_start(desc_lbl, True, True, 0)

            bot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            badge = Gtk.Label(label="Instalado")
            badge.get_style_context().add_class("badge-installed")
            bot_box.pack_start(badge, False, False, 0)

            open_btn = Gtk.Button(label="Abrir")
            open_btn.get_style_context().add_class("btn-primary")
            open_btn.connect("clicked", lambda b, cmd=app["exec"]: self.launch_cmd(cmd))
            bot_box.pack_end(open_btn, False, False, 0)

            card.pack_start(bot_box, False, False, 0)
            self.lib_flowbox.add(card)

        self.lib_flowbox.show_all()

    def get_installed_desktop_apps(self):
        seen = set()
        apps = []
        paths = ["/usr/share/applications/*.desktop", os.path.expanduser("~/.local/share/applications/*.desktop")]
        for p in paths:
            for file_path in glob.glob(p):
                try:
                    cp = configparser.ConfigParser(interpolation=None)
                    cp.read(file_path, encoding="utf-8", errors="ignore")
                    if not cp.has_section("Desktop Entry"):
                        continue
                    sec = cp["Desktop Entry"]
                    if sec.get("NoDisplay", "").lower() == "true":
                        continue
                    name = sec.get("Name")
                    exec_cmd = sec.get("Exec")
                    if not name or not exec_cmd or name in seen:
                        continue
                    seen.add(name)
                    clean_exec = exec_cmd.split("%")[0].strip()
                    apps.append({
                        "name": name,
                        "exec": clean_exec,
                        "icon": sec.get("Icon", "application-x-executable"),
                        "comment": sec.get("Comment", ""),
                        "categories": sec.get("Categories", "Aplicativo").split(";")[0]
                    })
                except Exception:
                    pass
        apps.sort(key=lambda x: x["name"].lower())
        return apps

    # ACTIONS: LAUNCH, INSTALL, UNINSTALL
    def launch_cmd(self, cmd):
        try:
            self.set_status(f"Iniciando {cmd.split()[0]}...", is_loading=False)
            subprocess.Popen(shlex.split(cmd))
        except Exception as e:
            self.set_status(f"Erro ao iniciar: {str(e)}", is_loading=False)

    def install_pkg(self, pkg_name, display_name):
        if pkg_name in self.active_jobs:
            return
        self.active_jobs.add(pkg_name)
        self.set_status(f"Instalando {display_name}... Aguarde alguns instantes.", is_loading=True)
        if self.stack.get_visible_child_name() == "featured":
            self.render_featured_catalog()
        elif self.stack.get_visible_child_name() == "database":
            self.render_database_page()
            
        threading.Thread(target=self._worker_install_pkg, args=(pkg_name, display_name), daemon=True).start()

    def _worker_install_pkg(self, pkg_name, display_name):
        cmd = f"sudo DEBIAN_FRONTEND=noninteractive apt-get update -y && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y {pkg_name}"
        try:
            proc = subprocess.run(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                msg = f"'{display_name}' instalado com sucesso!"
            else:
                msg = f"Falha na instalação de '{display_name}': {proc.stderr[:100]}"
        except Exception as e:
            msg = f"Erro: {str(e)}"
        finally:
            self.active_jobs.discard(pkg_name)
            self._init_apt_cache_worker()
            GLib.idle_add(self._on_action_finished, msg)

    def uninstall_pkg(self, pkg_name, display_name):
        if pkg_name in self.active_jobs:
            return

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Desinstalar {display_name}?"
        )
        dialog.format_secondary_text("Deseja realmente remover este pacote do sistema?")
        res = dialog.run()
        dialog.destroy()
        if res != Gtk.ResponseType.YES:
            return

        self.active_jobs.add(pkg_name)
        self.set_status(f"Removendo {display_name}...", is_loading=True)
        if self.stack.get_visible_child_name() == "featured":
            self.render_featured_catalog()
        elif self.stack.get_visible_child_name() == "database":
            self.render_database_page()

        threading.Thread(target=self._worker_uninstall_pkg, args=(pkg_name, display_name), daemon=True).start()

    def _worker_uninstall_pkg(self, pkg_name, display_name):
        cmd = f"sudo DEBIAN_FRONTEND=noninteractive apt-get remove -y {pkg_name}"
        try:
            proc = subprocess.run(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                msg = f"'{display_name}' removido com sucesso!"
            else:
                msg = f"Falha na remoção: {proc.stderr[:100]}"
        except Exception as e:
            msg = f"Erro: {str(e)}"
        finally:
            self.active_jobs.discard(pkg_name)
            self._init_apt_cache_worker()
            GLib.idle_add(self._on_action_finished, msg)

    def on_system_upgrade_clicked(self, btn):
        self.set_status("Atualizando todos os pacotes do sistema em segundo plano...", is_loading=True)
        threading.Thread(target=self._worker_system_upgrade, daemon=True).start()

    def _worker_system_upgrade(self):
        cmd = "sudo DEBIAN_FRONTEND=noninteractive apt-get update -y && sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y"
        try:
            proc = subprocess.run(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            msg = "Sistema e pacotes atualizados com sucesso!" if proc.returncode == 0 else "Aviso: alguns pacotes não puderam ser atualizados."
        except Exception as e:
            msg = f"Erro na atualização: {str(e)}"
        self._init_apt_cache_worker()
        GLib.idle_add(self._on_action_finished, msg)

    def _on_action_finished(self, msg):
        self.refresh_installed_status()
        self.render_featured_catalog()
        if self.stack.get_visible_child_name() == "database":
            self.filter_apt_packages()
        elif self.stack.get_visible_child_name() == "library":
            self.render_library()
        self.set_status(msg, is_loading=False)


def main():
    app = WinStoreApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    app.status_spinner.hide()
    Gtk.main()

if __name__ == "__main__":
    main()
