#!/usr/bin/env python3
# =============================================================================
# win_language.py – Seletor de Idioma do Windows 11 para Cloud Desktop
# Permite alterar o idioma a qualquer momento e aplica imediatamente.
# =============================================================================
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os, sys, subprocess, time

HOME = os.path.expanduser('~')
PREF_FILE = '/config/.language_preference'

LANGUAGES = [
    ('pt_BR', '🇧🇷', 'Português (Brasil)'),
    ('en_US', '🇺🇸', 'English (United States)'),
    ('es_ES', '🇪🇸', 'Español (España)'),
    ('de_DE', '🇩🇪', 'Deutsch (Deutschland)'),
    ('fr_FR', '🇫🇷', 'Français (France)'),
    ('it_IT', '🇮🇹', 'Italiano (Italia)'),
]

UI_TEXTS = {
    'pt_BR': {
        'title': 'Idioma do Sistema',
        'sub': 'Selecione o idioma de sua preferência para o ambiente de trabalho:',
        'apply_btn': 'Salvar e Reiniciar Sessão',
        'cancel_btn': 'Cancelar',
        'info': 'A sessão será reiniciada para aplicar as traduções em 100% dos menus e janelas.',
        'restarting': 'Aplicando novo idioma e reiniciando...',
    },
    'en_US': {
        'title': 'System Language',
        'sub': 'Select your preferred language for the desktop environment:',
        'apply_btn': 'Save and Restart Session',
        'cancel_btn': 'Cancel',
        'info': 'The session will restart to apply translations to all menus and windows.',
        'restarting': 'Applying new language and restarting...',
    },
    'es_ES': {
        'title': 'Idioma del Sistema',
        'sub': 'Seleccione su idioma preferido para el entorno de escritorio:',
        'apply_btn': 'Guardar y Reiniciar Sesión',
        'cancel_btn': 'Cancelar',
        'info': 'La sesión se reiniciará para aplicar las traducciones a todos los menús y ventanas.',
        'restarting': 'Aplicando nuevo idioma y reiniciando...',
    },
    'de_DE': {
        'title': 'Systemsprache',
        'sub': 'Wählen Sie Ihre bevorzugte Sprache für die Desktop-Umgebung:',
        'apply_btn': 'Speichern und Sitzung neu starten',
        'cancel_btn': 'Abbrechen',
        'info': 'Die Sitzung wird neu gestartet, um die Übersetzungen auf alle Menüs anzuwenden.',
        'restarting': 'Neue Sprache wird angewendet und neu gestartet...',
    },
    'fr_FR': {
        'title': 'Langue du système',
        'sub': 'Sélectionnez votre langue préférée pour l\'environnement de bureau :',
        'apply_btn': 'Enregistrer et redémarrer la session',
        'cancel_btn': 'Annuler',
        'info': 'La session va redémarrer pour appliquer les traductions à tous les menus et fenêtres.',
        'restarting': 'Application de la nouvelle langue et redémarrage...',
    },
    'it_IT': {
        'title': 'Lingua del sistema',
        'sub': 'Seleziona la tua lingua preferita per l\'ambiente desktop:',
        'apply_btn': 'Salva e Riavvia Sessione',
        'cancel_btn': 'Annulla',
        'info': 'La sessione verrà riavviata per applicare le traduzioni a tutti i menu e finestre.',
        'restarting': 'Applicazione della nuova lingua e riavvio...',
    },
}

def get_current_lang():
    if os.path.exists(PREF_FILE):
        try:
            with open(PREF_FILE) as f:
                c = f.read().strip()
                if c in [l[0] for l in LANGUAGES]:
                    return c
        except Exception:
            pass
    env = os.environ.get('LANG', 'pt_BR.UTF-8').split('.')[0]
    return env if env in [l[0] for l in LANGUAGES] else 'pt_BR'

class LanguageApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Idioma do Sistema / System Language")
        self.current_code = get_current_lang()
        self.ui = UI_TEXTS.get(self.current_code, UI_TEXTS['en_US'])

        self.set_default_size(460, 380)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        # Tema escuro estilo Windows 11
        css = b"""
        window { background-color: #202020; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
        .card { background-color: #2b2b2b; border-radius: 8px; padding: 20px; border: 1px solid #383838; }
        .title { font-size: 18px; font-weight: bold; color: #ffffff; }
        .sub { font-size: 13px; color: #cccccc; margin-bottom: 12px; }
        .info { font-size: 11px; color: #999999; }
        .btn-apply { background-color: #0078d4; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 10px 18px; border: none; }
        .btn-apply:hover { background-color: #1084d8; }
        .btn-cancel { background-color: #383838; color: #e0e0e0; border-radius: 4px; padding: 10px 16px; border: none; }
        .btn-cancel:hover { background-color: #444444; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_margin_top(16)
        outer.set_margin_bottom(16)
        outer.set_margin_start(16)
        outer.set_margin_end(16)
        self.add(outer)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.get_style_context().add_class('card')
        outer.pack_start(card, True, True, 0)

        lbl_title = Gtk.Label(label=f"🌐  {self.ui['title']}")
        lbl_title.get_style_context().add_class('title')
        lbl_title.set_halign(Gtk.Align.START)
        card.pack_start(lbl_title, False, False, 0)

        lbl_sub = Gtk.Label(label=self.ui['sub'])
        lbl_sub.get_style_context().add_class('sub')
        lbl_sub.set_halign(Gtk.Align.START)
        lbl_sub.set_line_wrap(True)
        card.pack_start(lbl_sub, False, False, 0)

        # Lista de seleção
        self.radios = []
        first_radio = None
        for code, flag, name in LANGUAGES:
            if first_radio is None:
                r = Gtk.RadioButton.new_with_label(None, f"{flag}  {name}")
                first_radio = r
            else:
                r = Gtk.RadioButton.new_with_label_from_widget(first_radio, f"{flag}  {name}")
            if code == self.current_code:
                r.set_active(True)
            r.code = code
            card.pack_start(r, False, False, 2)
            self.radios.append(r)

        lbl_info = Gtk.Label(label=f"ℹ️ {self.ui['info']}")
        lbl_info.get_style_context().add_class('info')
        lbl_info.set_line_wrap(True)
        lbl_info.set_halign(Gtk.Align.START)
        card.pack_start(lbl_info, False, False, 6)

        # Botões
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bbox.set_halign(Gtk.Align.END)
        outer.pack_start(bbox, False, False, 0)

        btn_cancel = Gtk.Button(label=self.ui['cancel_btn'])
        btn_cancel.get_style_context().add_class('btn-cancel')
        btn_cancel.connect('clicked', lambda w: Gtk.main_quit())
        bbox.pack_start(btn_cancel, False, False, 0)

        self.btn_apply = Gtk.Button(label=f"✓  {self.ui['apply_btn']}")
        self.btn_apply.get_style_context().add_class('btn-apply')
        self.btn_apply.connect('clicked', self.on_apply)
        bbox.pack_start(self.btn_apply, False, False, 0)

        self.connect('destroy', Gtk.main_quit)
        self.show_all()

    def on_apply(self, widget):
        selected_code = self.current_code
        for r in self.radios:
            if r.get_active():
                selected_code = r.code
                break

        # Grava nas duas localizações
        for path in [PREF_FILE, os.path.join(HOME, '.language_preference')]:
            try:
                with open(path, 'w') as f:
                    f.write(selected_code)
            except Exception:
                pass

        locale_str = f"{selected_code}.UTF-8"
        lang_short = selected_code.split('_')[0]
        env_content = f"LANG={locale_str}\nLANGUAGE={selected_code}:{lang_short}\nLC_ALL={locale_str}\n"

        try:
            with open('/tmp/.lang_env', 'w') as f:
                f.write(env_content)
            subprocess.run(['sudo', 'cp', '/tmp/.lang_env', '/etc/environment'], check=False)
            subprocess.run(['sudo', 'cp', '/tmp/.lang_env', '/etc/default/locale'], check=False)
        except Exception:
            pass

        try:
            subprocess.run(['sudo', 'locale-gen', locale_str], check=False)
        except Exception:
            pass

        self.btn_apply.set_sensitive(False)
        self.btn_apply.set_label("⏳ Aplicando...")

        # Dispara reinício da sessão desktop X11
        # No Webtop LinuxServer, matar o xfce4-session faz o supervisor s6 reiniciar a interface em 1 segundo
        subprocess.Popen(['bash', '-c', 'sleep 1; pkill -9 xfce4-session || pkill -9 xfdesktop || sudo pkill -f Xorg'])

        GLM = GLib.timeout_add(1500, Gtk.main_quit)

def main():
    app = LanguageApp()
    Gtk.main()

if __name__ == '__main__':
    main()
