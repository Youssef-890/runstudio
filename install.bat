@echo off
cd /d "%~dp0"
echo RunStudio - installation
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python is not installed or not on PATH.
  echo Install Python 3.10+ from https://www.python.org/downloads/
  pause
  exit /b 1
)

python --version
if not exist .venv\Scripts\python.exe (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Installation complete. Run: run.bat
pause
