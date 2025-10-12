# 貢獻指南（Contributing Guidelines）

> 感謝您對 Serelix Studio 專案的關注與支持 🎉

為確保所有貢獻能順利整合並維持高品質，我們制定以下貢獻流程與準則。

在提交前，請先閱讀本文件與專案的 [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)。

## 🚀 參與方式

您可以透過以下方式貢獻本專案：

- 🔧 **程式碼改進**：新增功能、修正錯誤、效能優化等
- 📚 **文件改善**：README、教學文件、註解等
- 🐛 **問題回報**：錯誤回報與改進建議
- 🧪 **品質保證**：協助測試、驗證或翻譯

## 🐛 回報問題（Issues）

若發現錯誤、漏洞或使用疑慮，請先確認以下事項：

1. ✅ 已搜尋過現有討論，確定問題尚未被提出
2. ✅ 提供明確的重現步驟、環境資訊與錯誤訊息
3. ⚠️ 若為安全性問題，**請勿公開發佈**，改以電子郵件方式通報（見 [SECURITY.md](./SECURITY.md)）

### 問題回報範本

```markdown
### 🐛 問題描述
（清楚描述遇到的問題）

### 🔄 重現步驟
1. 開啟...
2. 點擊...
3. 執行...

### ✅ 預期結果
（說明您認為應該出現的正確行為）

### ❌ 實際結果
（附上錯誤訊息或截圖）

### 🌐 環境資訊
- 作業系統：
- 瀏覽器/版本：
- 專案版本：
```

## 🔄 提交變更（Pull Requests）

### 1. Fork 與分支策略

```bash
# Fork 專案至您的帳號
git clone https://github.com/yourusername/project-name.git
cd project-name

# 建立新分支進行開發
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/bug-description
```

**分支命名規範：**
- `feature/forum-post-editor` - 新功能
- `fix/socket-timeout-bug` - 錯誤修正
- `docs/api-documentation` - 文件更新
- `refactor/user-auth-flow` - 程式碼重構

### 2. Commit 規範

每次提交訊息應簡潔且具描述性：

```bash
# 建議格式
git commit -m "add: 實作文章編輯模組"
git commit -m "fix: 修正登入時 Token 驗證錯誤"
git commit -m "docs: 更新 API 說明文件"
git commit -m "refactor: 重構使用者資料處理流程"
```

**Commit 類型：**
- `add` - 新增功能
- `fix` - 修正錯誤
- `docs` - 文件更新
- `style` - 格式調整（不影響程式邏輯）
- `refactor` - 程式碼重構
- `test` - 測試相關
- `chore` - 建置工具、依賴更新等

### 3. Pull Request 檢查清單

開啟 PR 前，請確認：

- [ ] 程式碼遵循專案風格規範
- [ ] 所有測試通過
- [ ] 文件已同步更新
- [ ] Commit 訊息清晰明確
- [ ] PR 描述包含變更目的與影響範圍

### 4. PR 描述範本

```markdown
## 📋 變更摘要
（簡述此 PR 的目的與背景）

## 🔧 主要修改
- 項目 1
- 項目 2
- 項目 3

## 🧪 測試方式
（說明如何驗證變更）

## 📸 截圖（如適用）
（UI 變更請附上前後對比圖）

## ⚠️ 注意事項
（是否有破壞性變更或需要特別注意的地方）
```

## 🎨 程式風格

為保持一致性，請遵循以下格式規範：

| 語言 | 標準 | 工具 |
|------|------|------|
| **Python** | PEP8 | Black, flake8 |
| **JavaScript/TypeScript** | ESLint + Prettier | ESLint, Prettier |
| **CSS/SCSS** | BEM 方法論 | Stylelint |
| **Markdown** | UTF-8，每行 ≤ 100 字元 | markdownlint |

### 自動化檢查

```bash
# Python
black . && flake8

# JavaScript/TypeScript
npm run lint && npm run format

# 所有檔案
npm run check
```

## 🧪 測試與驗證

- ✅ 新增或修改功能時，請同步更新測試案例
- ✅ 確保所有測試通過 CI/CD 檢查
- ✅ 若修改影響外部 API，請更新文件說明

```bash
# 執行測試
npm test

# 檢查測試覆蓋率
npm run test:coverage
```

## 📄 授權與貢獻歸屬

- 所有貢獻皆將遵循專案主要授權條款（見 [LICENSE](./LICENSE)）
- 提交 Pull Request 即代表您同意授予 Serelix Studio 使用與再發佈該內容的權利
- 我們會在貢獻記錄與發布說明中感謝所有貢獻者

## 📞 聯繫與支援

若您有任何疑問、建議或需要私下通報問題，請聯繫：

- 📧 **電子郵件**：serelixstudio@gmail.com
- 💬 **官方社群**：[Serelix Studio Discord](https://discord.gg/eRfGKepusP)
- 👨‍💻 **工作室首席工程師**：[kaiyasi](https://discord.com/users/kaiyasi)

## 🎖️ 貢獻者名單

感謝所有為 Serelix Studio 專案貢獻的開發者！您的參與讓專案更加完善。

<!-- 貢獻者清單將自動生成 -->

## 🙏 感謝您的貢獻

每一位貢獻者都是 Serelix Studio 成長的一部分。感謝您願意投入時間與心力，讓這個專案更好！

---

*最後更新：2024年10月*
