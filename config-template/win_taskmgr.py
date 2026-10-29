#!/usr/bin/env python3
"""
Windows 10/11 Task Manager for Linux (Python 3 + GTK3 + Cairo)
Ultra-lightweight, zero idle daemon, < 0.05% CPU, native X11/GTK integration.
Features:
- In-place row updates (zero jumping, rock-solid persistent selection)
- Stable sorting by name/friendly name by default
- Comprehensive Process Management:
  * Finalizar tarefa (SIGTERM)
  * Forçar finalização (SIGKILL)
  * Finalizar árvore de processos
  * Suspender / Retomar processo (SIGSTOP / SIGCONT)
  * Definir prioridade (Nice)
  * Abrir local do arquivo no Thunar
  * Copiar Nome, PID, Caminho e Linha de comando
  * Propriedades e Análise Completa (Modal Estilo Windows 11)
  * Velocidade de atualização configurável (Normal, Rápida, Baixa, Pausada)
  * Teclas de atalho (Delete, Shift+Del, Alt+Enter, F5, Ctrl+N, Ctrl+F)
"""

import os
import sys
import time
import pwd
import grp
import signal
import subprocess
import re
from collections import deque

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, Gdk, GLib, Pango, GObject
import cairo

# Friendly App Names and Icons
KNOWN_APPS = {
    "chrome": ("Google Chrome", "google-chrome"),
    "google-chrome": ("Google Chrome", "google-chrome"),
    "chromium": ("Chromium", "chromium"),
    "thunar": ("Gerenciador de Arquivos (Thunar)", "system-file-manager"),
    "thunar-real": ("Gerenciador de Arquivos (Thunar)", "system-file-manager"),
    "xfce4-terminal": ("Terminal", "utilities-terminal"),
    "synaptic": ("Instalar Apps (Synaptic)", "software-store"),
    "synaptic-pkexec": ("Instalar Apps (Synaptic)", "software-store"),
    "win-taskmgr": ("Gerenciador de Tarefas", "utilities-system-monitor"),
    "win_taskmgr.py": ("Gerenciador de Tarefas", "utilities-system-monitor"),
    "win-store": ("Microsoft Store", "software-store"),
    "win-store.py": ("Microsoft Store", "software-store"),
    "account-settings-gui": ("Configurações da Conta", "preferences-desktop-user"),
    "account_settings_gui.py": ("Configurações da Conta", "preferences-desktop-user"),
    "mousepad": ("Editor de Texto (Mousepad)", "accessories-text-editor"),
    "code": ("Visual Studio Code", "code"),
    "viewnior": ("Visualizador de Imagens", "image-viewer"),
    "xarchiver": ("Gerenciador de Arquivos Comprimidos", "xarchiver"),
    "vlc": ("VLC Media Player", "vlc"),
    "firefox": ("Mozilla Firefox", "firefox"),
}

KNOWN_BACKGROUND = {
    "xfwm4": "Gerenciador de Janelas XFWM",
    "xfce4-panel": "Barra de Tarefas XFCE",
    "xfsettingsd": "Serviço de Configurações XFCE",
    "xfdesktop": "Área de Trabalho XFCE",
    "docklike-plugin": "Docklike Taskbar Plugin",
    "genmon-plugin": "Monitor de Recursos do Painel",
    "nginx": "Servidor Web Nginx",
    "pulseaudio": "Servidor de Áudio PulseAudio",
    "dbus-daemon": "Barramento do Sistema D-Bus",
    "s6-supervise": "Supervisor de Serviços do Contêiner",
    "selkies": "Servidor de Vídeo WebRTC Selkies",
    "omniroute": "Roteamento de Rede Omniroute",
    "polkitd": "Serviço de Políticas Polkit",
    "cron": "Agendador Cron",
    "systemd": "Gerenciador do Sistema",
    "auth_server.py": "Servidor de Autenticação Webtop",
}

CSS_DATA = b"""
* {
    font-family: 'Segoe UI', 'Ubuntu', 'DejaVu Sans', sans-serif;
}

window {
    background-color: #1f1f1f;
    color: #e0e0e0;
}

/* Header & Navigation Bar */
.win-nav-bar {
    background-color: #242424;
    border-bottom: 1px solid #333333;
    padding: 5px 12px;
}

.nav-tab-btn {
    background: transparent;
    color: #a0a0a0;
    font-size: 13px;
    font-weight: 500;
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    margin-right: 4px;
}

.nav-tab-btn:hover {
    background-color: #2e2e2e;
    color: #ffffff;
}

.nav-tab-btn.active {
    color: #ffffff;
    font-weight: 600;
    border-bottom: 2px solid #0078d4;
    background-color: rgba(0, 120, 212, 0.08);
}

/* Action Buttons */
.btn-end-task {
    background-color: #0078d4;
    color: #ffffff;
    font-weight: 600;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 4px;
    border: 1px solid #1084d8;
}

.btn-end-task:hover {
    background-color: #1084d8;
}

.btn-end-task:active {
    background-color: #0067b8;
}

.btn-end-task:disabled {
    background-color: #2c2c2c;
    color: #666666;
    border: 1px solid #383838;
}

.btn-secondary {
    background-color: #2d2d2d;
    color: #cccccc;
    font-size: 12px;
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid #3d3d3d;
}

.btn-secondary:hover {
    background-color: #383838;
    color: #ffffff;
}

.btn-secondary:disabled {
    background-color: #252525;
    color: #555555;
    border-color: #333333;
}

.speed-combo {
    background-color: #2a2a2a;
    color: #e0e0e0;
    font-size: 12px;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 2px 6px;
}

.search-entry {
    background-color: #282828;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
}

.search-entry:focus {
    border-color: #0078d4;
}

/* System Metric Chips Banner */
.metrics-banner {
    background-color: #222222;
    border-bottom: 1px solid #303030;
    padding: 6px 14px;
}

.metric-chip {
    background-color: #2a2a2a;
    border: 1px solid #383838;
    border-radius: 5px;
    padding: 5px 14px;
    margin-right: 10px;
}

.metric-chip-title {
    color: #888888;
    font-size: 10px;
    font-weight: 600;
}

.metric-chip-value {
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}

/* TreeView Styling */
treeview {
    background-color: #1a1a1a;
    color: #dddddd;
    border: none;
}

treeview:selected, treeview:selected:focus {
    background-color: #0078d4;
    color: #ffffff;
}

treeview row {
    padding: 3px 0;
}

treeview row:hover {
    background-color: #262626;
}

treeview row:selected:hover {
    background-color: #1084d8;
}

treeview header button {
    background-color: #262626;
    color: #d0d0d0;
    font-weight: 600;
    font-size: 12px;
    border: none;
    border-right: 1px solid #333333;
    border-bottom: 1px solid #333333;
    padding: 6px 8px;
}

treeview header button:hover {
    background-color: #303030;
    color: #ffffff;
}

/* Performance Left Sidebar */
.perf-sidebar {
    background-color: #222222;
    border-right: 1px solid #333333;
    padding: 8px;
}

.perf-card-btn {
    background-color: #282828;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 8px;
}

.perf-card-btn:hover {
    background-color: #303030;
    border-color: #444444;
}

.perf-card-btn.active {
    background-color: #2a2a2a;
    border: 1px solid #0078d4;
    border-left: 4px solid #0078d4;
}

/* Stat Cards in Performance */
.stat-card {
    background-color: #262626;
    border: 1px solid #353535;
    border-radius: 5px;
    padding: 8px 12px;
}

.stat-label {
    color: #888888;
    font-size: 11px;
}

.stat-val {
    color: #ffffff;
    font-size: 15px;
    font-weight: 600;
}

/* Dialog Styling */
dialog {
    background-color: #202020;
    color: #e0e0e0;
}

.dialog-card {
    background-color: #262626;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 8px;
}

.btn-mini-copy {
    background-color: #333333;
    color: #cccccc;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 3px;
    border: 1px solid #444444;
}

.btn-mini-copy:hover {
    background-color: #444444;
    color: #ffffff;
}
"""

class TelemetryCollector:
    """Fast, zero-overhead proc reader."""
    def __init__(self):
        self.prev_total_cpu = 0
        self.prev_idle_cpu = 0
        self.prev_proc_ticks = {}
        self.uid_cache = {}
        self.cpu_model = self._detect_cpu_model()
        self.cpu_cores = os.cpu_count() or 1
        self.last_procs = []
        self.last_procs_by_pid = {}
        
        # Initial baseline sample
        self.cpu_history = deque(maxlen=60)
        self.mem_history = deque(maxlen=60)
        self.collect()
        time.sleep(0.06)
        init_data = self.collect()
        init_cpu = max(1.0, init_data['global_cpu'])
        init_mem = max(5.0, init_data['mem_pct'])
        for _ in range(60):
            self.cpu_history.append(init_cpu)
            self.mem_history.append(init_mem)
        
    def _detect_cpu_model(self):
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
        except:
            pass
        return "Processador x86_64"

    def get_user_name(self, uid):
        if uid not in self.uid_cache:
            try:
                self.uid_cache[uid] = pwd.getpwuid(uid).pw_name
            except:
                self.uid_cache[uid] = str(uid)
        return self.uid_cache[uid]

    def collect(self):
        # 1. Total CPU
        try:
            with open("/proc/stat") as f:
                fields = f.readline().split()
                total_cpu = sum(int(x) for x in fields[1:])
                idle_cpu = int(fields[4]) + int(fields[5])
        except:
            total_cpu = self.prev_total_cpu
            idle_cpu = self.prev_idle_cpu

        d_total = total_cpu - self.prev_total_cpu
        d_idle = idle_cpu - self.prev_idle_cpu
        global_cpu = 0.0
        if self.prev_total_cpu > 0 and d_total > 0:
            global_cpu = max(0.0, min(100.0, 100.0 * (1.0 - (d_idle / d_total))))
        self.prev_total_cpu = total_cpu
        self.prev_idle_cpu = idle_cpu
        self.cpu_history.append(global_cpu)

        # 2. Memory
        mem = {}
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if ":" in line:
                        k, v = line.split(":", 1)
                        mem[k.strip()] = int(v.split()[0])
        except:
            pass

        total_kb = mem.get("MemTotal", 1024)
        avail_kb = mem.get("MemAvailable", 0)
        used_kb = total_kb - avail_kb
        mem_pct = (used_kb / total_kb) * 100.0
        cached_kb = mem.get("Cached", 0) + mem.get("Buffers", 0)
        self.mem_history.append(mem_pct)

        # 3. Uptime
        try:
            with open("/proc/uptime") as f:
                uptime_s = float(f.read().split()[0])
        except:
            uptime_s = 0.0

        # 4. Read processes
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
        procs = []
        new_proc_ticks = {}
        total_threads = 0

        for pid_str in pids:
            try:
                pid = int(pid_str)
                with open(f"/proc/{pid}/stat") as f:
                    content = f.read()
                rparen = content.rfind(")")
                comm = content[content.find("(") + 1 : rparen]
                fields = content[rparen + 2 :].split()

                state_raw = fields[0]
                ppid = int(fields[1])
                utime = int(fields[11])
                stime = int(fields[12])
                priority = int(fields[15])
                nice = int(fields[16])
                threads = int(fields[17])
                vms_bytes = int(fields[20])
                rss_pages = int(fields[21])
                rss_bytes = rss_pages * 4096

                total_threads += threads
                ticks = utime + stime
                new_proc_ticks[pid] = ticks

                proc_cpu = 0.0
                if pid in self.prev_proc_ticks and d_total > 0:
                    dt = ticks - self.prev_proc_ticks[pid]
                    proc_cpu = max(0.0, min(100.0, (dt / d_total) * 100.0))

                # Read uid and full commandline
                uid = 1000
                gid = 1000
                cmdline = comm
                try:
                    with open(f"/proc/{pid}/status") as sf:
                        for line in sf:
                            if line.startswith("Uid:"):
                                uid = int(line.split()[1])
                            elif line.startswith("Gid:"):
                                gid = int(line.split()[1])
                    with open(f"/proc/{pid}/cmdline", "rb") as cf:
                        raw = cf.read().decode("utf-8", "replace").split("\0")
                        cmdline = " ".join([x for x in raw if x]) or comm
                except:
                    pass

                user_name = self.get_user_name(uid)

                # Classify into App vs Background
                is_app = False
                friendly_name = comm
                icon_name = "application-x-executable"
                base_bin = os.path.basename(cmdline.split()[0]) if cmdline else comm

                if comm in KNOWN_APPS:
                    friendly_name, icon_name = KNOWN_APPS[comm]
                    is_app = True
                elif base_bin in KNOWN_APPS:
                    friendly_name, icon_name = KNOWN_APPS[base_bin]
                    is_app = True
                elif comm in KNOWN_BACKGROUND:
                    friendly_name = KNOWN_BACKGROUND[comm]
                    icon_name = "applications-system"
                elif "win-store" in cmdline:
                    friendly_name = "Microsoft Store"
                    icon_name = "software-store"
                    is_app = True
                elif "account_settings_gui" in cmdline or "account-settings" in cmdline:
                    friendly_name = "Configurações da Conta"
                    icon_name = "preferences-desktop-user"
                    is_app = True
                elif "win_taskmgr" in cmdline or "win-taskmgr" in cmdline:
                    friendly_name = "Gerenciador de Tarefas"
                    icon_name = "utilities-system-monitor"
                    is_app = True

                # Process state string
                if state_raw == 'T':
                    state_str = "Suspenso"
                elif state_raw == 'R':
                    state_str = "Executando"
                elif state_raw == 'Z':
                    state_str = "Zumbi"
                elif state_raw == 'D':
                    state_str = "Aguardando E/S"
                else:
                    state_str = "Executando"

                procs.append({
                    "pid": pid,
                    "ppid": ppid,
                    "comm": comm,
                    "cmdline": cmdline,
                    "friendly_name": friendly_name,
                    "icon_name": icon_name,
                    "is_app": is_app,
                    "state_raw": state_raw,
                    "state_str": state_str,
                    "priority": priority,
                    "nice": nice,
                    "threads": threads,
                    "rss": rss_bytes,
                    "vms": vms_bytes,
                    "cpu": proc_cpu,
                    "ticks": ticks,
                    "uid": uid,
                    "gid": gid,
                    "user": user_name
                })
            except:
                pass

        self.prev_proc_ticks = new_proc_ticks
        self.last_procs = procs
        self.last_procs_by_pid = {p['pid']: p for p in procs}

        return {
            "global_cpu": global_cpu,
            "total_mem_kb": total_kb,
            "used_mem_kb": used_kb,
            "avail_mem_kb": avail_kb,
            "cached_mem_kb": cached_kb,
            "mem_pct": mem_pct,
            "uptime_s": uptime_s,
            "proc_count": len(procs),
            "thread_count": total_threads,
            "procs": procs
        }

class CairoChart(Gtk.DrawingArea):
    """Draws real-time telemetry line charts with gradients."""
    def __init__(self, history_deque, line_color=(0.0, 0.64, 0.94), fill_color=(0.0, 0.64, 0.94), is_mini=False):
        super().__init__()
        self.history = history_deque
        self.line_color = line_color
        self.fill_color = fill_color
        self.is_mini = is_mini
        self.connect("draw", self.on_draw)

    def on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w = alloc.width
        h = alloc.height

        # Background
        if self.is_mini:
            cr.set_source_rgb(0.12, 0.12, 0.12)
        else:
            cr.set_source_rgb(0.09, 0.09, 0.09)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Grid lines (if not mini)
        if not self.is_mini:
            cr.set_source_rgba(0.28, 0.28, 0.28, 0.85)
            cr.set_line_width(1.0)
            # Horizontal lines (4 divisions)
            for i in range(1, 4):
                y = (h / 4.0) * i
                cr.move_to(0, y)
                cr.line_to(w, y)
                cr.stroke()
            # Vertical lines (10 divisions)
            for i in range(1, 10):
                x = (w / 10.0) * i
                cr.move_to(x, 0)
                cr.line_to(x, h)
                cr.stroke()

            # Axis labels
            cr.set_source_rgba(0.55, 0.55, 0.55, 0.9)
            cr.select_font_face("Segoe UI", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(9)
            cr.move_to(w - 32, 12)
            cr.show_text("100%")
            cr.move_to(w - 26, (h / 2.0) + 4)
            cr.show_text("50%")
            cr.move_to(w - 20, h - 4)
            cr.show_text("0%")
            cr.move_to(8, h - 4)
            cr.show_text("60 s")
            cr.move_to(w - 48, h - 4)
            cr.show_text("0 s")

        # Data line
        pts = list(self.history)
        if not pts:
            return False

        n = len(pts)
        dx = w / max(1, n - 1)

        # Plot curve
        cr.set_line_width(2.0 if not self.is_mini else 1.5)
        cr.set_source_rgb(*self.line_color)

        cr.move_to(0, h - (pts[0] / 100.0) * (h - 8) - 4)
        for i in range(1, n):
            val = max(0.0, min(100.0, pts[i]))
            x = i * dx
            y = h - (val / 100.0) * (h - 8) - 4
            cr.line_to(x, y)
        cr.stroke_preserve()

        # Fill under curve
        cr.line_to(w, h)
        cr.line_to(0, h)
        cr.close_path()

        r, g, b = self.fill_color
        pat = cairo.LinearGradient(0, 0, 0, h)
        pat.add_color_stop_rgba(0.0, r, g, b, 0.35 if not self.is_mini else 0.25)
        pat.add_color_stop_rgba(1.0, r, g, b, 0.03)
        cr.set_source(pat)
        cr.fill()

        # Border
        cr.set_source_rgb(0.25, 0.25, 0.25)
        cr.set_line_width(1.0)
        cr.rectangle(0, 0, w, h)
        cr.stroke()

        return False

class ProcessPropertiesDialog(Gtk.Dialog):
    """Modern Windows 11 Fluent Process Properties & Analysis Modal."""
    def __init__(self, parent_window, pid, friendly_name, icon_name):
        super().__init__(
            title=f"Propriedades - {friendly_name} (PID: {pid})",
            transient_for=parent_window,
            flags=Gtk.DialogFlags.MODAL
        )
        self.set_default_size(600, 480)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_icon_name(icon_name)
        self.parent_window = parent_window
        self.pid = pid
        self.friendly_name = friendly_name

        # Read details from /proc
        self._inspect_proc(pid)
        self._build_ui(icon_name)

    def _inspect_proc(self, pid):
        self.exe_path = "N/A"
        self.cwd_path = "N/A"
        self.cmdline = "N/A"
        self.open_fds = 0
        self.parent_name = "N/A"
        
        try:
            self.exe_path = os.readlink(f"/proc/{pid}/exe")
        except:
            pass
        try:
            self.cwd_path = os.readlink(f"/proc/{pid}/cwd")
        except:
            pass
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                raw = f.read().decode("utf-8", "replace").split("\0")
                self.cmdline = " ".join([x for x in raw if x]) or self.friendly_name
        except:
            pass
        try:
            self.open_fds = len(os.listdir(f"/proc/{pid}/fd"))
        except:
            pass

        # Fetch telemetry info if cached
        p_info = self.parent_window.collector.last_procs_by_pid.get(pid, {})
        self.ppid = p_info.get("ppid", 0)
        if self.ppid > 0:
            try:
                with open(f"/proc/{self.ppid}/comm") as f:
                    self.parent_name = f.read().strip()
            except:
                self.parent_name = str(self.ppid)
        
        self.user = p_info.get("user", "1000")
        self.uid = p_info.get("uid", 1000)
        self.gid = p_info.get("gid", 1000)
        self.threads = p_info.get("threads", 1)
        self.rss = p_info.get("rss", 0)
        self.vms = p_info.get("vms", 0)
        self.cpu = p_info.get("cpu", 0.0)
        self.ticks = p_info.get("ticks", 0)
        self.state_str = p_info.get("state_str", "Executando")
        self.state_raw = p_info.get("state_raw", "R")
        self.nice = p_info.get("nice", 0)

    def _build_ui(self, icon_name):
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_start(16)
        content_area.set_margin_end(16)
        content_area.set_margin_top(14)
        content_area.set_margin_bottom(10)

        # Header: Icon + Friendly Name + PID
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        content_area.pack_start(header_box, False, False, 0)

        icon_theme = Gtk.IconTheme.get_default()
        pixbuf = None
        for iname in (icon_name, "application-x-executable"):
            if icon_theme.has_icon(iname):
                try:
                    pixbuf = icon_theme.load_icon(iname, 48, Gtk.IconLookupFlags.FORCE_SIZE)
                    break
                except:
                    pass
        if pixbuf:
            img = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            img = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DIALOG)
        header_box.pack_start(img, False, False, 0)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header_box.pack_start(title_box, True, True, 0)

        lbl_title = Gtk.Label()
        lbl_title.set_markup(f"<span size='x-large' weight='bold'>{GLib.markup_escape_text(self.friendly_name)}</span>")
        lbl_title.set_xalign(0)
        title_box.pack_start(lbl_title, False, False, 0)

        lbl_sub = Gtk.Label()
        state_color = "#f59e0b" if self.state_raw == 'T' else "#00cc6a"
        lbl_sub.set_markup(
            f"<span color='#aaaaaa'>PID: </span><b>{self.pid}</b>  •  "
            f"<span color='{state_color}'>●</span> <span color='#cccccc'>{self.state_str}</span>  •  "
            f"<span color='#aaaaaa'>Usuário: </span><b>{self.user}</b>"
        )
        lbl_sub.set_xalign(0)
        title_box.pack_start(lbl_sub, False, False, 0)

        # Notebook with Tabs: Geral e Desempenho
        notebook = Gtk.Notebook()
        content_area.pack_start(notebook, True, True, 4)

        # Tab 1: Geral & Identificação
        tab1_box = self._build_general_tab()
        notebook.append_page(tab1_box, Gtk.Label(label="Identificação & Geral"))

        # Tab 2: Desempenho & Recursos
        tab2_box = self._build_resources_tab()
        notebook.append_page(tab2_box, Gtk.Label(label="Desempenho & Recursos"))

        # Footer Action Buttons
        btn_open = Gtk.Button(label="Abrir Local do Arquivo")
        btn_open.get_style_context().add_class("btn-secondary")
        btn_open.connect("clicked", lambda b: self.parent_window.open_file_location(self.pid))
        self.add_action_widget(btn_open, Gtk.ResponseType.NONE)

        btn_kill = Gtk.Button(label="Finalizar Tarefa")
        btn_kill.get_style_context().add_class("btn-end-task")
        btn_kill.connect("clicked", self._on_dialog_kill)
        self.add_action_widget(btn_kill, Gtk.ResponseType.OK)

        btn_close = Gtk.Button(label="Fechar")
        btn_close.get_style_context().add_class("btn-secondary")
        btn_close.connect("clicked", lambda b: self.destroy())
        self.add_action_widget(btn_close, Gtk.ResponseType.CLOSE)

        self.show_all()

    def _build_general_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        # Executable Path Row
        box.pack_start(self._create_path_row("Caminho do Executável:", self.exe_path), False, False, 0)

        # Command Line Box
        lbl_cmd = Gtk.Label(label="Linha de Comando Completa:")
        lbl_cmd.set_xalign(0)
        lbl_cmd.get_style_context().add_class("stat-label")
        box.pack_start(lbl_cmd, False, False, 0)

        cmd_frame = Gtk.Frame()
        box.pack_start(cmd_frame, True, True, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        cmd_frame.add(scroll)

        tv = Gtk.TextView()
        tv.set_editable(False)
        tv.set_wrap_mode(Gtk.WrapMode.CHAR)
        tv.get_buffer().set_text(self.cmdline)
        tv.set_margin_start(6)
        tv.set_margin_end(6)
        tv.set_margin_top(6)
        tv.set_margin_bottom(6)
        scroll.add(tv)

        # Working Directory Row
        box.pack_start(self._create_path_row("Diretório de Trabalho (CWD):", self.cwd_path), False, False, 0)

        # Grid of General Meta
        grid = Gtk.Grid()
        grid.set_column_spacing(16)
        grid.set_row_spacing(6)
        box.pack_start(grid, False, False, 4)

        self._add_meta_item(grid, 0, 0, "Processo Pai (PPID):", f"{self.ppid} ({self.parent_name})")
        self._add_meta_item(grid, 1, 0, "Prioridade (Nice):", f"{self.nice}")
        self._add_meta_item(grid, 0, 1, "Usuário / Grupo:", f"{self.user} (UID: {self.uid}, GID: {self.gid})")
        self._add_meta_item(grid, 1, 1, "Arquivos / FDs Abertos:", f"{self.open_fds} descritores")

        return box

    def _build_resources_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(10)
        grid.set_column_homogeneous(True)
        box.pack_start(grid, False, False, 0)

        # Format Memory
        rss_mb = self.rss / 1048576.0
        rss_str = f"{rss_mb:.1f} MB" if rss_mb < 1024 else f"{rss_mb/1024.0:.2f} GB"

        vms_mb = self.vms / 1048576.0
        vms_str = f"{vms_mb:.1f} MB" if vms_mb < 1024 else f"{vms_mb/1024.0:.2f} GB"

        # Format CPU time
        # Standard clock ticks are 100 per sec
        cpu_secs = self.ticks / 100.0
        m = int(cpu_secs // 60)
        s = int(cpu_secs % 60)
        ms = int((cpu_secs - int(cpu_secs)) * 10)
        cpu_time_str = f"{m:02d}:{s:02d}.{ms}"

        self.parent_window._create_stat_card(grid, 0, 0, "Utilização de CPU Atual", f"{self.cpu:.1f} %")
        self.parent_window._create_stat_card(grid, 1, 0, "Tempo de CPU Total", cpu_time_str)
        self.parent_window._create_stat_card(grid, 2, 0, "Threads Ativas", str(self.threads))

        self.parent_window._create_stat_card(grid, 0, 1, "Memória Física (RSS)", rss_str)
        self.parent_window._create_stat_card(grid, 1, 1, "Memória Virtual (VMS)", vms_str)
        self.parent_window._create_stat_card(grid, 2, 1, "Descritores de E/S (FDs)", f"{self.open_fds}")

        # Explanatory card
        expl_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        expl_card.get_style_context().add_class("dialog-card")
        box.pack_start(expl_card, False, False, 6)

        lbl_e_title = Gtk.Label(label="<b>Diagnóstico do Processo</b>")
        lbl_e_title.set_use_markup(True)
        lbl_e_title.set_xalign(0)
        expl_card.pack_start(lbl_e_title, False, False, 0)

        diag_text = (
            f"O processo <b>{GLib.markup_escape_text(self.friendly_name)}</b> está atualmente <b>{self.state_str.lower()}</b>.\n"
            f"Aloca <b>{rss_str}</b> de memória RAM real e possui <b>{self.threads}</b> threads de execução ativas."
        )
        lbl_e_body = Gtk.Label()
        lbl_e_body.set_markup(diag_text)
        lbl_e_body.set_xalign(0)
        lbl_e_body.set_line_wrap(True)
        expl_card.pack_start(lbl_e_body, False, False, 0)

        return box

    def _create_path_row(self, label_text, path_val):
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl = Gtk.Label(label=label_text)
        lbl.set_xalign(0)
        lbl.get_style_context().add_class("stat-label")
        row.pack_start(lbl, False, False, 0)

        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.pack_start(inner, False, False, 0)

        val = Gtk.Label(label=path_val)
        val.set_xalign(0)
        val.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        val.set_selectable(True)
        inner.pack_start(val, True, True, 0)

        btn_copy = Gtk.Button(label="Copiar")
        btn_copy.get_style_context().add_class("btn-mini-copy")
        btn_copy.connect("clicked", lambda b: self.parent_window.copy_to_clipboard(path_val))
        inner.pack_end(btn_copy, False, False, 0)

        return row

    def _add_meta_item(self, grid, col, row, title, val):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl_t = Gtk.Label(label=title)
        lbl_t.get_style_context().add_class("stat-label")
        box.pack_start(lbl_t, False, False, 0)

        lbl_v = Gtk.Label(label=val)
        lbl_v.set_selectable(True)
        box.pack_start(lbl_v, False, False, 0)

        grid.attach(box, col, row, 1, 1)

    def _on_dialog_kill(self, btn):
        self.parent_window.terminate_pid(self.pid, signal.SIGTERM)
        self.destroy()

class WindowsTaskManager(Gtk.Window):
    def __init__(self, initial_tab="processos"):
        super().__init__(title="Gerenciador de Tarefas")
        self.set_default_size(980, 640)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("utilities-system-monitor")

        self.collector = TelemetryCollector()
        self.selected_pid = None
        self.selected_pids = []
        self.selected_row_ref = None
        self.search_query = ""
        self.timer_interval = 1500
        self.timer_id = None

        # Persistent Row References for In-Place Updates
        # Maps pid -> Gtk.TreeRowReference
        self.proc_row_refs = {}
        self.app_group_refs = {}
        self.details_row_refs = {}
        self.expanded_paths = set()
        self.tree_initialized = False
        self.details_initialized = False

        # Sort state
        self.proc_sort_column = "name"
        self.proc_sort_order = Gtk.SortType.ASCENDING

        # Load Dark CSS
        self._load_css()

        # Connect Global Keyboard Shortcuts
        self.connect("key-press-event", self.on_global_key_press)

        # Build Main Layout
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root_box)

        # 1. Windows 11 Top Bar (Tabs + Search + Actions)
        top_bar = self._build_top_bar()
        root_box.pack_start(top_bar, False, False, 0)

        # 2. System Metrics Summary Chips
        self.metrics_banner = self._build_metrics_banner()
        root_box.pack_start(self.metrics_banner, False, False, 0)

        # 3. Content Notebook/Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        root_box.pack_start(self.stack, True, True, 0)

        # Tab 1: Processos
        proc_page = self._build_processes_page()
        self.stack.add_named(proc_page, "processos")

        # Tab 2: Desempenho
        perf_page = self._build_performance_page()
        self.stack.add_named(perf_page, "desempenho")

        # Tab 3: Detalhes
        details_page = self._build_details_page()
        self.stack.add_named(details_page, "detalhes")

        # Initial data update
        self.on_timer_tick()

        # Switch to requested tab
        if initial_tab != "processos":
            if initial_tab == "desempenho":
                self._switch_tab("desempenho", self.btn_nav_perf)
            elif initial_tab == "detalhes":
                self._switch_tab("detalhes", self.btn_nav_details)

        # Start periodic update timer
        self.timer_id = GLib.timeout_add(self.timer_interval, self.on_timer_tick)

    def _load_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS_DATA)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_global_key_press(self, widget, event):
        # F5: Force Single Refresh
        if event.keyval == Gdk.KEY_F5:
            self.on_timer_tick()
            return True
        # Ctrl+F: Focus search box
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and (event.keyval in (Gdk.KEY_f, Gdk.KEY_F)):
            self.search_entry.grab_focus()
            return True
        # Ctrl+N: Run new task dialog
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and (event.keyval in (Gdk.KEY_n, Gdk.KEY_N)):
            self.on_run_new_task(None)
            return True
        # Delete: End task
        if event.keyval == Gdk.KEY_Delete:
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                self.force_kill_selected()
            else:
                self.on_end_task_clicked(None)
            return True
        # Alt+Enter: Properties
        if (event.state & Gdk.ModifierType.MOD1_MASK) and (event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter)):
            if self.selected_pid:
                self.show_properties(self.selected_pid)
            return True
        return False

    def _build_top_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.get_style_context().add_class("win-nav-bar")

        # Navigation Buttons (Processos, Desempenho, Detalhes)
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.pack_start(nav_box, False, False, 0)

        self.btn_nav_proc = Gtk.Button(label="Processos")
        self.btn_nav_proc.get_style_context().add_class("nav-tab-btn")
        self.btn_nav_proc.get_style_context().add_class("active")
        self.btn_nav_proc.connect("clicked", lambda b: self._switch_tab("processos", b))
        nav_box.pack_start(self.btn_nav_proc, False, False, 0)

        self.btn_nav_perf = Gtk.Button(label="Desempenho")
        self.btn_nav_perf.get_style_context().add_class("nav-tab-btn")
        self.btn_nav_perf.connect("clicked", lambda b: self._switch_tab("desempenho", b))
        nav_box.pack_start(self.btn_nav_perf, False, False, 0)

        self.btn_nav_details = Gtk.Button(label="Detalhes")
        self.btn_nav_details.get_style_context().add_class("nav-tab-btn")
        self.btn_nav_details.connect("clicked", lambda b: self._switch_tab("detalhes", b))
        nav_box.pack_start(self.btn_nav_details, False, False, 0)

        # Right-aligned Actions Box
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.pack_end(actions_box, False, False, 0)

        # Finalizar tarefa (Primary Windows Accent Blue)
        self.btn_kill = Gtk.Button(label="Finalizar tarefa")
        self.btn_kill.get_style_context().add_class("btn-end-task")
        self.btn_kill.set_sensitive(False)
        self.btn_kill.set_tooltip_text("Finalizar o processo selecionado (Del)")
        self.btn_kill.connect("clicked", self.on_end_task_clicked)
        actions_box.pack_end(self.btn_kill, False, False, 0)

        # Propriedades
        self.btn_props = Gtk.Button(label="Propriedades")
        self.btn_props.get_style_context().add_class("btn-secondary")
        self.btn_props.set_sensitive(False)
        self.btn_props.set_tooltip_text("Propriedades e Análise Completa (Alt+Enter ou duplo clique)")
        self.btn_props.connect("clicked", lambda b: self.show_properties(self.selected_pid))
        actions_box.pack_end(self.btn_props, False, False, 0)

        # Executar nova tarefa
        btn_run = Gtk.Button(label="Executar nova tarefa")
        btn_run.get_style_context().add_class("btn-secondary")
        btn_run.set_tooltip_text("Executar um programa ou comando (Ctrl+N)")
        btn_run.connect("clicked", self.on_run_new_task)
        actions_box.pack_end(btn_run, False, False, 0)

        # Velocidade de atualização selector
        self.combo_speed = Gtk.ComboBoxText()
        self.combo_speed.get_style_context().add_class("speed-combo")
        self.combo_speed.append("normal", "⏱️ Normal (1.5s)")
        self.combo_speed.append("fast", "⚡ Rápida (0.5s)")
        self.combo_speed.append("slow", "🐢 Baixa (4.0s)")
        self.combo_speed.append("paused", "⏸️ Pausada")
        self.combo_speed.set_active_id("normal")
        self.combo_speed.set_tooltip_text("Taxa de atualização dos dados")
        self.combo_speed.connect("changed", self.on_speed_changed)
        actions_box.pack_end(self.combo_speed, False, False, 0)

        # Search box
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Filtrar por nome ou PID (Ctrl+F)...")
        self.search_entry.get_style_context().add_class("search-entry")
        self.search_entry.set_width_chars(22)
        self.search_entry.connect("search-changed", self.on_search_changed)
        actions_box.pack_end(self.search_entry, False, False, 0)

        return bar

    def on_speed_changed(self, combo):
        active_id = combo.get_active_id()
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
        if active_id == "normal":
            self.timer_interval = 1500
            self.timer_id = GLib.timeout_add(1500, self.on_timer_tick)
        elif active_id == "fast":
            self.timer_interval = 500
            self.timer_id = GLib.timeout_add(500, self.on_timer_tick)
        elif active_id == "slow":
            self.timer_interval = 4000
            self.timer_id = GLib.timeout_add(4000, self.on_timer_tick)
        elif active_id == "paused":
            self.timer_interval = 0

    def _switch_tab(self, tab_name, active_btn):
        for btn in (self.btn_nav_proc, self.btn_nav_perf, self.btn_nav_details):
            btn.get_style_context().remove_class("active")
        active_btn.get_style_context().add_class("active")
        self.stack.set_visible_child_name(tab_name)

    def _build_metrics_banner(self):
        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        banner.get_style_context().add_class("metrics-banner")

        self.lbl_metric_cpu = self._create_metric_chip(banner, "CPU", "0%")
        self.lbl_metric_mem = self._create_metric_chip(banner, "MEMÓRIA", "0.0 GB (0%)")
        self.lbl_metric_proc = self._create_metric_chip(banner, "PROCESSOS", "0")
        self.lbl_metric_uptime = self._create_metric_chip(banner, "ATIVIDADE", "00:00:00")

        return banner

    def _create_metric_chip(self, parent, title, initial_val):
        chip = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        chip.get_style_context().add_class("metric-chip")

        lbl_t = Gtk.Label(label=title)
        lbl_t.get_style_context().add_class("metric-chip-title")
        lbl_t.set_xalign(0)
        chip.pack_start(lbl_t, False, False, 0)

        lbl_v = Gtk.Label(label=initial_val)
        lbl_v.get_style_context().add_class("metric-chip-value")
        lbl_v.set_xalign(0)
        chip.pack_start(lbl_v, False, False, 0)

        parent.pack_start(chip, False, False, 0)
        return lbl_v

    def _build_processes_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scroll, True, True, 0)

        # TreeStore columns:
        # 0: Icon Name (str)
        # 1: Display Name (str)
        # 2: Status (str)
        # 3: CPU % (float)
        # 4: CPU % Text (str)
        # 5: Memory Bytes (GObject.TYPE_INT64)
        # 6: Memory Text (str)
        # 7: PID (int)
        # 8: User (str)
        # 9: Is Group Header (bool)
        # 10: Sort Key (str)
        # 11: Row Key (str)
        self.proc_store = Gtk.TreeStore(str, str, str, float, str, GObject.TYPE_INT64, str, int, str, bool, str, str)
        self.proc_tree = Gtk.TreeView(model=self.proc_store)
        self.proc_tree.set_enable_search(False)
        self.proc_tree.connect("button-press-event", self.on_proc_tree_button_press)
        self.proc_tree.connect("row-activated", self.on_proc_row_double_click)

        sel = self.proc_tree.get_selection()
        sel.set_mode(Gtk.SelectionMode.SINGLE)
        sel.set_select_function(self._is_proc_row_selectable, None)
        sel.connect("changed", self.on_proc_selection_changed)

        # Track expansion state
        self.proc_tree.connect("row-expanded", self.on_row_expanded)
        self.proc_tree.connect("row-collapsed", self.on_row_collapsed)

        # Col 0: Nome (Icon + Name)
        col_name = Gtk.TreeViewColumn("Nome")
        col_name.set_min_width(320)
        col_name.set_resizable(True)
        col_name.set_clickable(True)
        col_name.connect("clicked", lambda c: self._set_sort_column("name"))

        cell_icon = Gtk.CellRendererPixbuf()
        cell_icon.set_property("stock-size", Gtk.IconSize.MENU)
        col_name.pack_start(cell_icon, False)
        col_name.add_attribute(cell_icon, "icon-name", 0)

        cell_name = Gtk.CellRendererText()
        cell_name.set_property("ellipsize", Pango.EllipsizeMode.END)
        col_name.pack_start(cell_name, True)
        col_name.add_attribute(cell_name, "markup", 1)
        self.proc_tree.append_column(col_name)

        # Col 1: Status
        col_status = Gtk.TreeViewColumn("Status")
        col_status.set_min_width(110)
        col_status.set_resizable(True)
        col_status.set_clickable(True)
        col_status.connect("clicked", lambda c: self._set_sort_column("status"))
        cell_status = Gtk.CellRendererText()
        col_status.pack_start(cell_status, True)
        col_status.add_attribute(cell_status, "markup", 2)
        self.proc_tree.append_column(col_status)

        # Col 2: CPU
        col_cpu = Gtk.TreeViewColumn("CPU")
        col_cpu.set_min_width(90)
        col_cpu.set_resizable(True)
        col_cpu.set_clickable(True)
        col_cpu.connect("clicked", lambda c: self._set_sort_column("cpu"))
        cell_cpu = Gtk.CellRendererText()
        cell_cpu.set_property("xalign", 1.0)
        col_cpu.pack_start(cell_cpu, True)
        col_cpu.add_attribute(cell_cpu, "markup", 4)
        self.proc_tree.append_column(col_cpu)

        # Col 3: Memória
        col_mem = Gtk.TreeViewColumn("Memória")
        col_mem.set_min_width(110)
        col_mem.set_resizable(True)
        col_mem.set_clickable(True)
        col_mem.connect("clicked", lambda c: self._set_sort_column("mem"))
        cell_mem = Gtk.CellRendererText()
        cell_mem.set_property("xalign", 1.0)
        col_mem.pack_start(cell_mem, True)
        col_mem.add_attribute(cell_mem, "markup", 6)
        self.proc_tree.append_column(col_mem)

        # Col 4: PID
        col_pid = Gtk.TreeViewColumn("PID")
        col_pid.set_min_width(80)
        col_pid.set_resizable(True)
        col_pid.set_clickable(True)
        col_pid.connect("clicked", lambda c: self._set_sort_column("pid"))
        cell_pid = Gtk.CellRendererText()
        cell_pid.set_property("xalign", 1.0)
        col_pid.pack_start(cell_pid, True)

        def _pid_cell_func(col, cell, model, tree_iter, data):
            pid = model.get_value(tree_iter, 7)
            is_group = model.get_value(tree_iter, 9)
            if is_group or pid <= 0:
                cell.set_property("text", "")
            else:
                cell.set_property("text", str(pid))
        col_pid.set_cell_data_func(cell_pid, _pid_cell_func)
        self.proc_tree.append_column(col_pid)

        # Col 5: Usuário
        col_user = Gtk.TreeViewColumn("Usuário")
        col_user.set_min_width(90)
        col_user.set_resizable(True)
        col_user.set_clickable(True)
        col_user.connect("clicked", lambda c: self._set_sort_column("user"))
        cell_user = Gtk.CellRendererText()
        col_user.pack_start(cell_user, True)
        col_user.add_attribute(cell_user, "text", 8)
        self.proc_tree.append_column(col_user)

        scroll.add(self.proc_tree)
        return box

    def _set_sort_column(self, col_key):
        if self.proc_sort_column == col_key:
            self.proc_sort_order = Gtk.SortType.DESCENDING if self.proc_sort_order == Gtk.SortType.ASCENDING else Gtk.SortType.ASCENDING
        else:
            self.proc_sort_column = col_key
            self.proc_sort_order = Gtk.SortType.DESCENDING if col_key in ("cpu", "mem") else Gtk.SortType.ASCENDING
        # Trigger full refresh with new sorting
        self.tree_initialized = False
        self.on_timer_tick()

    def on_row_expanded(self, tree, tree_iter, path):
        self.expanded_paths.add(str(path))

    def on_row_collapsed(self, tree, tree_iter, path):
        path_str = str(path)
        if path_str in self.expanded_paths:
            self.expanded_paths.remove(path_str)

    def _build_performance_page(self):
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(260)

        # Left Sidebar (Resource Cards: CPU, Memória)
        side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        side_box.get_style_context().add_class("perf-sidebar")
        paned.pack1(side_box, False, False)

        # CPU Card Button
        self.btn_card_cpu = Gtk.Button()
        self.btn_card_cpu.get_style_context().add_class("perf-card-btn")
        self.btn_card_cpu.get_style_context().add_class("active")
        self.btn_card_cpu.connect("clicked", lambda b: self._switch_perf_pane("cpu"))
        side_box.pack_start(self.btn_card_cpu, False, False, 0)

        cpu_card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.btn_card_cpu.add(cpu_card_box)

        lbl_c_title = Gtk.Label()
        lbl_c_title.set_markup("<b>CPU</b>")
        lbl_c_title.set_xalign(0)
        cpu_card_box.pack_start(lbl_c_title, False, False, 0)

        self.lbl_side_cpu_val = Gtk.Label()
        self.lbl_side_cpu_val.set_markup("<span color='#a0a0a0'>0%  2.50 GHz</span>")
        self.lbl_side_cpu_val.set_xalign(0)
        cpu_card_box.pack_start(self.lbl_side_cpu_val, False, False, 0)

        self.mini_chart_cpu = CairoChart(self.collector.cpu_history, (0.0, 0.64, 0.94), (0.0, 0.64, 0.94), is_mini=True)
        self.mini_chart_cpu.set_size_request(220, 36)
        cpu_card_box.pack_start(self.mini_chart_cpu, False, False, 4)

        # Memória Card Button
        self.btn_card_mem = Gtk.Button()
        self.btn_card_mem.get_style_context().add_class("perf-card-btn")
        self.btn_card_mem.connect("clicked", lambda b: self._switch_perf_pane("mem"))
        side_box.pack_start(self.btn_card_mem, False, False, 0)

        mem_card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.btn_card_mem.add(mem_card_box)

        lbl_m_title = Gtk.Label()
        lbl_m_title.set_markup("<b>Memória</b>")
        lbl_m_title.set_xalign(0)
        mem_card_box.pack_start(lbl_m_title, False, False, 0)

        self.lbl_side_mem_val = Gtk.Label()
        self.lbl_side_mem_val.set_markup("<span color='#a0a0a0'>0.0/0.0 GB (0%)</span>")
        self.lbl_side_mem_val.set_xalign(0)
        mem_card_box.pack_start(self.lbl_side_mem_val, False, False, 0)

        self.mini_chart_mem = CairoChart(self.collector.mem_history, (0.6, 0.4, 0.9), (0.6, 0.4, 0.9), is_mini=True)
        self.mini_chart_mem.set_size_request(220, 36)
        mem_card_box.pack_start(self.mini_chart_mem, False, False, 4)

        # Right Detail Stack
        self.perf_stack = Gtk.Stack()
        self.perf_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        paned.pack2(self.perf_stack, True, False)

        # CPU Detail View
        cpu_view = self._build_cpu_detail_view()
        self.perf_stack.add_named(cpu_view, "cpu")

        # Memory Detail View
        mem_view = self._build_mem_detail_view()
        self.perf_stack.add_named(mem_view, "mem")

        return paned

    def _switch_perf_pane(self, pane_name):
        self.btn_card_cpu.get_style_context().remove_class("active")
        self.btn_card_mem.get_style_context().remove_class("active")
        if pane_name == "cpu":
            self.btn_card_cpu.get_style_context().add_class("active")
        else:
            self.btn_card_mem.get_style_context().add_class("active")
        self.perf_stack.set_visible_child_name(pane_name)

    def _build_cpu_detail_view(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(15)
        box.set_margin_bottom(15)

        # Top Header: Title + Big Value
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(hdr, False, False, 0)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hdr.pack_start(title_box, False, False, 0)

        lbl_t = Gtk.Label()
        lbl_t.set_markup("<span size='xx-large' weight='bold'>CPU</span>")
        lbl_t.set_xalign(0)
        title_box.pack_start(lbl_t, False, False, 0)

        lbl_sub = Gtk.Label()
        lbl_sub.set_markup(f"<span color='#a0a0a0'>{self.collector.cpu_model} ({self.collector.cpu_cores} Núcleos)</span>")
        lbl_sub.set_xalign(0)
        title_box.pack_start(lbl_sub, False, False, 0)

        self.lbl_cpu_big_val = Gtk.Label()
        self.lbl_cpu_big_val.set_markup("<span size='xx-large' weight='bold' color='#00a4ef'>0 %</span>")
        hdr.pack_end(self.lbl_cpu_big_val, False, False, 0)

        # Big Cairo Chart
        self.big_chart_cpu = CairoChart(self.collector.cpu_history, (0.0, 0.64, 0.94), (0.0, 0.64, 0.94))
        self.big_chart_cpu.set_size_request(-1, 230)
        box.pack_start(self.big_chart_cpu, True, True, 4)

        # Telemetry Stat Cards Grid (2 rows x 3 cols)
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(10)
        grid.set_column_homogeneous(True)
        box.pack_start(grid, False, False, 0)

        self.stat_cpu_util = self._create_stat_card(grid, 0, 0, "Utilização", "0%")
        self.stat_cpu_speed = self._create_stat_card(grid, 1, 0, "Velocidade", "2.50 GHz")
        self.stat_cpu_procs = self._create_stat_card(grid, 2, 0, "Processos", "0")

        self.stat_cpu_threads = self._create_stat_card(grid, 0, 1, "Threads", "0")
        self.stat_cpu_uptime = self._create_stat_card(grid, 1, 1, "Tempo de atividade", "00:00:00")
        self.stat_cpu_cores = self._create_stat_card(grid, 2, 1, "Núcleos lógicos", str(self.collector.cpu_cores))

        return box

    def _build_mem_detail_view(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(15)
        box.set_margin_bottom(15)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(hdr, False, False, 0)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hdr.pack_start(title_box, False, False, 0)

        lbl_t = Gtk.Label()
        lbl_t.set_markup("<span size='xx-large' weight='bold'>Memória</span>")
        lbl_t.set_xalign(0)
        title_box.pack_start(lbl_t, False, False, 0)

        self.lbl_mem_sub = Gtk.Label()
        self.lbl_mem_sub.set_markup("<span color='#a0a0a0'>Memória do Sistema</span>")
        self.lbl_mem_sub.set_xalign(0)
        title_box.pack_start(self.lbl_mem_sub, False, False, 0)

        self.lbl_mem_big_val = Gtk.Label()
        self.lbl_mem_big_val.set_markup("<span size='xx-large' weight='bold' color='#a78bfa'>0.0 GB (0%)</span>")
        hdr.pack_end(self.lbl_mem_big_val, False, False, 0)

        # Big Cairo Chart
        self.big_chart_mem = CairoChart(self.collector.mem_history, (0.6, 0.4, 0.9), (0.6, 0.4, 0.9))
        self.big_chart_mem.set_size_request(-1, 230)
        box.pack_start(self.big_chart_mem, True, True, 4)

        # Stat Cards
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(10)
        grid.set_column_homogeneous(True)
        box.pack_start(grid, False, False, 0)

        self.stat_mem_used = self._create_stat_card(grid, 0, 0, "Em uso (Confirmada)", "0.0 GB")
        self.stat_mem_avail = self._create_stat_card(grid, 1, 0, "Disponível", "0.0 GB")
        self.stat_mem_total = self._create_stat_card(grid, 2, 0, "Total Instalado", "0.0 GB")

        self.stat_mem_cached = self._create_stat_card(grid, 0, 1, "Em cache", "0.0 GB")
        self.stat_mem_pct = self._create_stat_card(grid, 1, 1, "Utilização", "0%")
        self.stat_mem_type = self._create_stat_card(grid, 2, 1, "Tipo de Memória", "DDR4 / Virtual")

        return box

    def _create_stat_card(self, grid, col, row, label, val):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.get_style_context().add_class("stat-card")

        lbl_l = Gtk.Label(label=label)
        lbl_l.get_style_context().add_class("stat-label")
        lbl_l.set_xalign(0)
        card.pack_start(lbl_l, False, False, 0)

        lbl_v = Gtk.Label(label=val)
        lbl_v.get_style_context().add_class("stat-val")
        lbl_v.set_xalign(0)
        card.pack_start(lbl_v, False, False, 0)

        grid.attach(card, col, row, 1, 1)
        return lbl_v

    def _build_details_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scroll, True, True, 0)

        # ListStore: PID(int), Name(str), Status(str), User(str), CPU(float), CPU Text(str), RAM(GObject.TYPE_INT64), RAM Text(str), Command(str)
        self.details_store = Gtk.ListStore(int, str, str, str, float, str, GObject.TYPE_INT64, str, str)
        self.details_tree = Gtk.TreeView(model=self.details_store)
        self.details_tree.set_enable_search(False)
        self.details_tree.connect("button-press-event", self.on_proc_tree_button_press)
        self.details_tree.connect("row-activated", self.on_proc_row_double_click)

        sel = self.details_tree.get_selection()
        sel.set_mode(Gtk.SelectionMode.SINGLE)
        sel.connect("changed", self.on_details_selection_changed)

        cols = [
            ("PID", 0, 70, True),
            ("Nome", 1, 160, False),
            ("Status", 2, 90, False),
            ("Usuário", 3, 90, False),
            ("CPU %", 5, 80, True),
            ("Memória", 7, 100, True),
            ("Linha de Comando", 8, 320, False)
        ]

        for title, col_id, width, align_right in cols:
            renderer = Gtk.CellRendererText()
            if align_right:
                renderer.set_property("xalign", 1.0)
            col = Gtk.TreeViewColumn(title, renderer, text=col_id)
            col.set_min_width(width)
            col.set_resizable(True)
            col.set_sort_column_id(col_id)
            self.details_tree.append_column(col)

        scroll.add(self.details_tree)
        return box

    def on_search_changed(self, entry):
        self.search_query = entry.get_text().strip().lower()
        self.tree_initialized = False
        self.details_initialized = False
        self.on_timer_tick()

    def on_proc_selection_changed(self, selection):
        model, tree_iter = selection.get_selected()
        if tree_iter:
            pid = model.get_value(tree_iter, 7)
            is_group = model.get_value(tree_iter, 9)
            if not is_group and pid > 0:
                self.selected_pid = pid
                path = model.get_path(tree_iter)
                self.selected_row_ref = Gtk.TreeRowReference.new(model, path)
                
                # Check if this row is a parent with child subprocesses
                child_iter = model.iter_children(tree_iter)
                if child_iter:
                    pids = [pid]
                    while child_iter:
                        c_pid = model.get_value(child_iter, 7)
                        if c_pid > 0:
                            pids.append(c_pid)
                        child_iter = model.iter_next(child_iter)
                    self.selected_pids = pids
                else:
                    self.selected_pids = [pid]
                self.btn_kill.set_sensitive(True)
                self.btn_props.set_sensitive(True)
                return
        self.selected_pid = None
        self.selected_pids = []
        self.selected_row_ref = None
        self.btn_kill.set_sensitive(False)
        self.btn_props.set_sensitive(False)

    def on_details_selection_changed(self, selection):
        model, tree_iter = selection.get_selected()
        if tree_iter:
            pid = model.get_value(tree_iter, 0)
            if pid > 0:
                self.selected_pid = pid
                self.selected_pids = [pid]
                self.btn_kill.set_sensitive(True)
                self.btn_props.set_sensitive(True)
                return
        self.selected_pid = None
        self.selected_pids = []
        self.btn_kill.set_sensitive(False)
        self.btn_props.set_sensitive(False)

    def on_proc_row_double_click(self, tree, path, column):
        model = tree.get_model()
        tree_iter = model.get_iter(path)
        pid = model.get_value(tree_iter, 7 if isinstance(model, Gtk.TreeStore) else 0)
        if pid > 0:
            self.show_properties(pid)

    def _is_proc_row_selectable(self, selection, model, path, path_currently_selected, data):
        try:
            if isinstance(model, Gtk.TreeStore):
                tree_iter = model.get_iter(path)
                is_group = model.get_value(tree_iter, 9)
                return not is_group
            return True
        except:
            return True

    def on_proc_tree_button_press(self, widget, event):
        if event.button == 3: # Right click
            try:
                bx, by = widget.convert_widget_to_bin_window_coords(int(event.x), int(event.y))
            except:
                bx, by = int(event.x), int(event.y)
            path_info = widget.get_path_at_pos(bx, by)
            if path_info:
                path, col, _, _ = path_info
                model = widget.get_model()
                titer = model.get_iter(path)
                is_tree = isinstance(model, Gtk.TreeStore)
                is_group = model.get_value(titer, 9) if is_tree else False
                if not is_group:
                    pid = model.get_value(titer, 7 if is_tree else 0)
                    if pid > 0:
                        self.selected_pid = pid
                        self.selected_pids = [pid]
                        widget.get_selection().select_path(path)
                        self.btn_kill.set_sensitive(True)
                        self.btn_props.set_sensitive(True)
                        self.show_context_menu(event)
                        return True
        return False

    def show_context_menu(self, event):
        if not self.selected_pid:
            return
        menu = Gtk.Menu()

        # Finalizar tarefa
        item_kill = Gtk.MenuItem(label="Finalizar tarefa (Del)")
        item_kill.connect("activate", lambda m: self.on_end_task_clicked(None))
        menu.append(item_kill)

        # Forçar finalização (SIGKILL)
        item_force = Gtk.MenuItem(label="Forçar finalização (SIGKILL)")
        item_force.connect("activate", lambda m: self.force_kill_selected())
        menu.append(item_force)

        # Finalizar árvore de processos
        item_tree = Gtk.MenuItem(label="Finalizar árvore de processos")
        item_tree.connect("activate", lambda m: self.kill_process_tree(self.selected_pid))
        menu.append(item_tree)

        menu.append(Gtk.SeparatorMenuItem())

        # Suspender / Retomar Processo
        p_info = self.collector.last_procs_by_pid.get(self.selected_pid, {})
        is_paused = p_info.get("state_raw") == 'T'
        pause_label = "Retomar processo (SIGCONT)" if is_paused else "Suspender processo (SIGSTOP)"
        item_pause = Gtk.MenuItem(label=pause_label)
        item_pause.connect("activate", lambda m: self.toggle_pause_process(self.selected_pid))
        menu.append(item_pause)

        # Definir Prioridade (Nice)
        item_prio = Gtk.MenuItem(label="Definir prioridade")
        prio_menu = Gtk.Menu()
        item_prio.set_submenu(prio_menu)

        current_nice = p_info.get("nice", 0)
        priorities = [
            ("Alta (-10)", -10),
            ("Acima do Normal (-5)", -5),
            ("Normal (0)", 0),
            ("Abaixo do Normal (5)", 5),
            ("Baixa (10)", 10),
        ]
        for p_label, p_val in priorities:
            display_label = f"✓ {p_label}" if current_nice == p_val else f"   {p_label}"
            sub_item = Gtk.MenuItem(label=display_label)
            sub_item.connect("activate", lambda m, val=p_val: self.set_proc_priority(self.selected_pid, val))
            prio_menu.append(sub_item)
        menu.append(item_prio)

        menu.append(Gtk.SeparatorMenuItem())

        # Abrir local do arquivo
        item_open = Gtk.MenuItem(label="Abrir local do arquivo")
        item_open.connect("activate", lambda m: self.open_file_location(self.selected_pid))
        menu.append(item_open)

        # Submenu Copiar
        item_copy = Gtk.MenuItem(label="Copiar")
        copy_menu = Gtk.Menu()
        item_copy.set_submenu(copy_menu)

        sub_copy_name = Gtk.MenuItem(label="Copiar Nome")
        sub_copy_name.connect("activate", lambda m: self.copy_proc_info(self.selected_pid, "name"))
        copy_menu.append(sub_copy_name)

        sub_copy_pid = Gtk.MenuItem(label="Copiar PID")
        sub_copy_pid.connect("activate", lambda m: self.copy_proc_info(self.selected_pid, "pid"))
        copy_menu.append(sub_copy_pid)

        sub_copy_cmd = Gtk.MenuItem(label="Copiar Linha de Comando")
        sub_copy_cmd.connect("activate", lambda m: self.copy_proc_info(self.selected_pid, "cmdline"))
        copy_menu.append(sub_copy_cmd)

        sub_copy_path = Gtk.MenuItem(label="Copiar Caminho do Executável")
        sub_copy_path.connect("activate", lambda m: self.copy_proc_info(self.selected_pid, "exe"))
        copy_menu.append(sub_copy_path)
        menu.append(item_copy)

        menu.append(Gtk.SeparatorMenuItem())

        # Propriedades e Análise
        item_props = Gtk.MenuItem(label="Propriedades e Análise...")
        item_props.connect("activate", lambda m: self.show_properties(self.selected_pid))
        menu.append(item_props)

        menu.show_all()
        menu.popup(None, None, None, None, event.button if event else 0, Gtk.get_current_event_time())

    def on_end_task_clicked(self, btn):
        if not self.selected_pid and not self.selected_pids:
            return
        pids_to_kill = list(self.selected_pids) if self.selected_pids else [self.selected_pid]

        # Prevent accidental desktop kill
        critical = {"xfwm4", "xfce4-panel", "xfce4-session", "selkies", "sshd"}
        for p in pids_to_kill:
            p_info = self.collector.last_procs_by_pid.get(p, {})
            comm = p_info.get("comm", "")
            if comm in critical:
                dlg = Gtk.MessageDialog(
                    transient_for=self,
                    flags=Gtk.DialogFlags.MODAL,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK_CANCEL,
                    text="Aviso de Processo do Sistema"
                )
                dlg.format_secondary_text(
                    f"O processo '{comm}' (PID {p}) é essencial para o ambiente de trabalho.\n"
                    f"Finalizá-lo fechará sua sessão gráfica.\n\nDeseja realmente continuar?"
                )
                resp = dlg.run()
                dlg.destroy()
                if resp != Gtk.ResponseType.OK:
                    return

        for p in pids_to_kill:
            p_info = self.collector.last_procs_by_pid.get(p, {})
            if p_info.get("state_raw") == 'Z':
                # Zombie process: directly killing it does nothing in Linux.
                # Killing its parent (PPID) causes PID 1 to adopt and reap it!
                ppid = p_info.get("ppid", 0)
                if ppid > 1:
                    self.terminate_pid(ppid, signal.SIGTERM, silent=True)
                    time.sleep(0.05)
                    self.terminate_pid(ppid, signal.SIGKILL, silent=True)
            else:
                self.terminate_pid(p, signal.SIGTERM, silent=True)
        self.tree_initialized = False
        self.details_initialized = False
        self.on_timer_tick()

    def force_kill_selected(self):
        if not self.selected_pid and not self.selected_pids:
            return
        pids_to_kill = list(self.selected_pids) if self.selected_pids else [self.selected_pid]
        for p in pids_to_kill:
            p_info = self.collector.last_procs_by_pid.get(p, {})
            if p_info.get("state_raw") == 'Z':
                ppid = p_info.get("ppid", 0)
                if ppid > 1:
                    self.terminate_pid(ppid, signal.SIGKILL, silent=True)
            else:
                self.terminate_pid(p, signal.SIGKILL, silent=True)
        self.tree_initialized = False
        self.details_initialized = False
        self.on_timer_tick()

    def kill_process_tree(self, root_pid):
        descendants = []
        def _find_children(parent_pid):
            for p in self.collector.last_procs:
                if p['ppid'] == parent_pid:
                    descendants.append(p['pid'])
                    _find_children(p['pid'])
        _find_children(root_pid)
        for p in reversed(descendants):
            self.terminate_pid(p, signal.SIGKILL, silent=True)
        self.terminate_pid(root_pid, signal.SIGKILL, silent=True)
        self.on_timer_tick()

    def toggle_pause_process(self, pid):
        p_info = self.collector.last_procs_by_pid.get(pid, {})
        is_paused = p_info.get("state_raw") == 'T'
        sig = signal.SIGCONT if is_paused else signal.SIGSTOP
        try:
            os.kill(pid, sig)
        except Exception as e:
            self.show_error_dialog(f"Erro ao alterar estado do processo {pid}", str(e))
        self.on_timer_tick()

    def set_proc_priority(self, pid, nice_val):
        try:
            os.setpriority(os.PRIO_PROCESS, pid, nice_val)
        except PermissionError:
            subprocess.run(["sudo", "renice", "-n", str(nice_val), "-p", str(pid)], check=False)
        except Exception as e:
            self.show_error_dialog("Erro ao definir prioridade", str(e))
        self.on_timer_tick()

    def terminate_pid(self, pid, sig=signal.SIGTERM, silent=False):
        try:
            os.kill(pid, sig)
        except Exception as e:
            if not silent:
                self.show_error_dialog("Erro ao finalizar tarefa", f"Não foi possível finalizar o processo {pid}:\n{e}")
        if not silent:
            self.on_timer_tick()

    def open_file_location(self, pid):
        try:
            exe_path = os.readlink(f"/proc/{pid}/exe")
            folder = os.path.dirname(exe_path)
            subprocess.Popen(["thunar", folder])
        except Exception as e:
            self.show_error_dialog("Local do arquivo", f"Não foi possível acessar o executável do processo {pid}:\n{e}")

    def copy_to_clipboard(self, text):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()

    def copy_proc_info(self, pid, field_type):
        p_info = self.collector.last_procs_by_pid.get(pid, {})
        if field_type == "name":
            self.copy_to_clipboard(p_info.get("friendly_name", p_info.get("comm", "")))
        elif field_type == "pid":
            self.copy_to_clipboard(str(pid))
        elif field_type == "cmdline":
            self.copy_to_clipboard(p_info.get("cmdline", ""))
        elif field_type == "exe":
            try:
                exe = os.readlink(f"/proc/{pid}/exe")
                self.copy_to_clipboard(exe)
            except:
                pass

    def show_properties(self, pid):
        if not pid or pid <= 0:
            return
        p_info = self.collector.last_procs_by_pid.get(pid, {})
        fn = p_info.get("friendly_name", str(pid))
        icon = p_info.get("icon_name", "application-x-executable")
        dlg = ProcessPropertiesDialog(self, pid, fn, icon)
        dlg.run()
        dlg.destroy()

    def show_error_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def on_run_new_task(self, btn):
        dialog = Gtk.Dialog(title="Criar nova tarefa", transient_for=self, flags=Gtk.DialogFlags.MODAL)
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("OK", Gtk.ResponseType.OK)
        dialog.set_default_size(420, 160)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)

        lbl = Gtk.Label(label="Digite o nome de um programa ou comando para abri-lo:")
        lbl.set_xalign(0)
        box.pack_start(lbl, False, False, 0)

        entry = Gtk.Entry()
        entry.set_activates_default(True)
        box.pack_start(entry, False, False, 0)

        chk_admin = Gtk.CheckButton(label="Criar esta tarefa com privilégios de administrador")
        box.pack_start(chk_admin, False, False, 0)

        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show_all()

        resp = dialog.run()
        cmd_text = entry.get_text().strip()
        is_admin = chk_admin.get_active()
        dialog.destroy()

        if resp == Gtk.ResponseType.OK and cmd_text:
            try:
                cmd_args = cmd_text.split()
                if is_admin:
                    cmd_args = ["sudo"] + cmd_args
                subprocess.Popen(cmd_args)
            except Exception as e:
                self.show_error_dialog("Erro ao executar comando", str(e))

    def on_timer_tick(self):
        data = self.collector.collect()

        # Update Top Metric Chips
        self.lbl_metric_cpu.set_text(f"{data['global_cpu']:.0f}%")
        used_gb = data['used_mem_kb'] / 1048576.0
        total_gb = data['total_mem_kb'] / 1048576.0
        self.lbl_metric_mem.set_text(f"{used_gb:.1f} GB ({data['mem_pct']:.0f}%)")
        self.lbl_metric_proc.set_text(str(data['proc_count']))

        s = int(data['uptime_s'])
        d = s // 86400
        h = (s % 86400) // 3600
        m = (s % 3600) // 60
        sec = s % 60
        uptime_str = f"{d}d {h:02d}:{m:02d}:{sec:02d}" if d > 0 else f"{h:02d}:{m:02d}:{sec:02d}"
        self.lbl_metric_uptime.set_text(uptime_str)

        # Update Performance View
        self.lbl_side_cpu_val.set_text(f"{data['global_cpu']:.0f}%  2.50 GHz")
        self.lbl_side_mem_val.set_text(f"{used_gb:.1f}/{total_gb:.1f} GB ({data['mem_pct']:.0f}%)")
        self.lbl_cpu_big_val.set_text(f"{data['global_cpu']:.0f} %")
        self.lbl_mem_big_val.set_text(f"{used_gb:.1f} GB ({data['mem_pct']:.0f}%)")
        self.lbl_mem_sub.set_text(f"{total_gb:.1f} GB DDR4")

        self.stat_cpu_util.set_text(f"{data['global_cpu']:.1f}%")
        self.stat_cpu_procs.set_text(str(data['proc_count']))
        self.stat_cpu_threads.set_text(str(data['thread_count']))
        self.stat_cpu_uptime.set_text(uptime_str)

        self.stat_mem_used.set_text(f"{used_gb:.2f} GB")
        avail_gb = data['avail_mem_kb'] / 1048576.0
        cached_gb = data['cached_mem_kb'] / 1048576.0
        self.stat_mem_avail.set_text(f"{avail_gb:.2f} GB")
        self.stat_mem_cached.set_text(f"{cached_gb:.2f} GB")
        self.stat_mem_total.set_text(f"{total_gb:.2f} GB")
        self.stat_mem_pct.set_text(f"{data['mem_pct']:.1f}%")

        # Redraw Cairo charts
        self.mini_chart_cpu.queue_draw()
        self.mini_chart_mem.queue_draw()
        self.big_chart_cpu.queue_draw()
        self.big_chart_mem.queue_draw()

        # Update Tab 1 (Processos Tree) - In-place with persistent selection
        self._update_process_tree(data['procs'])

        # Update Tab 3 (Detalhes List) - In-place with persistent selection
        self._update_details_list(data['procs'])

        return True

    def _sort_procs_list(self, plist):
        """Stable sorting based on user selection or alphabetical by default."""
        k = self.proc_sort_column
        rev = (self.proc_sort_order == Gtk.SortType.DESCENDING)
        if k == "cpu":
            return sorted(plist, key=lambda x: (x['cpu'], x['rss']), reverse=rev)
        elif k == "mem":
            return sorted(plist, key=lambda x: (x['rss'], x['cpu']), reverse=rev)
        elif k == "pid":
            return sorted(plist, key=lambda x: x['pid'], reverse=rev)
        elif k == "user":
            return sorted(plist, key=lambda x: (x['user'], x['friendly_name'].lower()), reverse=rev)
        elif k == "status":
            return sorted(plist, key=lambda x: (x['state_str'], x['friendly_name'].lower()), reverse=rev)
        # Default: Alphabetical by Name (100% stable!)
        return sorted(plist, key=lambda x: x['friendly_name'].lower(), reverse=rev)

    def _update_process_tree(self, procs):
        """Updates the tree in-place without clearing, ensuring zero jumping and preserving selection."""
        # 1. Filter procs
        q = self.search_query
        filtered = []
        for p in procs:
            if q:
                if (q not in p['friendly_name'].lower() and
                    q not in p['comm'].lower() and
                    q not in str(p['pid'])):
                    continue
            filtered.append(p)

        # 2. If tree not initialized or search changed: full populate
        if not self.tree_initialized:
            self._full_populate_proc_tree(filtered)
            self.tree_initialized = True
            return

        # 3. Fast In-Place Reconciliation
        curr_pids = {p['pid']: p for p in filtered}

        # If processes were added or removed, re-populate cleanly
        if set(curr_pids.keys()) != set(self.proc_row_refs.keys()):
            self._full_populate_proc_tree(filtered)
            if self.selected_pid and self.selected_pid in self.proc_row_refs:
                ref = self.proc_row_refs[self.selected_pid]
                if ref and ref.valid():
                    self.proc_tree.get_selection().select_path(ref.get_path())
                    self.btn_kill.set_sensitive(True)
                    self.btn_props.set_sensitive(True)
            return

        # Update existing processes in-place (zero movement, zero flicker)
        for pid, p in curr_pids.items():
            ref = self.proc_row_refs.get(pid)
            if ref and ref.valid():
                path = ref.get_path()
                titer = self.proc_store.get_iter(path)
                cpu_markup = self._format_cpu_markup(p['cpu'])
                mem_str = self._format_mem(p['rss'])
                status_markup = self._format_status_markup(p['state_raw'])
                self.proc_store.set_value(titer, 2, status_markup)
                self.proc_store.set_value(titer, 3, p['cpu'])
                self.proc_store.set_value(titer, 4, cpu_markup)
                self.proc_store.set_value(titer, 5, p['rss'])
                self.proc_store.set_value(titer, 6, mem_str)

        # Update group headers (Aplicativos total count, Background total count)
        if hasattr(self, "hdr_apps_ref") and self.hdr_apps_ref.valid():
            path = self.hdr_apps_ref.get_path()
            apps_count = sum(1 for p in filtered if p['is_app'])
            self.proc_store.set_value(self.proc_store.get_iter(path), 1, f"<b>Aplicativos ({apps_count})</b>")

        if hasattr(self, "hdr_bg_ref") and self.hdr_bg_ref.valid():
            path = self.hdr_bg_ref.get_path()
            bg_count = sum(1 for p in filtered if not p['is_app'])
            self.proc_store.set_value(self.proc_store.get_iter(path), 1, f"<b>Processos em segundo plano ({bg_count})</b>")

        # Re-assert active selection on the selected PID so it never vanishes
        if self.selected_pid and self.selected_pid in self.proc_row_refs:
            ref = self.proc_row_refs[self.selected_pid]
            if ref and ref.valid():
                self.proc_tree.get_selection().select_path(ref.get_path())
                self.btn_kill.set_sensitive(True)
                self.btn_props.set_sensitive(True)

    def _full_populate_proc_tree(self, filtered):
        self.proc_store.clear()
        self.proc_row_refs.clear()
        self.app_group_refs.clear()

        apps = [p for p in filtered if p['is_app']]
        bg = [p for p in filtered if not p['is_app']]

        # Sort lists
        apps_sorted = self._sort_procs_list(apps)
        bg_sorted = self._sort_procs_list(bg)

        # Root Node 1: Aplicativos
        hdr_apps = self.proc_store.append(None, [
            "applications-other",
            f"<b>Aplicativos ({len(apps_sorted)})</b>",
            "", 0.0, "", 0, "", 0, "", True, "0_apps", "hdr:apps"
        ])
        self.hdr_apps_ref = Gtk.TreeRowReference.new(self.proc_store, self.proc_store.get_path(hdr_apps))

        # Group apps by friendly_name
        app_groups = {}
        for p in apps_sorted:
            fn = p['friendly_name']
            if fn not in app_groups:
                app_groups[fn] = []
            app_groups[fn].append(p)

        for fn, group_procs in app_groups.items():
            if len(group_procs) == 1:
                p = group_procs[0]
                titer = self._append_proc_row(hdr_apps, p)
                ref = Gtk.TreeRowReference.new(self.proc_store, self.proc_store.get_path(titer))
                self.proc_row_refs[p['pid']] = ref
            else:
                # Multi-process parent group (e.g. Chrome tabs)
                total_cpu = sum(x['cpu'] for x in group_procs)
                total_rss = sum(x['rss'] for x in group_procs)
                main_proc = min(group_procs, key=lambda x: x['pid'])
                name_markup = f"<b>{fn}</b> <span size='small' color='#888888'>({len(group_procs)})</span>"
                status_markup = self._format_status_markup(main_proc['state_raw'])
                parent_iter = self.proc_store.append(hdr_apps, [
                    main_proc['icon_name'],
                    name_markup,
                    status_markup,
                    total_cpu,
                    self._format_cpu_markup(total_cpu),
                    total_rss,
                    self._format_mem(total_rss),
                    main_proc['pid'],
                    main_proc['user'],
                    False,
                    f"0_{main_proc['pid']}",
                    f"grp:{fn}"
                ])
                self.proc_row_refs[main_proc['pid']] = Gtk.TreeRowReference.new(self.proc_store, self.proc_store.get_path(parent_iter))

                for cp in group_procs:
                    c_name = f"<span size='small' color='#cccccc'>{cp['comm']}</span>"
                    c_iter = self.proc_store.append(parent_iter, [
                        cp['icon_name'],
                        c_name,
                        self._format_status_markup(cp['state_raw']),
                        cp['cpu'],
                        self._format_cpu_markup(cp['cpu']),
                        cp['rss'],
                        self._format_mem(cp['rss']),
                        cp['pid'],
                        cp['user'],
                        False,
                        f"0_{cp['pid']}",
                        str(cp['pid'])
                    ])
                    self.proc_row_refs[cp['pid']] = Gtk.TreeRowReference.new(self.proc_store, self.proc_store.get_path(c_iter))

        # Root Node 2: Processos em segundo plano
        hdr_bg = self.proc_store.append(None, [
            "applications-system",
            f"<b>Processos em segundo plano ({len(bg_sorted)})</b>",
            "", 0.0, "", 0, "", 0, "", True, "1_bg", "hdr:bg"
        ])
        self.hdr_bg_ref = Gtk.TreeRowReference.new(self.proc_store, self.proc_store.get_path(hdr_bg))

        for p in bg_sorted:
            titer = self._append_proc_row(hdr_bg, p)
            ref = Gtk.TreeRowReference.new(self.proc_store, self.proc_store.get_path(titer))
            self.proc_row_refs[p['pid']] = ref

        # Expand root headers
        self.proc_tree.expand_row(self.proc_store.get_path(hdr_apps), False)
        self.proc_tree.expand_row(self.proc_store.get_path(hdr_bg), False)

        # Restore expanded child rows if previously expanded
        for p_str in list(self.expanded_paths):
            try:
                self.proc_tree.expand_row(Gtk.TreePath.new_from_string(p_str), False)
            except:
                pass

    def _append_proc_row(self, parent_iter, p):
        cpu_markup = self._format_cpu_markup(p['cpu'])
        mem_str = self._format_mem(p['rss'])
        status_markup = self._format_status_markup(p['state_raw'])
        name_markup = f"<b>{GLib.markup_escape_text(p['friendly_name'])}</b>" if p['is_app'] else GLib.markup_escape_text(p['comm'])
        return self.proc_store.append(parent_iter, [
            p['icon_name'],
            name_markup,
            status_markup,
            p['cpu'],
            cpu_markup,
            p['rss'],
            mem_str,
            p['pid'],
            p['user'],
            False,
            f"{p['pid']}",
            str(p['pid'])
        ])

    def _insert_single_proc_row(self, p):
        parent_ref = self.hdr_apps_ref if p['is_app'] else self.hdr_bg_ref
        if parent_ref and parent_ref.valid():
            parent_iter = self.proc_store.get_iter(parent_ref.get_path())
            titer = self._append_proc_row(parent_iter, p)
            ref = Gtk.TreeRowReference.new(self.proc_store, self.proc_store.get_path(titer))
            self.proc_row_refs[p['pid']] = ref

    def _update_details_list(self, procs):
        """Updates the Tab 3 details list in-place without clearing."""
        q = self.search_query
        filtered = []
        for p in procs:
            if q:
                if (q not in p['comm'].lower() and
                    q not in p['cmdline'].lower() and
                    q not in str(p['pid'])):
                    continue
            filtered.append(p)

        if not self.details_initialized:
            self.details_store.clear()
            self.details_row_refs.clear()
            for p in filtered:
                cpu_str = f"{p['cpu']:.1f} %" if p['cpu'] > 0.05 else "0.0 %"
                mem_str = self._format_mem(p['rss'])
                titer = self.details_store.append([
                    p['pid'],
                    p['comm'],
                    p['state_str'],
                    p['user'],
                    p['cpu'],
                    cpu_str,
                    p['rss'],
                    mem_str,
                    p['cmdline']
                ])
                ref = Gtk.TreeRowReference.new(self.details_store, self.details_store.get_path(titer))
                self.details_row_refs[p['pid']] = ref
            self.details_initialized = True
            return

        # Fast in-place updates for details
        curr_pids = {p['pid']: p for p in filtered}
        dead_pids = [pid for pid in self.details_row_refs if pid not in curr_pids]
        for pid in dead_pids:
            ref = self.details_row_refs.pop(pid, None)
            if ref and ref.valid():
                self.details_store.remove(self.details_store.get_iter(ref.get_path()))

        for pid, p in curr_pids.items():
            if pid in self.details_row_refs:
                ref = self.details_row_refs[pid]
                if ref and ref.valid():
                    titer = self.details_store.get_iter(ref.get_path())
                    cpu_str = f"{p['cpu']:.1f} %" if p['cpu'] > 0.05 else "0.0 %"
                    mem_str = self._format_mem(p['rss'])
                    self.details_store.set_value(titer, 2, p['state_str'])
                    self.details_store.set_value(titer, 4, p['cpu'])
                    self.details_store.set_value(titer, 5, cpu_str)
                    self.details_store.set_value(titer, 6, p['rss'])
                    self.details_store.set_value(titer, 7, mem_str)
            else:
                cpu_str = f"{p['cpu']:.1f} %" if p['cpu'] > 0.05 else "0.0 %"
                mem_str = self._format_mem(p['rss'])
                titer = self.details_store.append([
                    p['pid'],
                    p['comm'],
                    p['state_str'],
                    p['user'],
                    p['cpu'],
                    cpu_str,
                    p['rss'],
                    mem_str,
                    p['cmdline']
                ])
                self.details_row_refs[pid] = Gtk.TreeRowReference.new(self.details_store, self.details_store.get_path(titer))

    def _format_status_markup(self, state_raw):
        if state_raw == 'T':
            return "<span color='#f59e0b'>●</span> Suspenso"
        elif state_raw == 'Z':
            return "<span color='#ef4444'>●</span> Zumbi"
        elif state_raw == 'D':
            return "<span color='#38bdf8'>●</span> Aguardando"
        return "<span color='#00cc6a'>●</span> Executando"

    def _format_cpu_markup(self, cpu_val):
        if cpu_val < 0.05:
            return "<span color='#888888'>0.0 %</span>"
        elif cpu_val > 25.0:
            return f"<span color='#ff5252' weight='bold'>{cpu_val:.1f} %</span>"
        elif cpu_val > 10.0:
            return f"<span color='#ffa726' weight='bold'>{cpu_val:.1f} %</span>"
        return f"<span color='#ffffff'>{cpu_val:.1f} %</span>"

    def _format_mem(self, b):
        mb = b / 1048576.0
        if mb >= 1024.0:
            return f"{mb/1024.0:.2f} GB"
        return f"{mb:.1f} MB"

def main():
    initial = "processos"
    arg_str = " ".join(sys.argv).lower()
    if "perf" in arg_str or "-p" in arg_str:
        initial = "desempenho"
    elif "detail" in arg_str or "-d" in arg_str:
        initial = "detalhes"

    app = WindowsTaskManager(initial_tab=initial)
    app.connect("destroy", Gtk.main_quit)
    app.show_all()

    if initial != "processos":
        if initial == "desempenho":
            app._switch_tab("desempenho", app.btn_nav_perf)
        elif initial == "detalhes":
            app._switch_tab("detalhes", app.btn_nav_details)

    Gtk.main()

if __name__ == "__main__":
    main()
