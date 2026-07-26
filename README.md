# NextRole — AI 求職盤點工具（Claude Code / Codex）

> 求職盤點工具：用對話完成「天賦 + 技能」雙面向問卷 → 中立廣撒搜尋 104/Cake/LinkedIn → 評分 → 產出可篩選的 HTML 報表。

對話跑問卷、Python 跑爬蟲評分。**預設台灣，也可選海外（亞太 / 全球 / 全遠端）**、資料只存使用者本機。

## 安裝（Claude Code）

```bash
# 1. 裝 uv（Python 腳本執行器，~/3 秒一行指令）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 把 skill clone 到 Claude Code 的 skills 目錄
git clone https://github.com/oliviahuang0880/nextrole.git ~/.claude/skills/nextrole

# 3. 重開 Claude Code（讓它掃到新 skill）
```

> 沒有 `git` 的話也可以下載 zip 解壓到 `~/.claude/skills/nextrole/`。

## 在 Codex（或其他 AI 工具）使用

```bash
# clone 到任意位置
git clone https://github.com/oliviahuang0880/nextrole.git
cd nextrole
codex   # 在 repo 資料夾內啟動（Codex 會自動讀 AGENTS.md）
```

然後對它說「幫我找工作」即可，流程跟 Claude Code 版相同。差異：

- Codex 需要**在這個 repo 資料夾內**啟動才會載入指引（Claude Code 裝好後在任何資料夾都能觸發）
- 爬蟲與評分引擎完全相同；問卷對話的細膩度取決於所用模型
- Codex 端尚無大量實測，遇到問題歡迎開 issue

## 使用

在 Claude Code 對話框打：

> 「我想找台北的工作」 或 「想換工作」 或 「想找海外/遠端工作」 或 「help me find a remote job」

Skill 會自動觸發，引導你跑：

1. **天賦問卷**（可跳過）— 邀 5–6 位認識你的人寫「你眼中的我」貼回對話，AI 彙整成共通天賦
2. **技能問卷**（必做，35 題）— 一個技能一題情境式自評
3. **進階偏好** — 想找哪些地區（台灣 / 亞太 / 全球 / 全遠端，可複選）？要不要偏某個領域？有喜歡的職缺可貼 JD 給 AI 抽關鍵字？有什麼職稱想直接排除？
4. **搜尋並產出 HTML 報表** — 列出推薦 + 全部職缺、依分數排序、可依來源篩選

完成後開報表：
```bash
cd output && python3 -m http.server 8765
# 開 http://localhost:8765/results_<timestamp>.html
```
**不要用 `file://` 開**，職缺連結會空白（瀏覽器安全機制）。

## 需要

- [Claude Code](https://docs.claude.com/claude-code)，或 [Codex](https://openai.com/codex/) 等會讀 `AGENTS.md` 的 AI 工具
- [uv](https://docs.astral.sh/uv/)（偵測到沒裝會問是否代裝）
- **不需要任何 API key，也不需要 `.env`** — AI 推理（彙整朋友描述、抽 JD 關鍵字）由對話中的 AI 助手處理

### 選用：走 proxy（爬蟲被擋時）

若 104 / Cake / LinkedIn 開始回錯誤或空結果（被限流或擋 IP），可以用環境變數讓爬蟲走 HTTP proxy——在 shell 裡設好再跑，不需要設定檔：

```bash
export PROXY_URL=http://user:pass@host:port        # http、https 都走這個
# 或分別指定：
export PROXY_URL_HTTP=http://host:port
export PROXY_URL_HTTPS=http://host:port
```

不設（預設）就是直連。

## 隱私

- 所有資料（profile、爬到的職缺、報表）只存使用者本機，**沒有上傳**
- profile 位置：`~/.nextrole/profile.json`（覆蓋前自動備份）
- 報表位置：執行 `claude` 時當前目錄下的 `./output/`

## 重新使用

下次想再找：

| 場景 | 指令 |
|---|---|
| 重抓新職缺（profile 不變） | 對話「我要重新找職缺」→ 跑 `run_search.py` |
| 只想調關鍵字重算（不重抓） | 對話「重算一下」→ 跑 `run_search.py --from-cache`（秒算、不耗 token） |
| 重做問卷 | 對話「重做問卷」→ 從技能問卷重來，舊 profile 自動備份 |

不限次數，使用者自費 token。

## 評分邏輯（摘要）

- 總分 = **技能契合度 (60%) + 天賦契合度 (40%) − 負向懲罰**，0–100 分
- 沒做天賦問卷時自動切 100% 技能
- 命中職稱再 ×2 boost
- 「冷／硬冷」關鍵字出現在職稱直接排除（例：實習、財會、平面設計、表演⋯ 視個人分類而定）

## 也有網站版

有 GUI 偏好的人可以用網站版（同方法、不同介面）：（連結待補）。

## 已知限制

- 預設搜尋台灣的 104 / Cake / LinkedIn（規模約 300–400 筆/次）；選亞太/全球/遠端時 104 自動跳過、LinkedIn 改撈對應地點（亞太掃 7 城會多 5–8 分鐘）
- Cake / LinkedIn 改版時可能爬不到；先 ship，壞了砍剩 104
- 不做帳號、雲端儲存（資料就放使用者本機）

## 授權

MIT
