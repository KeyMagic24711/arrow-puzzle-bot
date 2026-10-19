
@echo off
setlocal
REM Arrow Puzzle Bot v2 - one-file downloader (no zip files anywhere).
REM Reads version.json from the public GitHub repo, downloads each small
REM file individually, installs Python deps if missing, makes a Desktop
REM shortcut, and launches the app. Put adb.exe on PATH or in tools\.
set REPO=https://raw.githubusercontent.com/KeyMagic24711/arrow-puzzle-bot/main
set DEST=%LOCALAPPDATA%\ArrowPuzzleBot
mkdir "%DEST%" 2>nul
echo Downloading version.json ...
curl -fsSL "%REPO%/version.json" -o "%DEST%\version.json" || goto :fail
where python >nul 2>nul || goto :nopython
curl -fsSL "%REPO%/requirements.txt" -o "%DEST%\requirements.txt" || goto :fail
python -m pip install --quiet -r "%DEST%\requirements.txt" || goto :fail
powershell -NoProfile -ExecutionPolicy Bypass -Command "$v=Get-Content '%DEST%\version.json' -Raw | ConvertFrom-Json; foreach($rel in $v.files){ $out=Join-Path '%DEST%' $rel; New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null; Invoke-WebRequest -Uri ('https://raw.githubusercontent.com/KeyMagic24711/arrow-puzzle-bot/main/'+$rel) -OutFile $out; Write-Host ('downloaded '+$rel) }"
if errorlevel 1 goto :fail
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Arrow Puzzle Bot.lnk'); $s.TargetPath='pythonw.exe'; $s.Arguments='\"%DEST%\app\main.py\"'; $s.WorkingDirectory='%DEST%'; $s.Save()"
echo Done. Launching Arrow Puzzle Bot...
start "" pythonw "%DEST%\app\main.py"
exit /b 0
:nopython
echo Python not found. Install Python 3.11+ from python.org with Add to PATH, then run this file again.
pause
exit /b 1
:fail
echo Download failed. Check internet connection and run again.
pause
exit /b 1
