@echo off
echo 正在啟動反向代理控制器...
echo.

REM 檢查Python是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤: 未找到Python，請先安裝Python
    pause
    exit /b 1
)

REM 檢查依賴包
echo 檢查依賴包...
python -c "import flask, requests, tkinter" >nul 2>&1
if errorlevel 1 (
    echo 錯誤: 缺少依賴包，正在安裝...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依賴包安裝失敗，請手動安裝
        pause
        exit /b 1
    )
)

echo 啟動應用程序...
python main.py

pause