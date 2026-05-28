#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
反向代理控制器主程序
整合GUI界面和反向代理伺服器
"""

import sys
import os
import logging

# 添加當前目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """設置日誌配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('proxy_app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """主程序入口"""
    try:
        # 設置日誌
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("啟動反向代理控制器")
        
        # 導入並運行GUI
        from proxy_gui import ProxyGUI
        import tkinter as tk
        from tkinter import messagebox
        
        # 創建主窗口
        root = tk.Tk()
        
        # 設置窗口圖標（如果有的話）
        try:
            # 可以在這裡添加圖標文件
            # root.iconbitmap("icon.ico")
            pass
        except:
            pass
        
        # 設置窗口關閉事件
        def on_closing():
            if messagebox.askokcancel("退出", "確定要退出代理控制器嗎？"):
                logger.info("用戶請求退出程序")
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 創建GUI應用
        app = ProxyGUI(root)
        
        # 運行主循環
        logger.info("GUI界面已啟動，等待用戶操作")
        root.mainloop()
        
        logger.info("程序正常退出")
        
    except ImportError as e:
        logger.error(f"導入模塊失敗: {e}")
        print(f"錯誤：缺少必要的模塊 - {e}")
        print("請運行: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序運行錯誤: {e}")
        print(f"程序運行錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()