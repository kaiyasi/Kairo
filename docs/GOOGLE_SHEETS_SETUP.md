# Google Sheets 設定指南

Kairo 機器人支援 Google Sheets 記帳功能，讓社團可以使用熟悉的 Google 試算表進行記帳管理。

## 🔧 設定步驟

### 1. 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用 Google Sheets API：
   - 在左側選單選擇「API 和服務」>「程式庫」
   - 搜尋「Google Sheets API」
   - 點擊並啟用

### 2. 建立服務帳號

1. 在 Google Cloud Console 中，前往「API 和服務」>「憑證」
2. 點擊「建立憑證」>「服務帳號」
3. 輸入服務帳號名稱（如：kairo-sheets-service）
4. 點擊「建立並繼續」
5. 角色選擇「編輯者」或「擁有者」
6. 點擊「完成」

### 3. 下載憑證金鑰

1. 在憑證頁面找到剛建立的服務帳號
2. 點擊服務帳號的 Email
3. 切換到「金鑰」頁籤
4. 點擊「新增金鑰」>「建立新金鑰」
5. 選擇「JSON」格式
6. 下載金鑰檔案並保存為 `service-account.json`

### 4. 設定 Google Sheets

1. 建立或開啟要使用的 Google Sheets
2. 點擊「共用」按鈕
3. 將服務帳號的 Email 地址（從 JSON 檔案中的 `client_email` 欄位取得）加入共用名單
4. 權限設定為「編輯者」
5. 複製 Google Sheets 的 URL

### 5. 設定環境變數

更新 `.env` 檔案：

```bash
# 預設 Google Sheets URL（可選）
EXCEL_PATH=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit

# Google 服務帳號憑證檔案路徑
GOOGLE_CREDENTIALS_PATH=/path/to/service-account.json
```

## 📋 使用方式

### 全域設定（適用所有 Guild）

在 `.env` 檔案中設定 `EXCEL_PATH` 為 Google Sheets URL：

```bash
EXCEL_PATH=https://docs.google.com/spreadsheets/d/1GoDnh4UdKwmA9ZVkbsQdCxVRdhGMJrwYRXoWBYuNLeM/edit
```

### 個別 Guild 設定

每個 Guild 可以有獨立的記帳檔案：

```bash
# 管理員在 Discord 中執行
/book_set_sheets url:https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

### 記帳操作

設定完成後，所有記帳指令都會自動使用 Google Sheets：

```bash
# 新增支出
/book_add category:零食 amount:-50 memo:餅乾一包

# 新增收入
/book_add category:社費 amount:500 memo:新生入社費

# 查詢餘額
/book_balance

# 匯出記錄
/book_export
```

## 🏗️ 工作表結構

### Journal 工作表（自動建立）

機器人會自動建立名為 "Journal" 的工作表，包含以下欄位：

| 欄位 | 說明 | 範例 |
|------|------|------|
| Date | 日期 | 2025-01-15 |
| Category | 類別 | 零食 |
| Amount | 金額 | -50 |
| Memo | 備註 | 餅乾一包 |
| User | 記錄者 | 小明 |

### Summary 工作表（可選）

您可以建立 "Summary" 工作表來計算總餘額：

```
A1: 總餘額
B1: =SUM(Journal!C:C)
```

機器人會優先讀取 Summary 工作表中的餘額顯示。

## 🔒 權限與安全

### 服務帳號權限

- 服務帳號只需要對特定 Google Sheets 的「編輯者」權限
- 建議不要給予過高的權限（如整個 Google Drive 的存取權）

### 資料安全

- 服務帳號憑證檔案請妥善保管，不要上傳到版本控制
- 定期輪換服務帳號金鑰
- 只與必要的 Google Sheets 共用權限

### Discord 權限

- 只有具備「管理伺服器」權限的用戶可以設定 Google Sheets URL
- 所有成員都可以使用記帳功能（如果模組已啟用）

## 🚨 常見問題

### Q: 顯示「Google Sheets 操作失敗」

**解決方法：**
1. 檢查服務帳號是否有 Google Sheets 的編輯權限
2. 確認 `GOOGLE_CREDENTIALS_PATH` 路徑正確
3. 驗證憑證檔案格式是否正確的 JSON

### Q: 無法建立 Journal 工作表

**解決方法：**
1. 確認服務帳號有編輯權限
2. 檢查 Google Sheets API 是否已啟用
3. 確認網路連線正常

### Q: 餘額顯示不正確

**解決方法：**
1. 檢查 Summary 工作表的公式是否正確
2. 確認 Journal 工作表的 Amount 欄位都是數值格式
3. 使用 `/book_export` 匯出檢查資料完整性

### Q: URL 格式錯誤

**正確的 URL 格式：**
```
https://docs.google.com/spreadsheets/d/SHEET_ID/edit
```

**錯誤的格式：**
- 缺少 `https://`
- 包含 `#gid=0` 等額外參數（會自動處理）
- 使用共用連結而非編輯連結

## 📊 進階功能

### 多工作表支援

除了 Journal 工作表外，您可以建立其他工作表進行分析：

- **Summary**: 總計與統計
- **Monthly**: 月度報表
- **Categories**: 類別分析

機器人只會寫入 Journal 工作表，其他工作表可以使用公式引用 Journal 的資料。

### 自動化公式

在 Summary 工作表中可以使用各種公式：

```
=SUM(Journal!C:C)                    // 總餘額
=SUMIF(Journal!B:B,"零食",Journal!C:C)   // 零食類別總額
=COUNTIF(Journal!C:C,"<0")           // 支出次數
```

## 🔄 從本地 Excel 遷移

如果您之前使用本地 Excel 檔案，可以：

1. 將 Excel 檔案上傳到 Google Drive
2. 轉換為 Google Sheets 格式
3. 使用 `/book_set_sheets` 設定新的 URL
4. 確認資料完整性

遷移後舊的本地檔案仍會保留，但機器人會使用新的 Google Sheets。