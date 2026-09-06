# NextRole — AI 求職工具（Claude Code / Codex）

> 搜職缺 → 評分 → 決定投不投 → 客製履歷 → 準備面試題 → 模擬面試 → 追蹤進度。
> 同一份資料串到底，**全部存在你自己的電腦上**。

對話跑問卷與判斷，Python 跑爬蟲、評分與產表。預設台灣，也可選海外（亞太／全球／全遠端）。

## 六個 skill

| 打這個 | 做什麼 | 自然講也會中 |
|---|---|---|
| `/nextrole:setup` | 第一次設定、之後改設定 | 「設定求職工具」 |
| `/nextrole:search` | 天賦＋技能問卷 → 廣撒搜尋 104/Cake/LinkedIn → 評分 | 「找工作」「想換工作」「找遠端工作」 |
| `/nextrole:board` | 職缺資料表、進度追蹤、適合度評分 | 「我投到哪了」「這個職缺值得投嗎」 |
| `/nextrole:resume` | 客製履歷與求職信 | 「幫我改履歷」「寫求職信」 |
| `/nextrole:interview` | 建面試素材、針對職缺出題、同步 Google 試算表 | （只能用指令叫） |
| `/nextrole:mock` | 模擬面試與復盤 | （只能用指令叫） |

> 最後兩個刻意不設自動觸發詞，避免跟你自己既有的面試相關 skill 互搶。

## 安裝（Claude Code）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
claude plugin marketplace add oliviahuang0880/nextrole
```

```bash
claude plugin install nextrole@nextrole
```

裝好後在 Claude Code 裡打 `/nextrole:setup` 開始。

## 在 Codex（或其他讀 AGENTS.md 的工具）使用

```bash
git clone https://github.com/oliviahuang0880/nextrole.git
cd nextrole
codex
```

然後說「幫我找工作」。差異：Codex 需要**在這個 repo 資料夾內**啟動才會載入指引；
爬蟲與評分引擎完全相同，問卷對話的細膩度取決於所用模型。

## 怎麼用

**第一次**

1. `/nextrole:setup` — 建 `~/.nextrole/`，登記你有幾種履歷、有哪些硬門檻條件
2. `/nextrole:search` — 天賦問卷（可跳過）＋ 技能問卷（35 題）→ 搜尋 → 評分
3. `/nextrole:board` — 打開職缺看板

**每天**

```bash
cd ~/.nextrole/bin && uv run serve.py
```

看板可以搜尋、依來源／狀態／分數篩選、點欄位排序、展開看評分細項，
每筆都能直接改狀態（想投／已投／面試中／已拒／Offer／略過）與備註，改完即時存回本機。

⚠️ **不要用 `file://` 開**，職缺連結會空白、狀態也存不回去。

**看到想投的**

1. `/nextrole:board` 對那幾筆做適合度評分 → 決定投不投
2. `/nextrole:resume` 客製履歷與求職信
3. `/nextrole:interview` 準備面試題
4. `/nextrole:mock` 練一場

## 兩套評分，分工不同

**機器分（0–100）** 是廣篩用的。自動全跑，看關鍵字命中：
總分 = 技能契合度 (60%) + 天賦契合度 (40%) − 負向懲罰。
沒做天賦問卷時自動切 100% 技能；命中職稱再 ×2；冷門關鍵字出現在職稱直接排除。

**適合度評分（13 分）** 是決定投不投用的。你在看板上勾哪幾筆才算，因為每筆都要讀完整 JD：

- 產業關係 1–4、職務重疊 1–4、條件符合 1–5
- ➕ **硬門檻**：一條不符合就直接被刷掉的條件（英文流利、必備 N 年年資、必備某產業實戰）。
  這個框架原本沒有，但它比三個指標加起來更能解釋「為什麼投了沒回音」

投遞門檻預設 7 分，但**每個人的實際命中率不同**。投到十家以上之後跑一次校準：

```bash
cd ~/.nextrole/bin && uv run calibrate.py
```

它會統計各分數段投遞後的回應率，告訴你哪個分數以下幾乎沒進面試 —— 那才是你真正的門檻。
順便點出「沒回應、也沒踩到已知硬門檻」的那幾家，那通常是你還沒登記的硬門檻。

## 資料放哪

**全部在 `~/.nextrole/`，沒有上傳，這個 repo 裡不含任何人的求職素材。**

```
~/.nextrole/
├── config.json      設定
├── profile.json     問卷關鍵字與權重（覆蓋前自動備份）
├── board.json       職缺主檔
├── kit/             你的事實庫、故事庫、口徑、弱點清單
├── resumes/         主履歷與各職缺的客製版
├── interviews/      各職缺的面試題與模擬復盤
└── output/          搜尋結果與看板
```

⭐ **重跑搜尋只會更新分數，不會動你的狀態、備註與適合度評分。**

Google 試算表是**選用**的輸出。設定了才會同步，而且每次寫入前都會先問過你 ——
你很可能同時在瀏覽器開著同一份表在改。

## 選用：每天自動跑

```bash
ln -sf ~/.nextrole/bin/daily_run.sh ~/.nextrole/daily_run.sh
```

再用 `launchctl load ~/Library/LaunchAgents/<你的 plist>` 排程（macOS），
或用 cron／排程工作呼叫 `~/.nextrole/bin/daily_run.sh`。
它會跑 `run_search.py --diff-against auto`，本次新出現的職缺在看板上標 ✨。

## 需要

- [Claude Code](https://docs.claude.com/claude-code)，或 [Codex](https://openai.com/codex/) 等會讀 `AGENTS.md` 的 AI 工具
- [uv](https://docs.astral.sh/uv/)（偵測到沒裝會問是否代裝）
- **不需要任何 API key，也不需要 `.env`**

### 選用：走 proxy（爬蟲被擋時）

```bash
export PROXY_URL=http://user:pass@host:port        # http、https 都走這個
# 或分別指定：
export PROXY_URL_HTTP=http://host:port
export PROXY_URL_HTTPS=http://host:port
```

不設（預設）就是直連。

## 開發

```bash
uv run scripts/selftest.py
```

在暫存目錄跑一次完整資料流，順便稽核這個 repo 裡有沒有混進試算表 ID、Email、
電話或薪資帶 —— 這是公開 repo，個人素材一律不進來。

## 已知限制

- 預設搜尋台灣的 104 / Cake / LinkedIn（約 300–400 筆／次）；選亞太／全球／遠端時
  104 自動跳過、LinkedIn 改撈對應地點（亞太掃 7 城會多 5–8 分鐘）
- Cake / LinkedIn 改版時可能爬不到。搜尋跑完會印一段「健檢」，某一站掛掉、
  結果被條件濾光、或沒有職缺過門檻時都會明講原因與建議，不會靜默丟一份空報表
- 不做帳號、雲端儲存

## 授權

MIT
