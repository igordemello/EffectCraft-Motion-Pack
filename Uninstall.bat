@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\Manage-Plugin.ps1" -Mode Uninstall %*
set "ECMP_EXIT=%ERRORLEVEL%"
if not "%ECMP_EXIT%"=="0" echo Uninstall incomplete. See the message above.
pause
exit /b %ECMP_EXIT%
