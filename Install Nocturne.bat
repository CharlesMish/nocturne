@echo off
setlocal
cd /d "%~dp0"

echo.
echo Nocturne installer
echo ===================
echo.

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3 was not found.
    echo.
    echo Install Python 3 from https://www.python.org/downloads/windows/
    echo During installation, enable "Add python.exe to PATH".
    echo Then double-click this file again.
    echo.
    pause
    exit /b 1
  )
  set "PY=python"
) else (
  set "PY=py -3"
)

%PY% install.py %*
if errorlevel 1 (
  echo.
  echo Install failed.
  echo.
  pause
  exit /b %errorlevel%
)

echo.
echo Install complete.
echo Double-click "Start Nocturne.bat" to run Nocturne locally.
echo.
pause
