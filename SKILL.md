---
name: nextrole
description: 台灣求職／找工作／換工作流程。用對話引導使用者完成天賦問卷（可選，邀朋友看自己天賦）與技能問卷（35 題情境式自評），產出個人化關鍵字後，到 104/Cake/LinkedIn 中立廣撒搜尋並評分，輸出可篩選的 HTML 報表。觸發詞：找工作、求職、換工作、找職缺、職涯盤點、job search Taiwan、台北求職、轉職、面試準備、想換跑道。
---

# NextRole — 台灣求職盤點 Skill

幫使用者透過對話完成「天賦＋技能」雙面向問卷，產出個人化關鍵字檔，自動搜尋 104/Cake/LinkedIn 並評分。**TW only**。

## 流程順序（嚴格遵守）

```
[起點] → ① 天賦問卷（可跳過）
       → ② 技能問卷（35 題，必做，不可跳）
       → ③ 進階偏好（地區必填、領域/JD 選填）
       → ④ 搜尋並產出 HTML
```

跳過天賦問卷時直接接 ②。重來時讀已存的 profile，可只跑 ③④。

## 0. 環境偵測（每次啟動先做）

跑 `command -v uv` 判斷：
- **有 uv** → 走完整模式（跑爬蟲）
- **沒有 uv 但有 bash** → 詢問「我可以幫你裝 uv 嗎？這是個免費工具，會幫你跑 Python 腳本，一行指令裝完：`curl -LsSf https://astral.sh/uv/install.sh | sh`。同意嗎？」同意就跑、不同意走降級模式。
- **完全沒 bash（claude.ai 網頁/桌面 app）** → **降級模式**：只用對話跑問卷（②），最後輸出關鍵字 JSON ＋ 三個站的搜尋網址清單貼到瀏覽器（步驟 4 改用 `references/method2_skills.json` 純對話、步驟 6 改成貼網址）。

## 1. 起點選擇

打招呼後問：

> 「歡迎用 NextRole！流程是這樣：先做天賦問卷（請 5–6 位認識你的人寫『你眼中的我』，幾分鐘到幾天看你怎麼安排），再做技能問卷（~35 題情境式自評，10 分鐘左右），最後搜尋。
>
> 想先做天賦問卷嗎？也可以**跳過直接做技能問卷**。」

如果 `~/.nextrole/profile.json` 已存在，多問一句：「你之前做過了。想直接重新搜尋，還是重做問卷？」

## 2. 天賦問卷（貼上模式，可跳過）

如果使用者選擇做：

1. 讀 `examples/invitation_template.md`，把預設邀請文字唸給使用者，請他複製傳給 5–6 位**認識他的人**。
2. 提醒「不急，可以慢慢等回覆。回來貼給我就行」。
3. **使用者貼回朋友回覆**（一則一則或一次全貼都行）。每收到一則簡短確認「收到 N 則了」。
4. 收到 ≥ 3 則後使用者說「彙整」或 ≥ 5 則時主動詢問「夠了要彙整嗎？」。
5. **由你（對話的 Claude）直接彙整**，不要呼叫任何 Anthropic API：
   - 任務：把所有回覆濃縮成 6–10 個**最常被提到**的共通天賦或特質，繁體中文短詞（單詞或短語、不要句子、不要公司名/人名/地名）。
   - 輸出 JSON 陣列（不要用 markdown code fence）：
     ```json
     [{"term":"傾聽溝通","en":"communication","weight":2},
      {"term":"分析判斷","en":"analysis","weight":2}, ...]
     ```
6. 把 JSON 寫到 `/tmp/talents.json`，跑：
   ```bash
   cd ~/.claude/skills/nextrole/scripts && uv run merge_talents.py /tmp/talents.json
   ```
7. 列出彙整出來的天賦給使用者看，接著進入 ③ 技能問卷。

## 3. 技能問卷（35 題，必做）

讀 `references/method2_skills.json`。它有 6 組（rounds），每組有情境句 + 一組技能。

### 對話節奏（重要）

- **進入新組時**，先把 `scenario` 情境句唸給使用者一次。
- **每一題都要再寫一個更具體的小情境**（不只是把組情境貼過來），並把 4 個選項用該題情境的語言「客製」描述，不要只列名稱。
- 每題格式：
  > **Q1.「研究」**
  > 情境：老闆丟你一個全新的題目「我們要不要做這個產品？」，沒有人做過，也沒有資料。你要去訪談使用者、查競品、看市場報告，把事情查到水落石出。
  >
  > 1️⃣ **On Fire** — 一頭栽進去查到忘記吃飯，這種題目最有趣
  > 2️⃣ **Heating Up** — 做得還不夠扎實，但很想練到能獨立扛這種題目
  > 3️⃣ **Burnout** — 查得來，但常做會累，比較想偶爾為之
  > 4️⃣ **Cold** — 看到一堆未知資訊就頭大，能不查就不查
  >
  > 💬 也可以描述實際工作情境，我幫你判斷。
- 不可以省略情境或選項描述，即使第二題之後也一樣。每組組情境句也要每題重貼在問題上方（用引用 quote 即可），讓使用者隨時看得到當下情境。
- 使用者回 1/2/3/4 → 立刻問下一題。
- 使用者打文字描述工作情境而不是 1/2/3/4 時 → 你來判斷分類，回覆「判定為 X — 理由」再接下一題。
- 每組結束問一次：「這組（XX類）有沒有想補充的？例如某個技能跟特定領域連在一起？沒有就回『沒有』」存到 notes。

### 內部累積（不給使用者看）

- `classifications`: `{<skill_key>: "on_fire"|"heating"|"burnout"|"cold"}`
- `notes`: `{<round_category>: "補充文字"}`

### 完成後

把 classifications + notes 用 JSON 透過 stdin 寫進 `build_profile.py`：
```bash
cd ~/.claude/skills/nextrole/scripts && echo '<JSON>' | uv run build_profile.py
```
JSON 結構：`{"classifications": {...}, "notes": {...}}`

成功後 `~/.nextrole/profile.json` 已更新（含天賦問卷的 talents 自動合併）。

### 完成後要主動列關鍵字給使用者看

跑完 `build_profile.py` 後（不要等使用者問）立刻列出：

1. **方法一：天賦關鍵字** — 從 `method1_positive` 讀，附權重（⭐ 數量）
2. **方法二：技能關鍵字** — 從 `method2_positive` 讀，分 🔥 On Fire / ♨️ Heating Up 兩段，每個技能旁邊用 🔍 標出 `q:true` 的（這些才會被拿去三站搜尋）
3. **Burnout / Cold** — 從 `negative` 讀，說明會扣分或排除
4. **JD 抽出的補充關鍵字**（如果有跑步驟 4c）

範例輸出格式參考：

```
━━━ 方法一：天賦關鍵字（朋友彙整 N 個）━━━
  ⭐⭐⭐ 傾聽溝通
  ⭐⭐ 協調化解
  ...

━━━ 方法二：技能關鍵字 ━━━
🔥 On Fire
  🔍 研究
     管理人員
♨️ Heating Up
  🔍 規劃
     做決策
（🔍 = 會拿去三站搜尋的關鍵字）
```

這是強制動作，每次跑完問卷都要做。

## 4. 進階偏好

依序問三題：

### 4a. 地區（必填，無預設）
> 「想找哪些地區？例如：台北、新北、桃園、新竹、台中、高雄⋯ 你可以講多個。也可以說『全台都看』或『遠端優先』。」

把答案寫入 profile 的 `filters.allowed_cities`（陣列，空陣列 = 全台不過濾）和 `filters.allow_remote`（true/false）。用 `python3` 直接修改 `~/.nextrole/profile.json` 即可（小改動，不用另寫腳本）。

### 4b. 領域偏好（選填）
> 「想偏向某個領域嗎？例如 UX、PM、行銷、data analyst⋯（不填 = 中立廣撒，三個站把所有相關技能職缺都掃過一次）」

有填 → 暫存到一個變數 `extra_queries` 等下一步用，並提醒「加了就不是中立、會偏向這方向」。

### 4c. 貼有興趣的 JD（選填）
> 「如果你最近有看到喜歡的職缺，把職缺描述貼給我（一段、多段、多則都行），我從裡面抽出領域關鍵字。」

收到 JD 文字後：
- **由你（對話的 Claude）直接抽 5–8 個中立技能/領域關鍵字**（繁體中文，不要公司名/地名）
- 列給使用者確認：「我抽到這些：研究、產品策略、跨部門協作⋯ 要全部加入嗎？還是挑幾個？」
- 確認後合併進 `extra_queries`

## 5. 執行搜尋

```bash
cd ~/.claude/skills/nextrole/scripts && uv run run_search.py --queries <extra_queries...>
```

爬蟲跑 1–3 分鐘。完成後告訴使用者：
- 共撈到 N 筆、推薦 M 筆
- 開啟方式（**必須提醒不要用 file://**）：
  ```bash
  cd output && python3 -m http.server 8765
  ```
  然後開 `http://localhost:8765/results_<timestamp>.html`

降級模式：跑 `uv run browser_urls.py` 印出三個站的搜尋網址清單給使用者貼到瀏覽器。

## 6. 重新找一次

使用者下次回來說「我要重新找職缺」時：
- `~/.nextrole/profile.json` 已存在 → 跳到步驟 4（重新問地區/領域/JD）
- 或者「不調整關鍵字、只想重抓新職缺」→ 直接 `uv run run_search.py`
- 或者「只調整關鍵字重算、不重抓」→ `uv run run_search.py --from-cache`

**Skill 不設次數上限**，使用者自費 token，要找幾次都行。

## 重要原則

- **中立搜尋**：使用者沒指定領域時用中立技能關鍵字搜尋。**不要**用「他是 X 行業」去判斷他適合哪些職缺，由分數呈現、由他決定。
- **不需要 ANTHROPIC_API_KEY**：彙整朋友描述、抽 JD 關鍵字都由你（對話的 Claude）做。
- **資料本機**：所有 profile 存在使用者本機 `~/.nextrole/`，沒有上傳。
- **覆蓋自動備份**：`profile_io.py` 在覆蓋 profile.json 前會自動 cp 一份 `profile.<UTC ts>.json`。
- **TW only**：地區限台灣，職缺站只爬 104/Cake/LinkedIn TW。

## 檔案位置摘要

- Skill 本體：`~/.claude/skills/nextrole/`
- 使用者 profile：`~/.nextrole/profile.json`（含備份）
- 搜尋產出：`./output/results_<ts>.html` + `.csv`（執行 claude 時的當前目錄下）
- 搜尋快取（重算用）：`./output/_jobs_cache.json`
- 參考資料：`references/method2_skills.json`、`examples/invitation_template.md`

## 已知地雷

- HTML 結果**不能用 file:// 開**，職缺連結會空白（瀏覽器安全機制）。必須用 `python3 -m http.server`。
- Cake / LinkedIn 改版時可能爬不到，先 ship、壞了砍 Cake/LinkedIn 改剩 104。
- 搜尋會 sleep 1.5 秒節流避免被擋（每個關鍵字三站）。
