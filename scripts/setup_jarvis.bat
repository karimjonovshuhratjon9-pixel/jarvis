@echo off
cd /d "%~dp0.."
python scripts\setup_jarvis.py
if errorlevel 1 pause
