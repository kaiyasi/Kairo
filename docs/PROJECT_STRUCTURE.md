# 專案目錄結構說明

> Kairo 專案的檔案組織架構

## 📁 根目錄結構

```
Kairo/
├── 📄 README.md                    # 專案主要說明文檔
├── 📄 LICENSE                      # 專案授權條款
├── 📄 requirements.txt             # Python 依賴套件清單
├── 📄 .gitignore                   # Git 忽略檔案設定
├── 🐳 Dockerfile                   # Docker 容器建置檔案
├── 🐳 docker-compose.yml           # Docker 容器編排檔案
├── 📂 kairo/                       # 主要程式碼目錄
├── 📂 docs/                        # 文檔資料夾
└── 📂 scripts/                     # 腳本檔案資料夾
```

## 🚀 主要程式碼目錄 (`kairo/`)

```
kairo/
├── 🤖 bot_main.py                  # Discord Bot 主程式
├── 🔌 socket_server.py             # Socket 伺服器
├── 🔑 generate_key.py              # 金鑰生成工具
├── 📂 cogs/                        # Discord Bot 功能模組
│   ├── 📊 attendance.py            # 出席管理功能
│   ├── 💰 bookkeeping.py           # 記帳功能
│   ├── 🔐 crypto_cog.py            # 加密功能
│   ├── 🏆 ctfd.py                  # CTF 競賽功能
│   ├── ⚙️ modules_admin.py         # 管理員功能
│   ├── 📋 plans.py                 # 計劃管理功能
│   ├── ❓ qa.py                    # 問答功能
│   ├── 📝 register.py              # 註冊功能
│   ├── 💬 response.py              # 回應處理功能
│   └── 🛣️ routing.py               # 路由功能
├── 📂 data/                        # 資料檔案
│   ├── 📊 qa_bank.json             # 問答題庫
│   └── 🗄️ tenant.db               # 租戶資料庫
├── 📂 tests/                       # 測試檔案
│   ├── 🧪 test_channels.py         # 頻道測試
│   ├── 🧪 test_crypto_longtext.py  # 加密長文本測試
│   └── 🧪 test_socket.py           # Socket 測試
└── 📂 utils/                       # 工具函式庫
    ├── 🎨 brand.py                 # 品牌相關工具
    ├── 🔐 crypto.py                # 加密工具
    ├── 📊 excel.py                 # Excel 處理工具
    ├── 📈 google_sheets.py         # Google Sheets 整合
    ├── 🏢 tenant.py                # 租戶管理工具
    └── 👁️ visibility.py            # 可見性控制工具
```

## 📚 文檔目錄 (`docs/`)

```
docs/
├── 📋 CODE_OF_CONDUCT.md           # 社群行為準則
├── 📋 CONTRIBUTING.md              # 貢獻指南
├── 🔒 SECURITY.md                  # 安全性政策
├── 📋 GOOGLE_SHEETS_SETUP.md       # Google Sheets 設定指南
└── 📋 PROJECT_STRUCTURE.md         # 專案結構說明文檔
```

## 🔧 腳本目錄 (`scripts/`)

```
scripts/
└── 🚀 demo.sh                     # 演示腳本
```

## 📋 檔案類型說明

### 🤖 核心程式檔案
- **bot_main.py**: Discord Bot 的主要進入點
- **socket_server.py**: 處理 WebSocket 連線的伺服器
- **generate_key.py**: 用於生成加密金鑰的工具

### 🔌 功能模組 (Cogs)
Discord Bot 的各項功能以模組化方式組織，每個 `.py` 檔案代表一個特定功能：
- 使用者管理（註冊、出席）
- 資料處理（記帳、問答）
- 安全功能（加密、管理）
- 競賽功能（CTF）

### 🛠️ 工具函式庫 (Utils)
共用的工具函式和輔助功能，提供給其他模組使用

### 🧪 測試檔案 (Tests)
確保程式品質的自動化測試檔案

### 📊 資料檔案 (Data)
- **qa_bank.json**: 問答系統的題庫資料
- **tenant.db**: SQLite 資料庫，存放租戶相關資訊

## 🔄 開發工作流程

1. **主程式**: 從 `kairo/bot_main.py` 啟動
2. **功能開發**: 在 `kairo/cogs/` 中新增或修改功能模組
3. **工具函式**: 在 `kairo/utils/` 中新增共用工具
4. **測試**: 在 `kairo/tests/` 中撰寫對應測試
5. **文檔**: 在 `docs/` 中更新相關說明

## 🐳 容器化部署

- **Dockerfile**: 定義應用程式的容器環境
- **docker-compose.yml**: 編排多容器應用程式
- **requirements.txt**: 指定 Python 依賴套件版本

## 📝 專案管理檔案

- **README.md**: 專案概述和使用說明（位於根目錄）
- **LICENSE**: 開源授權條款（位於根目錄）
- **docs/ 資料夾內的文檔**:
  - **CODE_OF_CONDUCT.md**: 社群參與準則
  - **CONTRIBUTING.md**: 貢獻者指南
  - **SECURITY.md**: 安全性政策和漏洞回報流程
  - **GOOGLE_SHEETS_SETUP.md**: Google Sheets 整合設定指南
  - **PROJECT_STRUCTURE.md**: 專案目錄結構說明

---

*此文檔會隨著專案結構變更而更新*
