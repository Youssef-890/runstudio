@echo off
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run install.bat first.
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat
set FLASK_DEBUG=1
echo RunStudio: http://127.0.0.1:5000/
echo Press Ctrl+C to stop.
python app.py
