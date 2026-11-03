@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Scripts\Manage-Pack.ps1" -Mode Install %*
set "ECMP_EXIT=%ERRORLEVEL%"
if not "%ECMP_EXIT%"=="0" echo Installation failed. See the message above.
pause
exit /b %ECMP_EXIT%
