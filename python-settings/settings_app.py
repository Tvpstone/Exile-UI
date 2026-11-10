"""Python settings window for Exile UI (hybrid approach).

AutoHotkey keeps the overlay, hotkeys and game logic. This window edits the same ini-files the
script already reads, then tells the running script about it through
"ini<version>\\python-bridge.txt" (see modules/python-bridge.ahk):

    apply   -> the script re-reads the settings that can change live
    reload  -> the script restarts (needed for settings that are only read at startup)

Usage:  python settings_app.py [--root PATH_TO_EXILE_UI] [--poe2]
"""
import argparse
import os
import tkinter as tk
from tkinter import ttk

from ini_file import IniFile

# --- setting definitions -------------------------------------------------------------------
# (label, section, key, kind, default, needs_reload, poe1_only, file)
#   kind: "bool" | ("int", min, max)
#   file: "version" -> ini<version>\config.ini, "shared" -> ini\config.ini (not split per game)
GENERAL = [
    ("Animations", "settings", "animations", "bool", 1, False, False, "version"),
    ("Browser features (PoE 1)", "settings", "enable browser features", "bool", 1, False, True, "version"),
    ("Capslock toggling", "settings", "enable capslock-toggling", "bool", 1, True, False, "version"),
    ("Single-threaded mode", "settings", "disable multi-threading", "bool", 0, True, False, "version"),
    ("Font size", "settings", "font-size", ("int", 6, 40), 16, True, False, "version"),
    ("Menu widget size", "settings", "menu-widget size", ("int", 6, 40), 16, True, False, "version"),
    ("Auto-close after N minutes without the game (0 = never)", "settings", "kill-timeout", ("int", 0, 10), 1, False, False, "shared"),
]


class SettingsApp(tk.Tk):
    def __init__(self, root_dir, poe2):
        super().__init__()
        self.title("Exile UI settings")
        self.minsize(560, 360)
        self.root_dir = root_dir
        self.poe2 = poe2
        self.version_dir = os.path.join(root_dir, "ini 2" if poe2 else "ini")
        self.shared_dir = os.path.join(root_dir, "ini")
        self.status = tk.StringVar(value="")
        self.vars = {}

        body = ttk.Frame(self, padding=8)
        body.pack(fill="both", expand=True)

        # section list on the left (only General so far; the other pages slot in here)
        self.sections = tk.Listbox(body, exportselection=False, width=16, height=10)
        self.sections.insert("end", "General")
        self.sections.selection_set(0)
        self.sections.pack(side="left", fill="y", padx=(0, 8))

        self.page = ttk.Frame(body)
        self.page.pack(side="left", fill="both", expand=True)
        self.build_general()

        ttk.Label(self, textvariable=self.status, anchor="w").pack(fill="x", padx=8, pady=(0, 6))

    # ---- ini access ------------------------------------------------------------------------
    def ini_for(self, which):
        folder = self.shared_dir if which == "shared" else self.version_dir
        return IniFile(os.path.join(folder, "config.ini"))

    def signal(self, command):
        os.makedirs(self.version_dir, exist_ok=True)
        path = os.path.join(self.version_dir, "python-bridge.txt")
        # a pending "reload" must not be downgraded to "apply" if the script hasn't picked it up yet
        try:
            with open(path, encoding="ascii") as f:
                if f.read().strip() == "reload":
                    command = "reload"
        except OSError:
            pass
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="ascii") as f:
            f.write(command)
        os.replace(tmp, path)

    # ---- pages -----------------------------------------------------------------------------
    def build_general(self):
        ttk.Label(self.page, text="General", font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row = 1
        for label, section, key, kind, default, reload_, poe1_only, which in GENERAL:
            if poe1_only and self.poe2:
                continue
            raw = self.ini_for(which).get(section, key)
            try:
                current = int(raw) if raw not in (None, "") else default
            except ValueError:
                current = default

            suffix = "  (restarts the script)" if reload_ else ""
            if kind == "bool":
                var = tk.IntVar(value=current)
                w = ttk.Checkbutton(self.page, text=label + suffix, variable=var,
                                    command=lambda s=(section, key, var, reload_, which), n=label: self.save(*s, n))
                w.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
            else:
                _, lo, hi = kind
                var = tk.IntVar(value=current)
                ttk.Label(self.page, text=label + suffix).grid(row=row, column=0, sticky="w", pady=2)
                w = ttk.Spinbox(self.page, from_=lo, to=hi, width=5, textvariable=var,
                                command=lambda s=(section, key, var, reload_, which), n=label: self.save(*s, n))
                w.bind("<FocusOut>", lambda _e, s=(section, key, var, reload_, which), n=label: self.save(*s, n))
                w.bind("<Return>", lambda _e, s=(section, key, var, reload_, which), n=label: self.save(*s, n))
                w.grid(row=row, column=1, sticky="w", padx=8)
            self.vars[key] = var
            row += 1

    # ---- saving ----------------------------------------------------------------------------
    def save(self, section, key, var, reload_, which, label):
        try:
            value = int(var.get())
        except (tk.TclError, ValueError):
            return  # half-typed spinbox content
        ini = self.ini_for(which)
        if ini.get(section, key) == str(value):
            return
        ini.set(section, key, value)
        ini.save()
        # kill-timeout also has a legacy "kill script" flag (0 disables auto-close), kept in sync like the AHK menu does
        if key == "kill-timeout":
            ini.set(section, "kill script", value)
            ini.save()
        self.signal("reload" if reload_ else "apply")
        self.status.set(f"{label} = {value}  ->  {'script restarting' if reload_ else 'applied'}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.path.dirname(here), help="Exile UI folder (contains 'Exile UI.ahk' and 'ini')")
    parser.add_argument("--poe2", action="store_true", help="edit the PoE 2 settings ('ini 2')")
    args = parser.parse_args()
    SettingsApp(os.path.abspath(args.root), args.poe2).mainloop()


if __name__ == "__main__":
    main()
