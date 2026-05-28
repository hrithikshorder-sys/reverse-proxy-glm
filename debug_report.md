# 反向代理專案除錯報告

## 專案概述

本專案旨在建立一個Python反向代理應用程序，用於代理AI網頁服務，提供GUI界面和API客戶端功能。

## 專案結構

```
myapp/
├── main.py              # 主程序入口
├── reverse_proxy_server.py  # 反向代理核心功能
├── proxy_gui.py        # GUI界面
├── ai_proxy_client.py  # API客戶端
├── test_proxy.py       # 測試腳本
├── requirements.txt    # 依賴包列表
├── README.md           # 說明文檔
├── start_app.bat       # Windows啟動腳本
├── start_app.sh        # Linux/macOS啟動腳本
└── debug_report.md     # 除錯報告
```

## 核心功能

1. **反向代理伺服器**：將請求轉發到指定的AI網頁
2. **圖形化界面**：使用tkinter提供直觀的控制界面
3. **消息傳遞**：支持直接在APP中輸入訊息並獲取AI回應
4. **API客戶端**：提供Python客戶端庫，可在代碼中直接使用
5. **GET/POST支持**：支持多種HTTP請求方法

## 遇到的問題與解決方案

### 問題1：應用程序無法關閉

**錯誤信息**：
```
NameError: name 'messagebox' is not defined
```

**問題分析**：
在`main.py`中，`on_closing`函數使用了`messagebox`，但沒有導入。

**解決方案**：
在`main.py`中添加導入語句：
```python
from tkinter import messagebox
```

### 問題2：GUI界面太小

**用戶反饋**：
"畫面太小"

**解決方案**：
將窗口大小從`600x500`調整為`800x700`：
```python
self.root.geometry("800x700")
```

### 問題3：POST請求返回405錯誤

**錯誤信息**：
```
POST /trialcenter/modeltrial/text HTTP/1.1" 405 -
```

**問題分析**：
1. 目標URL構建時出現重複路徑問題
2. Flask路由配置可能存在問題

**調試過程**：

#### 第一次修復：
```python
# 構建目標URL - 移除目標URL中的查詢參數，因為路徑已經包含了它們
base_url = self.target_url.split('?')[0]
target_url = urljoin(base_url, path)

# 如果原始目標URL有查詢參數，添加到新的URL中
if '?' in self.target_url:
    target_url += self.target_url.split('?')[1]
```

**問題**：這導致URL重複，例如：
`https://bigmodel.cn/trialcenter/modeltrial/text?modelCode=glm-5.1/trialcenter/modeltrial/text&modelCode=glm-5.1`

#### 第二次修復：
```python
# 構建目標URL - 修復重複路徑問題
base_url = "https://bigmodel.cn"
if path == '':
    # 如果路徑為空，使用基本端點
    target_url = f"{base_url}/trialcenter/modeltrial/text?modelCode=glm-5.1"
else:
    # 否則，使用base URL + 路徑
    target_url = urljoin(base_url, path)
    
    # 確保modelCode參數存在
    if 'modelCode=glm-5.1' not in target_url:
        if '?' in target_url:
            target_url += '&modelCode=glm-5.1'
        else:
            target_url += '?modelCode=glm-5.1'
```

**調試信息添加**：
```python
# 調試日誌
logging.info(f"收到請求: {request.method} {path}")
logging.info(f"請求方法: {request.method}")
logging.info(f"請求路徑: {path}")
logging.info(f"請求頭: {dict(request.headers)}")
```

#### 當前狀態：
雖然路由已經正確匹配，但仍然返回405錯誤。這表明問題可能在目標服務器端，即`https://bigmodel.cn`的API端點可能不支持POST請求到該路徑。

## 技術細節

### Flask路由配置
```python
@self.app.route('/', defaults={'path': ''})
@self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
```

### 目標URL構建邏輯
```python
base_url = "https://bigmodel.cn"
if path == '':
    target_url = f"{base_url}/trialcenter/modeltrial/text?modelCode=glm-5.1"
else:
    target_url = urljoin(base_url, path)
    if 'modelCode=glm-5.1' not in target_url:
        if '?' in target_url:
            target_url += '&modelCode=glm-5.1'
        else:
            target_url += '?modelCode=glm-5.1'
```

### POST請求處理
```python
elif request.method == 'POST':
    json_data = request.get_json()
    logging.info(f"POST數據: {json_data}")
    response = requests.post(target_url, headers=headers, json=json_data, data=data, timeout=30)
```

## 測試結果

### GET請求測試
- **結果**：成功
- **狀態碼**：200
- **說明**：GET請求可以正常工作

### POST請求測試
- **結果**：失敗
- **狀態碼**：405 (Method Not Allowed)
- **說明**：POST請求被目標服務器拒絕

## 可能的原因分析

1. **目標API端點限制**：`https://bigmodel.cn`的API端點可能只支持特定的POST路徑
2. **認證問題**：可能需要特定的認證頭或參數
3. **請求格式問題**：可能需要特定的請求格式或參數結構
4. **CORS限制**：可能存在跨域限制

## 建議的下一步

1. **檢查API文檔**：查看`https://bigmodel.cn`的API文檔，了解正確的POST端點
2. **使用curl直接測試**：直接使用curl測試目標API，確認是否支持POST
3. **檢查請求格式**：確認請求格式是否符合API要求
4. **添加認證**：如果需要的話，添加必要的認證信息

## 最新更新：2026-05-28

### 已修正項目

1. `reverse_proxy_server.py` 根路由 `/` 已明確支援 `GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS`。
2. URL 組裝邏輯已區分頁面路徑與 API 路徑：
   - `/api/...` 和 `/biz/...` 會直接代理到 `https://bigmodel.cn/...`
   - `/trialcenter/...` 頁面路徑才會使用原本的頁面 URL 補參數邏輯
3. `test_proxy.py` 已改為自動化除錯腳本：
   - 自動啟動代理
   - 自動測試目標頁 GET
   - 自動測試 `/health`
   - 自動送出訊息 `HI`
   - 若回 `405`，自動直接測試目標站確認錯誤來源
   - 支援前端 SSE 模擬模式

### 最新測試結果

```text
目標頁 GET: HTTP 200
代理 /health: HTTP 200
代理訊息 POST /trialcenter/modeltrial/text: HTTP 405
直接 POST 目標頁: HTTP 405
模型清單 API GET: HTTP 200，但回傳缺少 Authorization
```

### 最新判斷

`405 Method Not Allowed` 不是本機 Flask 路由錯誤，而是 `bigmodel.cn` 目標頁端點回傳。`/trialcenter/modeltrial/text` 是網頁頁面，GET 可取得 HTML，但不接受 POST 聊天訊息。

前端實際聊天呼叫方式為：

```text
POST /api/biz/trial/response/v4/sse/{modelId}
```

該 API 需要登入後的 headers：

```text
Authorization
Bigmodel-Organization
Bigmodel-Project
Set-Language
Content-Type: application/json
```

未提供 `Authorization` 時會回：

```json
{"code":1001,"msg":"Header中未收到Authorization参数，无法进行身份验证。","success":false}
```

### 前端 SSE 模擬測試方式

```powershell
$env:BIGMODEL_AUTH="你的登入 Authorization token"
$env:BIGMODEL_MODEL_ID="模型 ID"
$env:BIGMODEL_MODEL_CODE="glm-5.1"
python test_proxy.py
```

可選：

```powershell
$env:BIGMODEL_ORG="你的 organization id"
$env:BIGMODEL_PROJECT="你的 project id"
```

### 結論

目前代理基礎功能可正常執行。若只代理網頁 GET，流程正常；若要送出聊天訊息取得 AI 回覆，不能 POST 到頁面路徑，必須改走前端 SSE API，並提供登入後的 `Authorization` token 與正確的 `modelId`。

詳細紀錄請見 `frontend_sse_debug.md`。

### 401 完善處理

已新增 401 授權失敗診斷：

1. `reverse_proxy_server.py` 會遮蔽 `Authorization`、`Cookie` 等敏感 header，避免 token 寫入日誌。
2. 若請求未帶授權，代理會嘗試從環境變數補上：
   - `BIGMODEL_AUTH`
   - `BIGMODEL_ORG`
   - `BIGMODEL_PROJECT`
3. 目標 API 回傳 `401` 時，代理會記錄明確警告：授權無效、已過期，或缺少組織/專案資訊。
4. `test_proxy.py` 遇到前端 SSE `401` 時，會輸出排查建議，並使用相同 headers 測試 `/api/biz/model/trial/` 以確認 token 是否有效。

401 常見原因：

```text
BIGMODEL_AUTH 缺失、錯誤或過期
Authorization 格式與瀏覽器前端請求不一致
缺少 Bigmodel-Organization 或 Bigmodel-Project
modelId 與目前帳號、組織或專案不匹配
帳號沒有該模型或體驗中心權限
```
