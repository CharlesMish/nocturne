@echo off
setlocal
cd /d "%~dp0..\.."

echo.
echo Nocturne legacy ambient media fetcher
echo =======================================
echo This optional Pixabay workflow is not required for normal installation.
echo.

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3 was not found.
    echo Install Python 3 and enable "Add python.exe to PATH".
    pause
    exit /b 1
  )
  set "PY=python"
) else (
  set "PY=py -3"
)

if not exist "media_sources.json" (
  %PY% scripts\fetch_media.py --init
  if errorlevel 1 (
    echo.
    echo Could not prepare media_sources.json.
    pause
    exit /b %errorlevel%
  )
)

%PY% scripts\fetch_media.py --yes %*
if errorlevel 1 (
  echo.
  echo Automatic media fetch failed or found no downloadable files.
  echo Fallback: opening source pages and media_sources.json for manual URLs.
  echo.
  %PY% scripts\fetch_media.py --init --open-source-pages
  start "" notepad "media_sources.json"
  echo.
  echo In each Pixabay page, open DevTools ^> Network, play/download the sound,
  echo copy the cdn.pixabay.com/audio/...mp3 or cdn.pixabay.com/download/audio/...mp3 URL,
  echo paste it into download_url, save media_sources.json, then run this fetcher again.
  echo.
  pause
  exit /b 1
)

echo.
echo Media fetch complete.
echo.
pause
