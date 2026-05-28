# 前端 SSE 模擬除錯紀錄

日期：2026-05-28

## 目的

本文件記錄目前反向代理專案對 `bigmodel.cn` 的測試結果，以及如何模擬前端方式呼叫聊天 SSE API。

## 目前結論

代理服務可以正常啟動，`/health` 健康檢查也可正常回應。目標頁面 `https://bigmodel.cn/trialcenter/modeltrial/text?modelCode=glm-5.1` 使用 GET 可回傳 HTML 頁面，狀態碼為 `200`。

直接把聊天訊息用 POST 送到 `/trialcenter/modeltrial/text` 會得到 `405 Method Not Allowed`。這不是本機 Flask 路由造成，而是目標站 `bigmodel.cn` 對該網頁路徑回傳的結果。該路徑是前端頁面，不是聊天 API。

## 前端實際呼叫方式

從前端 JavaScript 觀察到，聊天訊息不是送到：

```text
/trialcenter/modeltrial/text
```

而是送到 SSE API：

```text
/api/biz/trial/response/v4/sse/{modelId}
```

請求方式為 `POST`，並使用 `text/event-stream` 接收串流回覆。

前端會帶入下列 headers：

```text
Authorization
Bigmodel-Organization
Bigmodel-Project
Set-Language
Content-Type: application/json
```

其中 `Authorization` 是必要項目。未登入或未帶 token 時，API 會回：

```json
{"code":1001,"msg":"Header中未收到Authorization参数，无法进行身份验证。","success":false}
```

## 已更新的程式

### `reverse_proxy_server.py`

已修正 URL 組裝邏輯：

- `/api/...` 和 `/biz/...` 路徑會直接代理到 `https://bigmodel.cn/...`
- 一般 `/trialcenter/...` 頁面路徑才會保留原本的 `modelCode=glm-5.1` 補參數邏輯
- 根路由 `/` 已明確支援 `GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS`

### `test_proxy.py`

測試腳本現在會：

1. 自動啟動代理服務
2. 測試目標頁 GET
3. 測試代理 `/health`
4. 自動送出訊息 `"HI"`
5. 若遇到 `405`，自動確認 405 是否來自目標站
6. 若提供授權環境變數，嘗試模擬前端 SSE 呼叫

## 執行測試

基本測試：

```powershell
python test_proxy.py
```

模擬前端 SSE 呼叫需要設定：

```powershell
$env:BIGMODEL_AUTH="你的登入 Authorization token"
$env:BIGMODEL_MODEL_ID="模型 ID"
$env:BIGMODEL_MODEL_CODE="glm-5.1"
python test_proxy.py
```

如帳號需要組織或專案 ID，也可設定：

```powershell
$env:BIGMODEL_ORG="你的 organization id"
$env:BIGMODEL_PROJECT="你的 project id"
```

## 測試結果摘要

目前未提供登入授權時的結果：

```text
目標頁 GET: HTTP 200
代理健康檢查: HTTP 200
代理訊息 POST /trialcenter/modeltrial/text: HTTP 405
直接 POST 目標頁: HTTP 405
模型清單 API GET: HTTP 200，但回傳缺少 Authorization
前端 SSE 模擬: 略過，因缺少 BIGMODEL_AUTH 和 BIGMODEL_MODEL_ID
```

## 下一步

若要讓訊息功能真正取得 AI 回覆，需要取得登入後的 `Authorization` token 與正確的 `modelId`，再透過 `test_proxy.py` 的前端 SSE 模擬模式測試。

若不想依賴網頁前端私有 API，建議改用官方公開 API，並以 API Key 呼叫正式模型服務。

## 401 授權失敗處理

若出現：

```text
API端點請求失敗: 401
```

代表請求已到達 API，但授權未通過。常見原因如下：

1. `BIGMODEL_AUTH` 缺失、填錯或已過期
2. `Authorization` 格式與前端實際格式不一致
3. 缺少 `BIGMODEL_ORG` 或 `BIGMODEL_PROJECT`
4. `BIGMODEL_MODEL_ID` 不屬於目前帳號、組織或專案
5. token 對應帳號沒有該模型或體驗中心權限

建議處理順序：

1. 在瀏覽器登入 `bigmodel.cn`
2. 開啟開發者工具 Network
3. 在體驗中心送出一次訊息
4. 找到 `/api/biz/trial/response/v4/sse/{modelId}` 請求
5. 複製該請求中的 `Authorization`、`Bigmodel-Organization`、`Bigmodel-Project`
6. 將值設定到環境變數後重新執行測試

```powershell
$env:BIGMODEL_AUTH="從 Network 複製的 Authorization 原值"
$env:BIGMODEL_ORG="從 Network 複製的 Bigmodel-Organization"
$env:BIGMODEL_PROJECT="從 Network 複製的 Bigmodel-Project"
$env:BIGMODEL_MODEL_ID="SSE 路徑最後的 modelId"
$env:BIGMODEL_MODEL_CODE="glm-5.1"
python test_proxy.py
```

注意：不要自行加上 `Bearer`，除非瀏覽器 Network 裡的 `Authorization` 本來就包含 `Bearer`。本專案會原樣轉發 `BIGMODEL_AUTH`。

目前 `reverse_proxy_server.py` 已避免在日誌中輸出 `Authorization`、`Cookie` 等敏感 header，並可在請求未帶授權時自動從環境變數補上 `BIGMODEL_AUTH`、`BIGMODEL_ORG`、`BIGMODEL_PROJECT`。

若仍然回 `500`，下一步不要再貼完整 headers。請只提供同一個 SSE 請求的 `Request Payload` / `Payload` JSON。前端 SSE 請求的 `content-length` 若大於簡化 payload，通常代表 body 裡還有 `tools`、`thinking`、模型參數或其他欄位。

如確定必須帶 Cookie 才能測，可在本機設定：

```powershell
$env:BIGMODEL_COOKIE="從 Network 複製的 Cookie 原值"
```

但不要把 Cookie 貼到聊天室。

## 成功條件

前端 SSE 模擬成功時會看到：

```text
前端 SSE POST: HTTP 200
Content-Type: text/event-stream;charset=UTF-8
```

並且後續會出現類似：

```text
event:webSearch
event:add
data:{...}
```

這代表請求已成功進入前端 SSE API，並開始收到串流事件。
