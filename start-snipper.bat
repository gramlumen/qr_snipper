@echo off
cd /d "%~dp0"

rem 1. Check if virtual environment exists
if exist ".venv\Scripts\python.exe" goto RUN_APP

echo [System] Environment not found. Initializing...

rem 2. Check if Python is installed globally
python --version > nul 2>&1
if errorlevel 1 goto NO_PYTHON

rem 3. Create virtual environment
echo [System] Creating virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 goto VENV_ERR

rem 4. Install dependencies if requirements.txt exists
if not exist "requirements.txt" goto SKIP_REQ

echo [System] Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 goto PIP_ERR

:SKIP_REQ
echo [System] Setup completed successfully!
echo --------------------------------------------------

:RUN_APP
".venv\Scripts\python.exe" "main.py" %*
goto END

:NO_PYTHON
echo [Error] Python is not installed or not in PATH!
echo Please install Python and check "Add Python to PATH".
pause
exit /b 1

:VENV_ERR
echo [Error] Failed to create virtual environment!
pause
exit /b 1

:PIP_ERR
echo [Error] Failed to install dependencies!
pause
exit /b 1

:END