# Kairo - 多社團 Discord 機器人

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/) ![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)

**作者：** Serelix Studio

Kairo 是一個功能豐富的多租戶 Discord 機器人，專為學校社團和組織設計，提供簽到、週計劃、問答系統、CTFd 整合、加解密工具和記帳功能。

## 🌟 主要特色

- **多租戶架構** - 每個 Discord 伺服器皆為獨立管理，資料完全隔離。
- **申請審核系統** - 新的伺服器需經過審核，才能使用完整功能。
- **選擇性指令同步** - 根據伺服器狀態和啟用的模組，動態顯示可用指令。
- **模組化架構** - 各項功能均為獨立模組，可依需求啟用或關閉。

## 🚀 快速入門

### 環境需求

- Python 3.10+
- `pip install -r requirements.txt`

### 安裝步驟

1.  **複製 (Clone) 專案**
    ```bash
    git clone https://github.com/your-username/Kairo.git
    cd Kairo
    ```

2.  **安裝依賴套件**
    ```bash
    pip install -r requirements.txt
    ```

3.  **設定環境變數**
    將 `.env.example` 複製為 `.env` 檔案。
    ```bash
    cp .env.example .env
    ```
    接著，編輯 `.env` 檔案並填入所有必要的設定值。請參考下一節「環境變數」。

4.  **啟動機器人**
    ```bash
    python bot_main.py
    ```

## ⚙️ 環境變數

請在 `.env` 檔案中設定以下變數：

| 變數名稱 | 說明 | 範例 |
| --------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------- |
| `DISCORD_TOKEN` | **必需。** 你的 Discord 機器人 Token。 | `your_discord_bot_token` |
| `MASTER_KEY_BASE64` | **必需。** 用於加密敏感資料的 32 位元組金鑰 (Base64 編碼)。可使用 `generate_key.py` 產生。 | `your_base64_encoded_32_byte_key` |
| `SUPER_ADMIN_ID` | **必需。** 你的 Discord 使用者 ID，用於執行最高權限指令。 | `759651999036997672` |
| `ADMIN_GUILD_ID` | **必需。** 用於接收新伺服器註冊申請和管理機器人的「管理用伺服器」 ID。 | `1405176396158079076` |
| `REVIEW_CHANNEL_ID` | **必需。** 在管理用伺服器中，用於接收和處理註冊申請的頻道 ID。 | `1416406590411509860` |
| `EXCEL_PATH` | **必需。** 記帳功能的預設檔案路徑。可以是本機 `.xlsx` 檔案或 Google Sheets 網址。 | `data/bookkeeping.xlsx` |
| `GOOGLE_CREDENTIALS_PATH` | **可選。** 若使用 Google Sheets 記帳，請提供服務帳號的 JSON 憑證檔案路徑。 | `/path/to/your/service-account.json` |
| `HOST_PORT` | **可選。** 健康檢查服務所監聽的埠號。 | `12004` |

## 📦 功能模組

- **註冊與管理 (`register`, `response`, `modules_admin`)**: 新伺服器註冊、審核與模組管理。
- **簽到系統 (`attendance`)**: 透過指令或按鈕進行活動簽到。
- **週計劃 (`plans`)**: 發布與查詢每週活動或課程計畫。
- **問答系統 (`qa`)**: 建立題庫、進行問答和計分。
- **CTFd 整合 (`ctfd`)**: 連結 CTFd 平台，自動同步分數與獎勵。
- **加解密工具 (`crypto_cog`)**: 提供多種古典與現代密碼學工具。
- **記帳系統 (`bookkeeping`)**: 使用 Excel 或 Google Sheets 進行簡易記帳。
- **頻道路由 (`routing`)**: 設定特定模組的訊息推播頻道。

## 📚 詳細說明

- **[Google Sheets 設定指南](./GOOGLE_SHEETS_SETUP.md)** - 說明如何設定 Google Sheets 以搭配記帳功能使用。

## 🐳 Docker 部署

本專案支援使用 Docker 進行部署。

```bash
# 根據 .env.example 建立 .env 檔案並填寫設定

# 建置並於背景啟動服務
docker-compose up --build -d

# 檢查服務狀態
./demo.sh

# 停止服務
docker-compose down
```
