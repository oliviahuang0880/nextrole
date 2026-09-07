# NextRole — AI 求職工具（Claude Code / Codex）

> 搜職缺 → 評分 → 決定投不投 → 客製履歷 → 準備面試題 → 模擬面試 → 追蹤進度。
> 同一份資料串到底，**全部存在你自己的電腦上**。

對話跑問卷與判斷，Python 跑爬蟲、評分與產表。預設台灣，也可選海外（亞太／全球／全遠端）。

## 六個 skill

| 打這個 | 做什麼 | 自然講也會中 |
|---|---|---|
| `/nextrole:setup` | 第一次設定、之後改設定 | 「設定求職工具」 |
| `/nextrole:search` | 天賦＋技能問卷 → 廣撒搜尋 104/Cake/LinkedIn → 評分 | 「找工作」「想換工作」「找遠端工作」 |
| `/nextrole:board` | 三頁看板：收件匣、契合度診斷、投遞追蹤 | 「我投到哪了」「這個職缺值得投嗎」 |
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

看板有三頁，左側可切換。**流動方向是單向的**，東西只會往前走：

| 頁 | 回答的問題 | 你在這裡做什麼 |
|---|---|---|
| ① 職缺收件匣 | 這批搜尋結果哪些值得留下？ | `✓` 收起來（下次不出現）、`☆` 存進診斷。兩個互不相干 |
| ② 契合度診斷 | 留下的這幾個，到底投不投？ | 挑幾筆做契合度診斷，決定了按「開始投遞」 |
| ③ 投遞追蹤 | 投出去的現在到哪了？ | 改狀態、記備註，看漏斗轉換率 |

第一頁的**評分**（0–100，關鍵字命中）是用來判斷**搜尋詞抓得準不準**，不是判斷該不該投。
真正決定投不投的是第二頁的**契合度診斷**（13 分制，要讀完整 JD）。
收起來或移出的職缺都沒有不見，各自的彈窗找得回來。

⚠️ **不要用 `file://` 開**，職缺連結會空白、改動也存不回去。

**看到想投的**

流程走在對話裡，畫面負責讓你看見結果 —— 每一步做完，工具會主動問你下一步。

1. 搜尋完 → 問你要不要放一份履歷進來。**什麼格式都行**，PDF、Word、純文字或直接貼，
   工具自己轉。契合度診斷要拿它對照 JD
2. `/nextrole:board` 對存起來的職缺做契合度診斷 → 決定投不投
3. 診斷完 → 問你要不要客製履歷 → `/nextrole:resume` 產履歷與求職信
4. `/nextrole:interview` 準備面試題 → 想在手機上複習就同步到 Google 試算表
5. `/nextrole:mock` 練一場 → 面試完回 `/nextrole:interview` 復盤

⭐ **在別的地方看到的職缺，直接把 JD 貼給它就好**，不用先加進看板。
貼進來的會自己進看板、先做契合度診斷，再走客製履歷 —— 跟從看板挑的走同一條路。
貼的時候把原始網址一起給，這筆就會跟爬蟲撈到的合而為一，不會變成兩筆。

⚠️ **契合度診斷沒有你的履歷就別做。** 三個指標全部要拿你實際做過什麼去對照 JD，
沒有這份資料，AI 會憑對話印象猜 —— 而且猜得很像真的。

## 兩套評分，分工不同

**評分（0–100）** 是廣篩用的。自動全跑，看關鍵字命中：
總分 = 100 × 技能契合度 + 天賦加分（上限 15） − 負向懲罰。
命中職稱再 ×2；冷門關鍵字出現在職稱直接排除。

⭐ **天賦只加分，不當分母。** 技能詞（研究、分析、專案管理）本來就是 JD 的用語，
天賦詞是朋友形容你的話（「面對不確定性」），JD 幾乎不會這樣寫 —— 命中率差一個量級。
早期版本把兩者放進同一個線性加權，結果是**做過天賦問卷的人分數反而更低**，
用了功能反而被懲罰。現在天賦只會往上加，而且彙整時會一起產出 JD 慣用語當同義詞。

**契合度診斷（13 分）** 是決定投不投用的。你在看板上勾哪幾筆才算，因為每筆都要讀完整 JD：

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

⭐ **重跑搜尋只會更新分數，不會動你的狀態、備註與契合度診斷。**

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

想看版面長怎樣（不用真的跑爬蟲）：

```bash
uv run scripts/demo_data.py
```

會產一份 60 筆的虛構資料到 `~/.nextrole-demo/`，**不會碰到你自己的 `~/.nextrole/`**。
跑完照它印的指令開 server 就能點。截圖也用這份，不會截到真實職缺。

⚠️ 改了 `ui.py` 或 `render_board.py` 之後**要重開 `serve.py`** ——
它把模組留在記憶體裡，每次寫回都會用舊的那份重畫，會蓋掉你手動產生的檔案。

⚠️ 改了任何 `SKILL.md` 之後，slash command 不會馬上跟著變。它讀的是 plugin 快取，
不是這個工作目錄。要三步，缺一不可：

```bash
claude plugin marketplace update nextrole && claude plugin update nextrole@nextrole
```

然後**重開 Claude Code**。注意是 `plugin update` 不是 `plugin install` ——
對已經裝好的 plugin，`install` 是 no-op，會安靜地什麼都不做。
（Python 腳本不受影響，它們走 `~/.nextrole/bin` symlink，指到這個工作目錄，改了即時生效。）

版面規範在 [`design.md`](design.md)。改任何一頁之前先讀那份，
樣式一律寫在 `scripts/ui.py` 的共用 CSS，不要為單一頁另寫。

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
