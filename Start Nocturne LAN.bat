@echo off
setlocal
cd /d "%~dp0"

echo This starts Nocturne on 0.0.0.0 so other devices on your trusted LAN can connect.
echo Windows Firewall may ask you to allow Python. Choose private networks only.
echo.
call "Start Nocturne.bat" 0.0.0.0 8000
