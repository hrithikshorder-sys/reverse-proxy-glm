#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI代理客戶端
用於在代碼中直接使用反向代理詢問AI網頁
"""

import requests
import json
import logging
from typing import Dict, Any, Optional

class AIProxyClient:
    """AI代理客戶端，封裝了與AI網頁的交互"""
    
    def __init__(self, proxy_url: str = "http://localhost:8080", timeout: int = 30):
        """
        初始化AI代理客戶端
        
        Args:
            proxy_url: 反向代理服務器地址
            timeout: 請求超時時間（秒）
        """
        self.proxy_url = proxy_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # 設置日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def ask_ai(self, prompt: str, model_code: str = "glm-5.1", 
                temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        向AI發送問題
        
        Args:
            prompt: 要問AI的問題
            model_code: 模型代碼
            temperature: 溫度參數
            max_tokens: 最大令牌數
            
        Returns:
            AI的回應數據
        """
        try:
            # 構建請求數據
            request_data = {
                "prompt": prompt,
                "modelCode": model_code,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # 發送POST請求到代理服務器
            response = self.session.post(
                f"{self.proxy_url}/trialcenter/modeltrial/text",
                json=request_data,
                timeout=self.timeout
            )
            
            # 檢查響應
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"AI回應成功: {prompt}")
                return result
            else:
                error_msg = f"請求失敗，狀態碼: {response.status_code}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"網路請求錯誤: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析錯誤: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"未知錯誤: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_health_check(self) -> Dict[str, Any]:
        """
        檢查代理服務器健康狀態
        
        Returns:
            健康檢查結果
        """
        try:
            response = self.session.get(
                f"{self.proxy_url}/health",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"健康檢查失敗: {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def custom_request(self, endpoint: str, method: str = "GET", 
                     data: Optional[Dict] = None, 
                     headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        發送自定義請求
        
        Args:
            endpoint: 端點路徑
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            data: 請求數據
            headers: 請求頭
            
        Returns:
            響應數據
        """
        try:
            url = f"{self.proxy_url}/{endpoint.lstrip('/')}"
            
            if method.upper() == "GET":
                response = self.session.get(url, params=data, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise Exception(f"不支持的HTTP方法: {method}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"請求失敗: {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

# 使用示例
def example_usage():
    """使用示例"""
    # 創建AI代理客戶端
    client = AIProxyClient(proxy_url="http://localhost:8080")
    
    # 檢查服務狀態
    health = client.get_health_check()
    print(f"服務狀態: {health}")
    
    # 問AI問題
    try:
        response = client.ask_ai("你好，請介紹一下你自己")
        print("AI回應:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    example_usage()