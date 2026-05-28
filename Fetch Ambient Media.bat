@echo off
setlocal
cd /d "%~dp0"

echo.
echo Nocturne ambient media fetcher
echo ===============================
echo.

if not exist "media_sources.json" (
  if exist "media_sources.default.json" (
    copy "media_sources.default.json" "media_sources.json" >nul
    echo Created media_sources.json from media_sources.default.json (recommended).
    echo.
    echo Fill the 7 'url' fields with fresh direct CDN links (see instructions inside the file),
    echo save, then double-click this fetcher again.
    echo.
    start "" notepad "media_sources.json"
    pause
    exit /b 0
  ) else if exist "media_sources.example.json" (
    copy "media_sources.example.json" "media_sources.json" >nul
    echo Created media_sources.json from media_sources.example.json.
    echo.
    echo (Better: use media_sources.default.json as your starting point.)
    start "" notepad "media_sources.json"
    pause
    exit /b 0
  ) else (
    echo Neither media_sources.default.json nor .example.json found.
    pause
    exit /b 1
  )
)

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    echo Python 3 was not found.
    echo Install Python 3 and enable "Add python.exe to PATH".
    pause
    exit /b 1
  )
)

%PY% install.py --fetch-media %*
if errorlevel 1 (
  echo.
  echo Media fetch failed.
  echo Check media_sources.json, then try again.
  echo.
  pause
  exit /b %errorlevel%
)

echo.
echo Media fetch complete.
echo.
pause
