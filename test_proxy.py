#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
反向代理測試腳本
自動啟動代理、送出測試訊息，並輸出 405 除錯資訊。
"""

import logging
import os
import json
import socket
import sys
import time
from typing import Optional

import requests

from reverse_proxy_server import ReverseProxyServer


PROXY_ADDRESS = "http://localhost:8080"
TARGET_PAGE_URL = "https://bigmodel.cn/trialcenter/modeltrial/text?modelCode=glm-5.1"
MESSAGE_PATH = "/trialcenter/modeltrial/text"
TEST_MESSAGE = "HI"
FRONTEND_SSE_PATH = "/api/biz/trial/response/v4/sse/{model_id}"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def is_port_open(host: str = "127.0.0.1", port: int = 8080) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def wait_for_health(timeout: int = 15) -> Optional[dict]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"{PROXY_ADDRESS}/health", timeout=2)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            time.sleep(0.5)
    return None


def ensure_proxy_started() -> Optional[ReverseProxyServer]:
    if is_port_open():
        print("代理端口 8080 已開啟，使用現有代理服務。")
        return None

    print("代理未啟動，正在自動啟動代理服務...")
    proxy_server = ReverseProxyServer()
    proxy_server.start_server()
    return proxy_server


def print_response_debug(label: str, response: requests.Response):
    print(f"{label}: HTTP {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Allow: {response.headers.get('allow')}")
    body = response.text[:500].replace("\n", " ").replace("\r", " ")
    if body:
        print(f"Body 前 500 字: {body}")


def explain_auth_failure(response: requests.Response):
    print("\n401 授權失敗處理建議:")
    print("- 確認 BIGMODEL_AUTH 是登入後前端實際送出的 Authorization 值。")
    print("- 不要自行加 Bearer，除非瀏覽器 Network 裡 Authorization 本來就包含 Bearer。")
    print("- 確認 token 尚未過期；過期需要重新登入 bigmodel.cn 後取得新值。")
    print("- 若帳號屬於組織/專案，補上 BIGMODEL_ORG 與 BIGMODEL_PROJECT。")
    print("- 確認 BIGMODEL_MODEL_ID 與 BIGMODEL_MODEL_CODE 對應同一個模型。")

    body = response.text
    if "6101" in body:
        print("判斷: 組織不存在或 Bigmodel-Organization 錯誤。")
    elif "6102" in body:
        print("判斷: 專案不存在或 Bigmodel-Project 錯誤。")
    elif "6103" in body:
        print("判斷: 目前帳號不是該組織/專案成員。")
    elif "Authorization" in body or "401" in body:
        print("判斷: Authorization 缺失、格式錯誤或已失效。")


def test_target_get() -> bool:
    print("\n1. 直接測試目標頁 GET...")
    response = requests.get(TARGET_PAGE_URL, timeout=15)
    print_response_debug("目標頁 GET", response)
    return response.status_code == 200


def test_proxy_health() -> bool:
    print("\n2. 測試代理健康檢查...")
    health = wait_for_health()
    if health:
        print(f"代理健康檢查成功: {health}")
        return True
    print("代理健康檢查失敗: 無法連線到 /health")
    return False


def test_message_hi() -> int:
    print(f"\n3. 自動輸入訊息 {TEST_MESSAGE!r} 並送出...")
    payload = {
        "prompt": TEST_MESSAGE,
        "modelCode": "glm-5.1",
        "temperature": 0.7,
        "max_tokens": 1000,
    }
    response = requests.post(
        f"{PROXY_ADDRESS}{MESSAGE_PATH}",
        json=payload,
        timeout=30,
    )
    print_response_debug("代理訊息 POST", response)
    return response.status_code


def debug_405():
    print("\n4. 405 除錯...")
    print("直接測試目標頁 POST，確認 405 來源是否為目標站。")
    response = requests.post(
        TARGET_PAGE_URL,
        json={
            "prompt": TEST_MESSAGE,
            "modelCode": "glm-5.1",
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        timeout=15,
    )
    print_response_debug("目標頁 POST", response)

    print("\n再測試前端實際 SSE API 入口是否需要登入驗證。")
    api_response = requests.get(
        "https://bigmodel.cn/api/biz/model/trial/",
        timeout=15,
    )
    print_response_debug("模型清單 API GET", api_response)

    if response.status_code == 405:
        print(
            "\n判斷: 405 是 bigmodel.cn 的目標頁端點回傳。"
            " 該頁面 GET 可開啟 HTML，但不接受 POST 聊天訊息。"
        )
    if "Authorization" in api_response.text:
        print(
            "判斷: 前端 API 需要 Authorization；目前程式沒有登入/授權 token，"
            "所以無法直接取得模型 ID 或呼叫正式 SSE 聊天 API。"
        )


def test_frontend_sse_mode() -> Optional[int]:
    auth = os.environ.get("BIGMODEL_AUTH", "").strip()
    model_id = os.environ.get("BIGMODEL_MODEL_ID", "").strip()
    model_code = os.environ.get("BIGMODEL_MODEL_CODE", "glm-5.1").strip()
    org_id = os.environ.get("BIGMODEL_ORG", "").strip()
    project_id = os.environ.get("BIGMODEL_PROJECT", "").strip()
    cookie = os.environ.get("BIGMODEL_COOKIE", "").strip()
    payload_json = os.environ.get("BIGMODEL_PAYLOAD_JSON", "").strip()

    print("\n5. 模擬前端 SSE 呼叫...")
    if not auth or not model_id:
        print(
            "略過: 需要先設定 BIGMODEL_AUTH 和 BIGMODEL_MODEL_ID。"
            " 可選 BIGMODEL_ORG、BIGMODEL_PROJECT、BIGMODEL_MODEL_CODE。"
        )
        return None

    headers = {
        "Authorization": auth,
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
        "Set-Language": "zh",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://bigmodel.cn",
        "Referer": TARGET_PAGE_URL,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        ),
    }
    if org_id:
        headers["Bigmodel-Organization"] = org_id
    if project_id:
        headers["Bigmodel-Project"] = project_id
    if cookie:
        headers["Cookie"] = cookie

    if payload_json:
        payload = json.loads(payload_json)
    else:
        payload = {
            "model": model_code,
            "prompt": [{"role": "user", "content": TEST_MESSAGE, "fileContentList": []}],
            "modelId": int(model_id) if model_id.isdigit() else model_id,
            "stream": True,
            "thinking": {"type": "enabled"},
            "max_tokens": 65536,
            "temperature": 1,
            "top_p": 0.95,
            "tools": [
                {
                    "type": "web_search",
                    "web_search": {
                        "search_engine": "search_std",
                        "search_recency_filter": "noLimit",
                        "count": 10,
                        "search_intent": False,
                        "search_domain_filter": "",
                        "content_size": "medium",
                    },
                    "extraMcpData": [],
                }
            ],
        }

    response = requests.post(
        f"{PROXY_ADDRESS}{FRONTEND_SSE_PATH.format(model_id=model_id)}",
        json=payload,
        headers=headers,
        stream=True,
        timeout=30,
    )
    print_response_debug("前端 SSE POST", response)

    if response.status_code == 401:
        explain_auth_failure(response)
        validate_frontend_auth(headers)

    if response.status_code == 200:
        print("SSE 前幾行:")
        for index, line in enumerate(response.iter_lines(decode_unicode=True)):
            if line:
                print(line[:500])
            if index >= 8:
                break
    return response.status_code


def validate_frontend_auth(headers: dict):
    print("\n使用相同 headers 測試模型清單 API...")
    response = requests.get(
        f"{PROXY_ADDRESS}/api/biz/model/trial/",
        headers=headers,
        timeout=15,
    )
    print_response_debug("授權驗證 GET /api/biz/model/trial/", response)
    if response.status_code == 200 and '"code":1001' not in response.text:
        print("授權驗證通過；401 可能與 modelId、模型權限或 SSE payload 有關。")
    elif '"code":1001' in response.text:
        print("授權驗證失敗；請重新取得 BIGMODEL_AUTH。")


def main():
    setup_logging()

    proxy_server = None
    try:
        proxy_server = ensure_proxy_started()

        target_get_ok = test_target_get()
        if not target_get_ok:
            print("目標頁 GET 未成功，繼續保留狀態碼供除錯。")

        health_ok = test_proxy_health()
        if not health_ok:
            return 1

        message_status = test_message_hi()
        if message_status == 405:
            debug_405()
            frontend_status = test_frontend_sse_mode()
            return 0 if frontend_status == 200 else 1

        if message_status == 200:
            print("\n測試完成: 代理可以送出訊息並取得 200 回應。")
            return 0

        print(f"\n測試完成: 訊息請求回傳非預期狀態碼 {message_status}。")
        return 1
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
        return 1
    except Exception as exc:
        logging.exception("測試過程中發生錯誤")
        print(f"測試過程中發生錯誤: {exc}")
        return 1
    finally:
        if proxy_server:
            proxy_server.stop_server()


if __name__ == "__main__":
    sys.exit(main())
