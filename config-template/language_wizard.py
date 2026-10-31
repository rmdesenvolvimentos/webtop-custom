#!/usr/bin/env python3
# =============================================================================
# language_wizard.py – Assistente de idioma (primeira execução)
# Cloud Desktop – Windows 11 Style
# =============================================================================
# Exibido automaticamente no primeiro login.
# Detecta o idioma atual, exibe confirmação e permite trocar.
# Salva a preferência em ~/.language_preference para uso em toda a sessão.
# =============================================================================
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os, subprocess, sys

HOME        = os.path.expanduser('~')
LANG_FILE   = os.path.join(HOME, '.language_preference')
DONE_FLAG   = os.path.join(HOME, '.language_wizard_done')

# Idiomas suportados: (código_locale, emoji_bandeira, nome_exibição)
LANGUAGES = [
    ('pt_BR', '🇧🇷', 'Português (Brasil)'),
    ('en_US', '🇺🇸', 'English (United States)'),
    ('es_ES', '🇪🇸', 'Español (España)'),
    ('de_DE', '🇩🇪', 'Deutsch (Deutschland)'),
    ('fr_FR', '🇫🇷', 'Français (France)'),
    ('it_IT', '🇮🇹', 'Italiano (Italia)'),
]

# Textos da janela em cada idioma
UI = {
    'pt_BR': {
        'title':    'Bem-vindo ao Cloud Desktop',
        'detected': 'Idioma detectado:',
        'question': 'Confirme o idioma ou escolha outro:',
        'confirm':  '✓  Confirmar e Aplicar',
        'cancel':   'Cancelar',
        'note':     'As alterações serão salvas. Recomenda-se reiniciar o container ou deslogar para aplicar 100% no XFCE.',
    },
    'en_US': {
        'title':    'Welcome to Cloud Desktop',
        'detected': 'Detected language:',
        'question': 'Confirm your language or choose another:',
        'confirm':  '✓  Confirm',
        'cancel':   'Cancel',
        'note':     'For full effect, log out and log back in.',
    },
    'es_ES': {
        'title':    'Bienvenido a Cloud Desktop',
        'detected': 'Idioma detectado:',
        'question': 'Confirme el idioma o elija otro:',
        'confirm':  '✓  Confirmar',
        'cancel':   'Cancelar',
        'note':     'Para aplicar completamente, cierre sesión y vuelva a entrar.',
    },
    'de_DE': {
        'title':    'Willkommen beim Cloud Desktop',
        'detected': 'Erkannte Sprache:',
        'question': 'Sprache bestätigen oder eine andere wählen:',
        'confirm':  '✓  Bestätigen',
        'cancel':   'Abbrechen',
        'note':     'Für volle Wirkung bitte abmelden und erneut anmelden.',
    },
    'fr_FR': {
        'title':    'Bienvenue sur Cloud Desktop',
        'detected': 'Langue détectée :',
        'question': 'Confirmez la langue ou choisissez-en une autre :',
        'confirm':  '✓  Confirmer',
        'cancel':   'Annuler',
        'note':     'Pour un effet complet, déconnectez-vous puis reconnectez-vous.',
    },
    'it_IT': {
        'title':    'Benvenuto in Cloud Desktop',
        'detected': 'Lingua rilevata:',
        'question': 'Conferma la lingua o scegline un\'altra:',
        'confirm':  '✓  Conferma e Applica',
        'cancel':   'Annulla',
        'note':     'Le modifiche sono salvate. Riavvia il container o disconnettiti per applicare al 100% in XFCE.',
    },
}


def detect_current_lang():
    """Detecta o idioma atual: arquivo de preferência → LANG → fallback."""
    if os.path.exists(LANG_FILE):
        stored = open(LANG_FILE).read().strip()
        codes = [l[0] for l in LANGUAGES]
        if stored in codes:
            return stored
    env_lang = os.environ.get('LANG', 'pt_BR.UTF-8').split('.')[0]
    codes = [l[0] for l in LANGUAGES]
    return env_lang if env_lang in codes else 'pt_BR'


def save_language(code):
    """Salva preferência e aplica locale no ambiente da sessão."""
    for p in [LANG_FILE, '/config/.language_preference']:
        try:
            with open(p, 'w') as f:
                f.write(code)
        except Exception:
            pass

    locale_str = f"{code}.UTF-8"
    lang_short  = code.split('_')[0]
    env_content = (
        f'LANG={locale_str}\n'
        f'LANGUAGE={code}:{lang_short}\n'
        f'LC_ALL={locale_str}\n'
    )

    # 1. Atualiza /etc/environment e /etc/default/locale via sudo
    try:
        tmp = '/tmp/.lang_env_new'
        with open(tmp, 'w') as f:
            f.write(env_content)
        subprocess.run(['sudo', 'cp', tmp, '/etc/environment'], check=False, timeout=5)
        subprocess.run(['sudo', 'cp', tmp, '/etc/default/locale'], check=False, timeout=5)
    except Exception:
        pass

    # 2. Gera locales dinamicamente se necessário
    try:
        subprocess.run(['sudo', 'locale-gen', locale_str], check=False, timeout=10)
    except Exception:
        pass

    # 3. Atualiza xfconf para a sessão XFCE
    try:
        subprocess.run(
            ['xfconf-query', '-c', 'xfce4-session', '-p',
             '/general/LangEnvironment', '--create', '-t', 'string', '-s', locale_str],
            check=False, timeout=5)
    except Exception:
        pass

    # 4. Grava em ~/.profile e ~/.bashrc para terminais e novos processos
    export_lines = f'\nexport LANG="{locale_str}"\nexport LANGUAGE="{code}:{lang_short}"\nexport LC_ALL="{locale_str}"\n'
    for profile_file in [os.path.join(HOME, '.profile'), os.path.join(HOME, '.bashrc')]:
        try:
            with open(profile_file, 'a') as f:
                f.write(export_lines)
        except Exception:
            pass


def get_lang_info(code):
    for lc, flag, name in LANGUAGES:
        if lc == code:
            return flag, name
    return '🌐', code


class LanguageWizard(Gtk.Window):
    def __init__(self):
        super().__init__(title='Cloud Desktop')
        self.current_code = detect_current_lang()
        self.ui = UI.get(self.current_code, UI['en_US'])

        # ── Janela ──────────────────────────────────────────────────────────
        self.set_default_size(480, 360)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(True)
        self.set_keep_above(True)
        self.connect('destroy', Gtk.main_quit)

        # CSS para combinar com o tema escuro Windows 11
        css = b"""
        window { background-color: #1e2128; }
        .card  { background-color: #252930; border-radius: 12px; padding: 24px; }
        .title { color: #ffffff; font-size: 20px; font-weight: bold; }
        .sub   { color: #9da8b7; font-size: 13px; }
        .flag  { font-size: 40px; }
        .lang-detected { color: #e0e6f0; font-size: 15px; font-weight: bold; }
        .note  { color: #6b7585; font-size: 11px; font-style: italic; }
        button.confirm {
            background: #0078d4;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 24px;
            font-size: 13px;
            font-weight: bold;
        }
        button.confirm:hover { background: #106ebe; }
        button.cancel-btn {
            background: #3a3f4b;
            color: #c0c8d8;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 13px;
        }
        button.cancel-btn:hover { background: #474d5c; }
        combobox { background-color: #2d323e; color: #e0e6f0; border-radius: 6px; }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # ── Layout ──────────────────────────────────────────────────────────
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_margin_top(20)
        outer.set_margin_bottom(20)
        outer.set_margin_start(20)
        outer.set_margin_end(20)
        self.add(outer)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class('card')
        outer.pack_start(card, True, True, 0)

        # Ícone + título
        flag_now, name_now = get_lang_info(self.current_code)
        flag_label = Gtk.Label(label=flag_now)
        flag_label.get_style_context().add_class('flag')
        flag_label.set_halign(Gtk.Align.CENTER)
        card.pack_start(flag_label, False, False, 0)

        title = Gtk.Label(label=self.ui['title'])
        title.get_style_context().add_class('title')
        title.set_halign(Gtk.Align.CENTER)
        card.pack_start(title, False, False, 4)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_opacity(0.2)
        card.pack_start(sep, False, False, 8)

        # Idioma detectado
        detected_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        detected_box.set_halign(Gtk.Align.CENTER)

        sub = Gtk.Label(label=self.ui['detected'])
        sub.get_style_context().add_class('sub')
        detected_box.pack_start(sub, False, False, 0)

        lang_name_lbl = Gtk.Label(label=f"{flag_now}  {name_now}")
        lang_name_lbl.get_style_context().add_class('lang-detected')
        detected_box.pack_start(lang_name_lbl, False, False, 0)
        card.pack_start(detected_box, False, False, 0)

        # Separador + pergunta
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.set_opacity(0.15)
        card.pack_start(sep2, False, False, 8)

        question = Gtk.Label(label=self.ui['question'])
        question.get_style_context().add_class('sub')
        question.set_halign(Gtk.Align.START)
        card.pack_start(question, False, False, 0)

        # Dropdown de idiomas
        store = Gtk.ListStore(str, str)  # código, exibição
        self.combo = Gtk.ComboBox.new_with_model(store)
        renderer = Gtk.CellRendererText()
        self.combo.pack_start(renderer, True)
        self.combo.add_attribute(renderer, 'text', 1)

        active_idx = 0
        for i, (code, flag, name) in enumerate(LANGUAGES):
            store.append([code, f"{flag}  {name}"])
            if code == self.current_code:
                active_idx = i
        self.combo.set_active(active_idx)
        card.pack_start(self.combo, False, False, 0)

        # Nota de logout
        note = Gtk.Label(label=self.ui['note'])
        note.get_style_context().add_class('note')
        note.set_halign(Gtk.Align.CENTER)
        note.set_line_wrap(True)
        card.pack_start(note, False, False, 8)

        # Botões
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)

        btn_cancel = Gtk.Button(label=self.ui['cancel'])
        btn_cancel.get_style_context().add_class('cancel-btn')
        btn_cancel.connect('clicked', self._on_cancel)

        btn_confirm = Gtk.Button(label=self.ui['confirm'])
        btn_confirm.get_style_context().add_class('confirm')
        btn_confirm.connect('clicked', self._on_confirm)

        btn_box.pack_start(btn_cancel, False, False, 0)
        btn_box.pack_start(btn_confirm, False, False, 0)
        card.pack_start(btn_box, False, False, 0)

        self.show_all()

    def _get_selected_code(self):
        it = self.combo.get_active_iter()
        if it:
            return self.combo.get_model()[it][0]
        return self.current_code

    def _on_confirm(self, _btn):
        selected = self._get_selected_code()
        save_language(selected)
        # Marca como concluído
        with open(DONE_FLAG, 'w') as f:
            f.write(selected)
        self.destroy()

        # Reinicia o painel XFCE e o desktop para recarregar o novo idioma nos menus e ícones imediatamente
        try:
            locale_str = f"{selected}.UTF-8"
            lang_short = selected.split('_')[0]
            env_cmd = f"export LANG={locale_str}; export LANGUAGE={selected}:{lang_short}; export LC_ALL={locale_str}; "
            subprocess.Popen(["bash", "-c", f"{env_cmd} xfce4-panel -r 2>/dev/null; {env_cmd} xfdesktop --reload 2>/dev/null &"])
        except Exception:
            pass

        Gtk.main_quit()

    def _on_cancel(self, _btn):
        # Cancela sem salvar — na próxima sessão abre novamente
        Gtk.main_quit()


def main():
    # Não executa se já foi configurado nesta sessão
    if os.path.exists(DONE_FLAG):
        sys.exit(0)
    # Aguarda o desktop estar pronto
    import time
    time.sleep(3)
    win = LanguageWizard()
    Gtk.main()


if __name__ == '__main__':
    main()
