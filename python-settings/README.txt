Python settings window (hybrid approach)
========================================

AutoHotkey keeps the overlay, hotkeys and game logic. This window edits the same ini-files the
script already reads, then signals the running script through ini\python-bridge.txt
(handled by modules\python-bridge.ahk).

Run (Python 3.9+, uses only the standard library):
    python python-settings\settings_app.py            (PoE 1: 'ini')
    python python-settings\settings_app.py --poe2     (PoE 2: 'ini 2')

Pages so far: General (animations, browser features, capslock toggling, single-threaded mode,
font size, menu widget size, auto-close timeout).

Settings that are only read at startup (marked "restarts the script") make the script reload;
the rest are re-read live.

Tests:  cd python-settings && python -m unittest
