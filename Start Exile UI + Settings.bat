@echo off
rem Starts Exile UI (AutoHotkey) and the Python settings window together.
rem Extra arguments are passed to the settings window, e.g.:  "Start Exile UI + Settings.bat" --poe2
cd /d "%~dp0"

start "" "%~dp0Exile UI.ahk"

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw "%~dp0python-settings\settings_app.py" %*
) else (
    start "" python "%~dp0python-settings\settings_app.py" %*
)
