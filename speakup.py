#!/usr/bin/env python3
# (C) 2017 Matthias Dellweg

import os
import sys
import re
import gi
import yaml
from espeak import espeak

gi.require_version('Clutter', '1.0')
gi.require_version('ClutterGdk', '1.0')
from gi.repository import Clutter, ClutterGdk, Pango

# --- Glue layer ---

def speak(text, config):
    language = config['default_language']
    lang_match = re.match('^<(.*)>(.*)$', text)
    if lang_match:
        language = lang_match.group(1)
        text = lang_match.group(2)
    if language in config['voices']:
        espeak.set_voice(config['voices'][language])
    text = text.strip()
    if text:
        espeak.synth(text)


# --- Events ---

def stage_on_delete(stage, event, config=None):
    Clutter.main_quit()


def stage_on_button_press(stage, event, config=None):
    Clutter.main_quit()


def entry_on_key_press(entry, event, config=None):
    if event.keyval in [ Clutter.KEY_Return, Clutter.KEY_KP_Enter ]:
        text = entry.get_text()
        if text:
            speak(text, config)
        else:
            Clutter.main_quit()
        entry.set_text("")
        entry.old_iterator = -1
        for old_entry in entry.old_entries:
            old_text = old_entry.get_text()
            old_entry.set_text(text)
            text = old_text
        return True
    if event.keyval == Clutter.KEY_Up:
        entry.old_iterator = min(entry.old_iterator + 1, 14)
        entry.set_text(entry.old_entries[entry.old_iterator].get_text())
        return True
    if event.keyval == Clutter.KEY_Down:
        entry.old_iterator = max(entry.old_iterator, 0) - 1
        if entry.old_iterator < 0:
            entry.set_text("")
        else:
            entry.set_text(entry.old_entries[entry.old_iterator].get_text())
        return True
    if event.keyval == Clutter.KEY_Escape:
        Clutter.main_quit()
    if event.keyval in config['mapped_idioms']:
        entry.set_text(config['mapped_idioms'][event.keyval])
        return True


# --- setup ---

def read_config():
    config_base = os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    try:
        with open(os.path.join(config_base, 'speakup.yml')) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        pass
    if not 'idioms' in config:
        config['idioms'] = [ 'Yup', 'Nope' ]
    if not 'voices' in config:
        config['voices'] = { 'en': 'english', 'de': 'german' }
    if not 'default_language' in config:
        config['default_language'] = list(config['voices'].keys())[0]
    # adjust info
    config['mapped_idioms'] = { k: str(v) for k, v in zip(range(Clutter.KEY_F1, Clutter.KEY_F12 + 1), config['idioms']) }
    return config


def setup_stage(config):
    stage_color = Clutter.Color.new(0, 0, 0, 0)
    text_color = Clutter.Color.new(0, 128, 0, 255)

    Clutter.init(sys.argv)
    stage = Clutter.Stage()
    stage.set_title("Speakup")
    stage.set_use_alpha(True)
    stage.set_background_color(stage_color)
    stage.connect("delete-event", stage_on_delete, config)
    stage.connect("button-press-event", stage_on_button_press, config)

    layout = Clutter.BoxLayout()
    layout.set_orientation(Clutter.Orientation.VERTICAL)
    layout.set_spacing(15)
    stage.set_layout_manager(layout)

    old_entries = []
    for i in range(15):
        old_entry = Clutter.Text.new_with_text("Sans 28px", "")
        old_entry.set_color(Clutter.Color.new(0, 128, 0, (i + 1) * 16))
        old_entries.append(old_entry)
        stage.add_actor(old_entry)
    old_entries.reverse()

    entry = Clutter.Text.new_with_text("Sans 28px", "")
    entry.set_color(text_color)
    entry.set_editable(True)
    entry.set_reactive(True)
    entry.set_single_line_mode(True)
    entry.set_line_alignment(Pango.Alignment.CENTER)
    entry.connect("key-press-event", entry_on_key_press, config)
    stage.add_actor(entry)
    entry.old_entries = old_entries
    entry.old_iterator = -1

    stage.show()
    stage.set_fullscreen(True)
    stage.set_key_focus(entry)

    stage_window = ClutterGdk.get_stage_window(stage)
    stage_window.set_keep_above(True)
    stage_window.set_modal_hint(True)
    stage_window.set_skip_taskbar_hint(True)
    stage_window.set_skip_pager_hint(True)
    # TODO always in front and on active screen


# --- Main ---

if __name__ == "__main__":
    config = read_config()
    setup_stage(config)
    Clutter.main()
