---
name: setup
description: NextRole 求職工具的第一次設定與後續改設定：建立本機資料夾 ~/.nextrole/、登記 Google 帳號與面試準備試算表、設定投遞門檻與硬門檻條件、登記履歷版本。使用者說「第一次用 NextRole」「設定求職工具」「改我的求職設定」「登記我的履歷版本」「設定投遞門檻」時使用。也在其他 NextRole skill 發現 ~/.nextrole/config.json 不存在時被叫來補跑。
---

# NextRole 設定

建立與維護 `~/.nextrole/` — 使用者所有個人素材的家。
**這個 plugin 本身不含任何人的資料**，所有內容都由使用者在這裡自己建。

## Output Contract

- 唯一會寫的地方是 `~/.nextrole/`。不得把使用者的任何素材寫進 plugin 目錄或任何 git repo。
- `config.json` 只放設定，不放素材。素材放 `kit/`。
- 每一題都要收到回答才寫入。沒問到的欄位維持 `null`，不要猜。
- 使用者說「跳過」的題目就留空 — 空欄位是合法狀態，其他 skill 會在需要時再問。

# SOP

## Phase 0 -- 建骨架

1. WRITE 跑 `init_store.py`。第一次跑時 `~/.nextrole/bin` 還不存在，用本 plugin 的 `scripts/`：

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT:-$HOME/.nextrole/bin}/scripts/init_store.py" 2>/dev/null \
     || uv run ~/.nextrole/bin/init_store.py
   ```

   它會建目錄、`bin` symlink、空的 `config.json` 與 `kit/` 範本。已存在的檔案不會被覆寫，可以重複跑。
2. READ 讀回 `~/.nextrole/config.json`，確認哪些欄位還是 `null` — **只問這些**，已經有值的不要重問。

## Phase 1 -- 逐項設定

依 `skills/search/rules/提問與選項撰寫判準.md` 的格式提問（一次一題、附選項表、留「其他」）。
以下每一題都可以跳過。

1. WRITE **1a 履歷版本**（`resume_versions`）
   問：「你手上有幾種履歷？各自是投什麼方向的？」
   例：一份偏產品經理、一份偏解決方案顧問。寫成 `[{"id":"pm","label":"PM 版","for":"產品策略、0→1、數據驗證"}]`。
   只有一種就寫一筆。之後 `/nextrole:resume` 會照 JD 訊號挑版本。
2. WRITE **1b 硬門檻條件**（`hard_blockers`）
   先解釋這是什麼：**不是「我比較弱」，是「一條就直接被刷掉」的條件** — 例如必備英文流利、必備 N 年某職務年資、必備特定產業實戰。
   問：「以你目前的條件，看到哪些要求你會知道自己一定不會過？」
   寫成字串陣列。空的也可以，之後評分時發現了再補。
3. WRITE **1c 投遞門檻**（`fit_threshold`，預設 7）
   說明：適合度評分滿分 13，框架的建議是 7 分以上值得投，但每個人的實際命中率不同。
   先用預設值，等累積夠多投遞結果後 `/nextrole:board` 會自動回報建議值。這題通常直接用預設。
4. WRITE **1d 求職信字數上限**（`cover_letter_max_chars`，預設 300）
5. WRITE **1e Google 帳號與試算表**（`google_email`、`spreadsheet_id`）
   只有要把面試題同步到 Google 試算表時才需要。問：「要把面試準備同步到 Google 試算表嗎？」
   - 要，而且已經有一份 → 請他貼試算表網址，從 `/spreadsheets/d/<ID>/` 取出 ID。
   - 要，但還沒有 → 用 `mcp__google_workspace__create_spreadsheet` 建一份，標題讓他決定，建好後把 ID 寫進 config，並把連結給他。
   - 不用 → 兩欄留 `null`，`/nextrole:interview` 就只寫本機檔案。
   ⚠️ Google 工具回報需要授權時，把授權連結**原樣**貼給他點，不要自己想辦法繞過。

## Phase 2 -- 寫入與回報

1. THINK 確認每一題都已收到回答或明確跳過。還有沒問到的就停在這裡。
2. WRITE 用 `python3` 直接改 `~/.nextrole/config.json` 即可，不用另寫腳本。
3. WRITE 回報：哪些設好了、哪些留空、下一步可以做什麼。

   > 設定好了。接下來：
   > - `/nextrole:search` 做問卷並開始找職缺
   > - `/nextrole:board` 看職缺看板
   > - `/nextrole:interview` 建面試素材（故事庫、事實庫、口徑）

## Phase 3 -- 之後改設定（回訪）

1. READ 讀現有 `config.json`，把目前的值列給使用者看。
2. WRITE 問他要改哪一項，只改那一項，其餘不動。

## 檔案位置

| 路徑 | 內容 |
|---|---|
| `~/.nextrole/config.json` | 設定（不放素材） |
| `~/.nextrole/kit/` | 事實庫、故事庫、口徑、弱點 — 由 `/nextrole:interview` 填 |
| `~/.nextrole/board.json` | 職缺主檔 |
| `~/.nextrole/resumes/` | 主履歷與各職缺的客製版 |
| `~/.nextrole/output/` | 搜尋結果與看板 |
| `~/.nextrole/bin` | → 本 plugin 的 `scripts/` |

## 已知地雷

- `~/.nextrole/bin` 是 symlink。plugin 更新或搬家後指向會失效 — 重跑 `init_store.py` 會自動更新指向。
- 這個 plugin 的目錄底下**永遠不該出現使用者的素材**。發現有就是 bug，要移到 `~/.nextrole/`。
