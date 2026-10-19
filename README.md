# Arrow Puzzle Bot v2
Clean modular rebuild (5 modules, plain small files, no zip archives).
Modules: ReadMap (capture+stitch+detect), Solver (zones+layers+order),
Tapper (tapping, hearts; renamed from Stepper), Connection (ADB+game+
interruptions), UI (controls, 2 clocks, manual update).
## Download / install (Windows)
Download the single file `installer/ArrowBotDownloader.bat`, run it: it reads
version.json, downloads every file individually into
%LOCALAPPDATA%\ArrowPuzzleBot, installs Python deps, creates a Desktop
shortcut and launches the app. You also need Python 3.11+ (Add to PATH)
and Android platform-tools adb.exe on PATH (or in the tools folder).
Updates are checked/downloaded only when you press the update button in
the UI. `version.json` at the repo root is the only update-check file.
## Run from source
pip install -r requirements.txt ; python app/main.py ; python app/main.py --self-check
## Tests
python -m unittest discover -s tests -v
Spec: docs/SPEC.md ; settled assumptions: docs/ASSUMPTIONS.md
