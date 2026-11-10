;hybrid-settings bridge: lets the external Python settings window (python-settings\settings_app.py) talk to the running script
;the Python app edits the ini-files directly and then drops a command into "ini<version>\python-bridge.txt"
;this timer-function picks the command up, deletes the file, and either re-reads the live-applicable settings ("apply") or restarts the script ("reload")
PythonBridge_Poll()
{
	local
	global vars, settings

	file := "ini" vars.poe_version "\python-bridge.txt"
	If !FileExist(file)
		Return

	FileRead, command, % file
	FileDelete, % file
	command := Trim(command, " `t`r`n")

	If (command = "reload")
	{
		Reload
		ExitApp
	}

	If (command != "apply")
		Return

	config := "ini" vars.poe_version "\config.ini"
	settings.general.animations := LLK_IniRead(config, "settings", "animations", 1)
	settings.features.browser := LLK_IniRead(config, "settings", "enable browser features", 1)
	settings.general.kill.1 := LLK_IniRead("ini\config.ini", "settings", "kill script", 1)
	settings.general.kill.2 := LLK_IniRead("ini\config.ini", "settings", "kill-timeout", 1)
}
