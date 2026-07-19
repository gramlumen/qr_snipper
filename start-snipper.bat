@echo off
cd /d "%~dp0"

:: 1. 检查虚拟环境是否存在，如果存在则直接跳转到运行程序
if exist ".venv\Scripts\python.exe" goto RUN_APP

echo [System] Environment not found. Initializing...

:: 2. 检查全局 Python 是否可用
python --version > nul 2>&1
if errorlevel 1 goto NO_PYTHON

:: 3. 创建虚拟环境
echo [System] Creating virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 goto VENV_ERR

:: 4. 检查并安装依赖
if not exist "requirements.txt" goto SKIP_REQ

echo [System] Installing dependencies from requirements.txt...
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
echo [Error] Python is not installed or not added to PATH!
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