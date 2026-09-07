---
name: search
description: 求職／找工作／換工作流程，預設台灣、可選海外/全球/遠端。用對話引導使用者完成天賦問卷（可選，邀朋友看自己天賦）與技能問卷（35 題情境式自評），產出個人化關鍵字後，到 104/Cake/LinkedIn 廣撒搜尋並用通用能力評分（不替使用者預設領域偏好），輸出可篩選的 HTML 報表並併進職缺看板。觸發詞：找工作、求職、換工作、找職缺、職涯盤點、海外求職、全球求職、遠端工作、remote job、job search、台北求職、轉職、想換跑道。
---

# NextRole — 求職盤點 Skill（台灣／亞太／全球／遠端）

幫使用者透過對話完成「天賦＋技能」雙面向問卷，產出個人化關鍵字檔，自動搜尋 104/Cake/LinkedIn 並評分。

本 skill 必須自足執行，只依使用者指示、本 skill 的 `rules/`、`templates/`、`references/`、`examples/` 與 `scripts/`。細節判準一律寫在 `rules/`，輸出格式一律寫在 `templates/`，**用到才讀**。

## Output Contract

- 主要持久產物是 `~/.nextrole/profile.json`（覆寫前 `profile_io.py` 會自動備份一份 `profile.<UTC ts>.json`）。
- 搜尋產出放 `~/.nextrole/output/`：`results_<ts>.html` + `.csv`、重算用的 `_jobs_cache.json`，以及看板 `board.html`。
- 搜尋收尾會把結果併進 `~/.nextrole/board.json`。**併入只更新分數與 last_seen，使用者在看板上設的狀態／備註／契合度一律保留** — 不得覆寫。
- `profile.json` 只放長期偏好：關鍵字、權重、`filters`、`negative`、`scoring`。**不得**寫入單次執行才用的東西（`extra_queries` 只當次有效）。
- Phase 5 收尾若使用者給了主履歷，另外寫 `~/.nextrole/resumes/master-<id>.md`
  並在 `config.json` 的 `resume_versions` 補一筆。他說「先不要」就什麼都不寫。
- 所有資料留在使用者本機，不上傳。不需要也不得要求 `ANTHROPIC_API_KEY`。
- 對話輸出有兩個固定格式：關鍵字清單用 `templates/keywords-report.md`，搜尋回報用 `templates/search-summary.md`。兩者都不得殘留 `{{...}}` 填位符號。
- 未收到使用者對 Phase 4 提問的回答前，不得寫入 `profile.json`，也不得開始搜尋。

## 流程順序（嚴格遵守）

```
[Phase 0] 環境偵測 → [Phase 1] 起點 → [Phase 2] 天賦問卷（可跳過）
        → [Phase 3] 技能問卷（35 題，必做）→ [Phase 4] 進階偏好 → [Phase 5] 搜尋與回報
```

跳過天賦問卷時直接接 Phase 3。重來時讀已存的 profile，可只跑 Phase 4–5。

# SOP

## Phase 0 -- 環境偵測

1. READ 讀取 `rules/環境偵測與降級模式判準.md`，跑 `command -v uv` 判斷完整模式或降級模式。
   同時確認 `~/.nextrole/bin` 與 `~/.nextrole/config.json` 存在；不存在就先跑 `/nextrole:setup`。
2. THINK 若沒有 `uv` 但有 bash，依規則詢問使用者是否同意安裝；未同意前不得執行安裝指令。
3. THINK 確認本次走完整模式或降級模式，後續 Phase 3 收尾與 Phase 5 的做法依此分流。

## Phase 1 -- 起點選擇

1. READ 檢查 `~/.nextrole/profile.json` 是否存在，確認是首次執行還是回訪。
2. WRITE 打招呼並說明流程：

   > 「歡迎用 NextRole！流程是這樣：先做天賦問卷（請 5–6 位認識你的人寫『你眼中的我』，幾分鐘到幾天看你怎麼安排），再做技能問卷（~35 題情境式自評，10 分鐘左右），最後搜尋。
   >
   > 想先做天賦問卷嗎？也可以**跳過直接做技能問卷**。」

3. WRITE 若 profile 已存在，多問一句：「你之前做過了。想直接重新搜尋，還是重做問卷？」選前者就跳到 Phase 4。

## Phase 2 -- 天賦問卷（可跳過）

1. READ 讀取 `examples/invitation_template.md`，把邀請文字唸給使用者，請他複製傳給 5–6 位**認識他的人**，並提醒「不急，可以慢慢等回覆，回來貼給我就行」。
2. READ 接收使用者貼回的朋友回覆（一則一則或一次全貼都行），每收到一則簡短確認「收到 N 則了」。
3. THINK 收到 ≥ 3 則且使用者說「彙整」，或 ≥ 5 則時主動詢問「夠了要彙整嗎？」，再由**你自己**把所有回覆濃縮成 6–10 個最常被提到的共通天賦（繁體中文短詞，不要句子／公司名／人名／地名）。不得呼叫任何外部 AI API。
4. WRITE 把彙整結果寫成 `/tmp/talents.json`（JSON 陣列，不要 code fence）。
   ⭐ **每一個天賦都要帶 `syn`：2–3 個 JD 真的會這樣寫的說法。**

   ```json
   [{"term":"傾聽溝通","en":"communication","weight":2,
     "syn":["溝通協調","跨部門溝通","stakeholder communication"]},
    {"term":"分析判斷","en":"analysis","weight":2,
     "syn":["數據分析","問題分析","data analysis"]}]
   ```

   為什麼一定要有 `syn`：朋友寫的是「面對不確定性」「好奇追問」，JD 寫的是
   「抗壓性」「主動探究」；朋友寫「跨部門溝通」，JD 寫「跨部門協作」。
   中文比對走子字串，**差一個字就是 0 分**。實測沒有 `syn` 時，七個天賦詞裡
   只有一個曾經命中過任何一份 JD —— 等於整份天賦問卷對評分沒有作用。
   `term` 保留朋友的原話（那是給履歷和面試用的），`syn` 負責讓它在 JD 裡找得到。

5. WRITE 跑 `cd ~/.nextrole/bin && uv run merge_talents.py /tmp/talents.json`，列出彙整出的天賦給使用者看，接著進 Phase 3。

## Phase 3 -- 技能問卷（35 題，必做，不可跳）

1. READ 讀取 `rules/技能問卷對話節奏判準.md` 與 `references/method2_skills.json`，確認 6 組情境、題目節奏、進度條與選項客製化的硬性要求。
2. WRITE 依已載入規則逐題提問，內部累積 `classifications` 與 `notes`，過程中不把這兩包 dump 給使用者。
   每組開頭要說「這組跟你想找的工作沒關係就說『跳過』」（見該規則 Rule 7）。
3. WRITE 問完 35 題後把結果餵進 profile：

   ```bash
   cd ~/.nextrole/bin && echo '{"classifications": {...}, "notes": {...}}' | uv run build_profile.py
   ```

   降級模式沒有 `uv`，改依 `rules/環境偵測與降級模式判準.md` 的替代路徑處理。
4. READ 讀取 `templates/keywords-report.md` 與 `templates/keywords-report.example.md`。
5. WRITE 依樣板**主動**列出方法一天賦、方法二技能（標 🔍 = 會拿去搜尋）、負向詞與 JD 補充詞。這是強制動作，不要等使用者問。

## Phase 4 -- 進階偏好

1. READ 讀取 `rules/提問與選項撰寫判準.md` 與 `rules/中立與加權判準.md`，確認提問格式、推薦選項的禁區與三種加權機制的分工。
2. WRITE 問 **4a 想找的職稱**（必問，直接決定撈得到什麼）。

   ```
   你想找的職稱是什麼？講幾個你會拿去搜尋的說法就好。
   例：產品經理、Product Manager、產品企劃
   ```

   ⭐ **這是唯一會用「職稱」去撈職缺的地方。** 技能問卷產出的是「研究」「分析」這類
   通用能力詞，用它們去搜 104 會撈回一堆不相干的東西。職稱才撈得到對的職缺。
   收到之後寫進 `filters` 同層的 `candidate_titles`（字串陣列），`run_search.py` 會把它
   排在搜尋詞的第一順位。中英文都給更好，兩邊的站命中率不一樣。
   使用者說「不知道」就照技能問卷的結果建議 2–3 個，**列給他確認過**才寫入。

3. WRITE 問 **4b 地區**（必填、無預設、可複選）：台灣／亞太／全球／全遠端。含台灣要追問哪些城市。依答案寫入 `filters.regions`（`tw`/`apac`/`global`/`remote`）與 `filters.allowed_cities`；`filters.allow_remote` 維持 `true`。提醒亞太會掃 7 個城市、整跑約 5–8 分鐘。
4. WRITE 問 **4c 領域偏好**（選填，影響**評分**）。有填 → 由你生 8–15 個該領域的技能／工具／職能詞，列給使用者確認後寫進 `field_terms`（`weight: 3`）並把 `scoring.use_field_terms` 設 `true`。不填 → 維持 `false`，純通用能力評分。**這題不得標推薦選項。**
5. WRITE 問 **4d 貼有興趣的 JD**（選填，影響**搜尋**）。抽 5–8 個中立技能／領域詞，列給使用者確認後併進本次的 `extra_queries`，不寫進 profile。
6. WRITE 問 **4e 負向詞**（必問）。先講清楚「職稱命中→整筆剔除／內文命中→扣分」的差別，再給 A–H 選項讓使用者複選或自由填答。依 `rules/中立與加權判準.md` Rule 4 的格式寫入 `negative`；使用者回「沒有」就完全不動。
7. THINK 確認每一題都已收到使用者回答；有任何一題還沒回答就停在這裡，不得往下走。
   ⚠️ 再確認一次搜尋詞夠不夠：`candidate_titles` ＋ `q:true` 的技能詞加起來
   少於 3 個就要提醒使用者，否則搜尋會回 `NO_QUERIES` 或 `THIN_RESULT`。用 `python3` 直接改 `~/.nextrole/profile.json` 即可，不用另寫腳本。

## Phase 5 -- 搜尋與回報

1. WRITE 執行搜尋（爬蟲約 1–3 分鐘，選亞太約 5–8 分鐘）：

   ```bash
   cd ~/.nextrole/bin && uv run run_search.py --queries <extra_queries...>
   ```

   降級模式改跑 `uv run browser_urls.py` 印三站搜尋網址讓使用者自己貼到瀏覽器。
2. READ 讀取 `rules/搜尋結果健檢判準.md`，對照 stdout 最後一行的 `健檢代碼：`，判斷這次結果是否健康。
3. READ 讀取 `templates/search-summary.md` 與 `templates/search-summary.example.md`。
4. WRITE 依樣板回報筆數、來源分佈、健檢結論與具體建議、開啟方式（**必須提醒不要用 `file://`**）。健檢代碼不是 `OK` 時，不得用「完成」的語氣草草帶過。
   收尾要告訴使用者結果已併進看板，用 `/nextrole:board` 或 `cd ~/.nextrole/bin && uv run serve.py` 看。
5. WRITE ⭐ **接著問主履歷**（搜尋完就問，不要等他自己想到）：

   > 「接下來要判斷這些職缺值不值得投，我需要你的履歷 —— 契合度診斷要拿你實際做過什麼
   > 去對照 JD 的職責清單，沒有履歷我只能瞎猜。
   > 貼上來或給我檔案路徑都行，會存在 `~/.nextrole/resumes/`，不會離開你的電腦。」

   收到就存成 `~/.nextrole/resumes/master-<id>.md`，`<id>` 用他講的方向命名（`pm`、`consultant`…），
   並順手把 `config.json` 的 `resume_versions` 補一筆。
   他說「先不要」就記著，等他真的要診斷時再問一次 —— **但不要靜默跳過這一題**。
6. READ 回頭檢查回報內容有無殘留填位符號、有無違反 `rules/中立與加權判準.md`（例如替使用者推測該走哪個領域）；不符合就立即修正。

## Phase 6 -- 重新找一次（回訪時）

1. THINK 判斷使用者要重做到哪一步：
   - 想調整地區／領域／JD → 回 Phase 4。
   - 只想重抓新職缺 → `uv run run_search.py`。
   - 只想調關鍵字重算、不重爬（最快，約 5 秒）→ `uv run run_search.py --from-cache`。
2. WRITE 定期重跑時加 `--diff-against auto`，會自動挑 `./output` 裡最新一份舊 CSV 比對，本次新出現的職缺在 HTML 與 CSV 都標 ✨。第一次跑沒有舊 CSV 會自動略過、不報錯。
3. THINK Skill 不設次數上限，使用者自費 token，要找幾次都行。想無人值守可搭配 cron / launchd / scheduled task 呼叫上面那行。

## 檔案位置摘要

- Skill 本體：本 plugin 的 `skills/search/`（判準在 `rules/`、輸出格式在 `templates/`）
- 腳本：`~/.nextrole/bin`（symlink → plugin 的 `scripts/`）
- 使用者 profile：`~/.nextrole/profile.json`（含自動備份）
- 搜尋產出：`~/.nextrole/output/`；職缺主檔 `~/.nextrole/board.json`
- 參考資料：`skills/search/references/method2_skills.json`、`skills/search/examples/invitation_template.md`

## 已知地雷

- HTML 結果**不能用 `file://` 開**，職缺連結會空白、看板的狀態也存不回去。用 `cd ~/.nextrole/bin && uv run serve.py`。
- Cake / LinkedIn 改版時可能爬不到 — 健檢會回 `SOURCE_DEAD:<站名>`，照 `rules/搜尋結果健檢判準.md` 處理。
- 搜尋每個關鍵字跑三站後 sleep 1.5 秒節流，避免被擋。
