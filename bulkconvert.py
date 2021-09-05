# -*- coding: utf-8 -*-

# Paste Images As WebP add-on for Anki 2.1
# Copyright (C) 2021  Ren Tatsumoto. <tatsu at autistici.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Any modifications to this file must keep this entire header intact.
import re
from pathlib import Path
from typing import Optional

from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import tooltip

from .utils.gui import SettingsDialog
from .utils.webp import ImageConverter


def checkpoint(msg="Checkpoint"):
    def decorator(fn):
        def decorated(*args, **kwargs):
            mw.checkpoint(msg)
            mw.progress.start()
            fn(*args, **kwargs)
            mw.progress.finish()
            mw.reset()

        return decorated

    return decorator


def convert_image(filename: str) -> Optional[Path]:
    try:
        w = ImageConverter()
        w.load_internal(filename)
        w.convert_internal(filename)
    except RuntimeError:
        tooltip(f"Couldn't convert {filename}.")
    else:
        return w.filepath


def find_eligible_images(html: str):
    images = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', html)
    return (image for image in images if image[-5:] != '.webp')


@checkpoint(msg="Bulk-convert to WebP")
def bulk_convert(nids: list):
    notes = {mw.col.getNote(nid) for nid in nids}
    counter = 0
    for note in notes:
        for key, field in note.items():
            if '<img' not in field:
                continue

            for image in find_eligible_images(field):
                if filepath := convert_image(image):
                    note[key] = field.replace(image, filepath.name, 1)
                    counter += 1

        note.flush()

    tooltip(f"Done. Converted {counter} files.")


def on_bulk_convert(browser: Browser):
    selected_notes = browser.selectedNotes()
    if selected_notes:
        dialog = SettingsDialog(browser)
        dialog.exec_()
        bulk_convert(selected_notes)
    else:
        tooltip("No cards selected.")


def setup_menu(browser: Browser):
    a = QAction("Bulk-convert to WebP", browser)
    a.triggered.connect(lambda: on_bulk_convert(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


def init():
    gui_hooks.browser_menus_did_init.append(setup_menu)