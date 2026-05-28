#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Open BigModel in Chrome with DevTools visible.

This script does not click page elements, read cookies, inspect Network data,
or extract credentials. It only opens the browser and waits for manual use.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


TARGET_URL = "https://bigmodel.cn/trialcenter/modeltrial/text?modelCode=glm-5.1"


def main():
    options = Options()
    options.add_argument("--auto-open-devtools-for-tabs")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    driver.get(TARGET_URL)

    print("Chrome 已開啟，DevTools 應已自動打開。")
    print("請在瀏覽器中手動登入、操作並查看 Network。")
    print("完成後回到此視窗按 Enter 關閉 Chrome。")
    input()
    driver.quit()


if __name__ == "__main__":
    main()
