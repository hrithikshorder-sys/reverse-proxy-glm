#!/bin/bash

echo "正在啟動反向代理控制器..."
echo

# 檢查Python是否安裝
if ! command -v python3 &> /dev/null; then
    echo "錯誤: 未找到Python3，請先安裝Python3"
    exit 1
fi

# 檢查依賴包
echo "檢查依賴包..."
python3 -c "import flask, requests, tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "錯誤: 缺少依賴包，正在安裝..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依賴包安裝失敗，請手動安裝"
        exit 1
    fi
fi

echo "啟動應用程序..."
python3 main.py