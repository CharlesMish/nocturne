@echo off
setlocal
cd /d "%~dp0"

set "HOST=127.0.0.1"
set "PORT=8000"
if not "%~1"=="" set "HOST=%~1"
if not "%~2"=="" set "PORT=%~2"

if not exist ".venv\Scripts\python.exe" (
  echo Nocturne does not look installed yet.
  echo Running installer first...
  echo.
  call "Install Nocturne.bat"
  if errorlevel 1 exit /b %errorlevel%
)

set "OPEN_HOST=%HOST%"
if "%HOST%"=="0.0.0.0" set "OPEN_HOST=127.0.0.1"

echo.
echo Starting Nocturne on http://%OPEN_HOST%:%PORT%/
echo Close this window or press Ctrl+C to stop the server.
echo.

start "" powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 2; Start-Process 'http://%OPEN_HOST%:%PORT%/'"
".venv\Scripts\python.exe" -m uvicorn main:app --host %HOST% --port %PORT%

echo.
echo Nocturne stopped.
echo.
pause
