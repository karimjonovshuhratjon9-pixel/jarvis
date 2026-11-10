@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Run scripts\setup_jarvis.bat first.
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install pyinstaller
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --name JARVIS --hidden-import ui --add-data "assets/fonts;assets/fonts" main.py
if errorlevel 1 exit /b 1
echo Build output: dist\JARVIS\JARVIS.exe
echo Optional installer: open installer\JARVIS.iss with Inno Setup 6.
echo Test the packaged app on the target Windows 11 machine before distributing it.
