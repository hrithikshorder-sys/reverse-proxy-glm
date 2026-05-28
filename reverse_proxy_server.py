import threading
import requests
from flask import Flask, request, jsonify, Response
from urllib.parse import urljoin
import logging
import os
import sys


SENSITIVE_HEADERS = {
    'authorization',
    'cookie',
    'set-cookie',
    'x-token',
}


def sanitize_headers(headers):
    safe_headers = {}
    for name, value in headers.items():
        if name.lower() in SENSITIVE_HEADERS:
            safe_headers[name] = '***'
        else:
            safe_headers[name] = value
    return safe_headers


def apply_env_auth_headers(headers):
    auth = os.environ.get('BIGMODEL_AUTH', '').strip()
    org_id = os.environ.get('BIGMODEL_ORG', '').strip()
    project_id = os.environ.get('BIGMODEL_PROJECT', '').strip()

    if auth and not headers.get('Authorization'):
        headers['Authorization'] = auth
    if org_id and not headers.get('Bigmodel-Organization'):
        headers['Bigmodel-Organization'] = org_id
    if project_id and not headers.get('Bigmodel-Project'):
        headers['Bigmodel-Project'] = project_id
    return headers

class ReverseProxyServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.target_url = "https://bigmodel.cn/trialcenter/modeltrial/text?modelCode=glm-5.1"
        self.proxy_port = 8080
        self.server_thread = None
        self.is_running = False
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
        @self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
        def proxy(path):
            # 調試日誌
            logging.info(f"收到請求: {request.method} {path}")
            logging.info(f"請求方法: {request.method}")
            logging.info(f"請求路徑: {path}")
            logging.info(f"請求頭: {sanitize_headers(dict(request.headers))}")
            
            # 構建目標URL - 前端頁面路徑與 API 路徑使用不同規則
            base_url = "https://bigmodel.cn"
            if path == '':
                # 如果路徑為空，使用基本端點
                target_url = f"{base_url}/trialcenter/modeltrial/text?modelCode=glm-5.1"
            elif path.startswith('api/') or path.startswith('biz/'):
                target_url = urljoin(f"{base_url}/", path)
            else:
                # 否則，使用base URL + 路徑
                target_url = urljoin(f"{base_url}/", path)
                
                # 確保modelCode參數存在
                if 'modelCode=glm-5.1' not in target_url:
                    if '?' in target_url:
                        target_url += '&modelCode=glm-5.1'
                    else:
                        target_url += '?modelCode=glm-5.1'
            
            logging.info(f"目標URL: {target_url}")
            
            # 獲取請求數據
            data = request.get_data()
            headers = dict(request.headers)
            
            # 移除一些不需要轉發的頭部
            headers.pop('Host', None)
            headers.pop('Content-Length', None)
            headers = apply_env_auth_headers(headers)
            
            try:
                # 根據請求方法轉發
                if request.method == 'GET':
                    response = requests.get(target_url, headers=headers, params=request.args, data=data, timeout=30)
                elif request.method == 'POST':
                    json_data = request.get_json()
                    logging.info(f"POST數據: {json_data}")
                    response = requests.post(target_url, headers=headers, json=json_data, data=data, timeout=30)
                elif request.method == 'PUT':
                    response = requests.put(target_url, headers=headers, json=request.get_json(), data=data, timeout=30)
                elif request.method == 'DELETE':
                    response = requests.delete(target_url, headers=headers, data=data, timeout=30)
                elif request.method == 'PATCH':
                    response = requests.patch(target_url, headers=headers, json=request.get_json(), data=data, timeout=30)
                elif request.method == 'HEAD':
                    response = requests.head(target_url, headers=headers, timeout=30)
                elif request.method == 'OPTIONS':
                    response = requests.options(target_url, headers=headers, timeout=30)
                else:
                    return jsonify({'error': '不支持的請求方法'}), 405
                
                logging.info(f"響應狀態: {response.status_code}")
                if response.status_code == 401:
                    logging.warning(
                        "目標 API 回傳 401: Authorization 無效、已過期，或缺少 Bigmodel-Organization/Bigmodel-Project"
                    )
                
                # 轉發響應
                excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
                headers = [(name, value) for (name, value) in response.headers.items() if name.lower() not in excluded_headers]
                
                return Response(response.content, response.status_code, headers)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"代理請求失敗: {e}")
                return jsonify({'error': f'代理請求失敗: {str(e)}'}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({'status': 'ok', 'target_url': self.target_url})
    
    def start_server(self):
        if not self.is_running:
            self.is_running = True
            self.server_thread = threading.Thread(target=self.run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            logging.info(f"反向代理伺服器已啟動，監聽端口: {self.proxy_port}")
    
    def stop_server(self):
        if self.is_running:
            self.is_running = False
            # Flask伺服器需要手動停止，這裡簡化處理
            logging.info("反向代理伺服器已停止")
    
    def run_server(self):
        try:
            self.app.run(host='0.0.0.0', port=self.proxy_port, debug=False, use_reloader=False)
        except Exception as e:
            logging.error(f"伺服器運行錯誤: {e}")
    
    def get_proxy_address(self):
        return f"http://localhost:{self.proxy_port}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    proxy_server = ReverseProxyServer()
    proxy_server.start_server()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        proxy_server.stop_server()
