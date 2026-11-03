@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\Manage-Pack.ps1" -Mode Uninstall %*
set "ECMP_EXIT=%ERRORLEVEL%"
pause
exit /b %ECMP_EXIT%
