@echo off
:: 设置字符集为 UTF-8，防止中文乱码
chcp 65001 > nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo 未检测到虚拟环境，正在初始化...

    python --version > nul 2>&1
    if errorlevel 1 (
        echo 没有安装 Python，或者未添加到系统 PATH 环境变量中！
        echo 请先安装 Python 并勾选 "Add Python to PATH"。
        pause
        exit /b 1
    )

    echo 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo 虚拟环境创建失败！
        pause
        exit /b 1
    )

    if exist "requirements.txt" (
        echo 正在安装第三方依赖，请稍候...
        ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
        ".venv\Scripts\pip.exe" install -r requirements.txt
        if errorlevel 1 (
            echo 依赖包安装失败，请检查网络或 requirements.txt！
            pause
            exit /b 1
        )
    ) else (
        echo 未找到 requirements.txt，跳过依赖安装。
    )

    echo 环境初始化成功...
)

".venv\Scripts\python.exe" "main.py" %*