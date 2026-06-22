# NextRole — Claude Skill

> 台灣求職盤點工具：用對話完成「天賦 + 技能」雙面向問卷 → 中立廣撒搜尋 104/Cake/LinkedIn → 評分 → 產出可篩選的 HTML 報表。

對話跑問卷、Python 跑爬蟲評分。**TW only**、資料只存使用者本機。

## 安裝

```bash
# 1. 裝 uv（Python 腳本執行器，~/3 秒一行指令）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 把 skill clone 到 Claude Code 的 skills 目錄
git clone https://github.com/oliviahuang0880/nextrole.git ~/.claude/skills/nextrole

# 3. 重開 Claude Code（讓它掃到新 skill）
```

> 沒有 `git` 的話也可以下載 zip 解壓到 `~/.claude/skills/nextrole/`。

## 使用

在 Claude Code 對話框打：

> 「我想找台北的工作」 或 「想換工作」 或 「help me find a job in Taiwan」

Skill 會自動觸發，引導你跑：

1. **天賦問卷**（可跳過）— 邀 5–6 位認識你的人寫「你眼中的我」貼回對話，AI 彙整成共通天賦
2. **技能問卷**（必做，35 題）— 一個技能一題情境式自評
3. **進階偏好** — 想找哪些縣市？要不要偏某個領域？有喜歡的職缺可貼 JD 給 AI 抽關鍵字
4. **搜尋並產出 HTML 報表** — 列出推薦 + 全部職缺、依分數排序、可依來源篩選

完成後開報表：
```bash
cd output && python3 -m http.server 8765
# 開 http://localhost:8765/results_<timestamp>.html
```
**不要用 `file://` 開**，職缺連結會空白（瀏覽器安全機制）。

## 需要

- [Claude Code](https://docs.claude.com/claude-code)（或同等支援 skill 的環境）
- [uv](https://docs.astral.sh/uv/)（skill 偵測到沒裝會問是否代裝）
- **不需要** `ANTHROPIC_API_KEY` — AI 推理（彙整朋友描述、抽 JD 關鍵字）由對話的 Claude 處理

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

- 只搜尋 TW 的 104、Cake、LinkedIn（規模約 300–400 筆/次）
- Cake / LinkedIn 改版時可能爬不到；先 ship，壞了砍剩 104
- 不做帳號、雲端儲存（資料就放使用者本機）

## 授權

MIT
