---
name: setup
description: NextRole 求職工具的初始化與設定檢視：建立本機資料夾 ~/.nextrole/、修復 bin symlink、列出或修改目前設定。使用者說「第一次用 NextRole」「初始化求職工具」「改我的求職設定」「看我的設定」時使用。其他 NextRole skill 發現 ~/.nextrole/ 不存在時也會叫它來補建。
---

# NextRole 初始化

建立 `~/.nextrole/` — 使用者所有個人素材的家。
**這個 plugin 本身不含任何人的資料**，所有內容都由使用者透過工具自己建。

## 設計原則：這裡不問問題

⭐ **setup 只建骨架，不做設定問答。**

設定項目（履歷版本、硬門檻、試算表）**一律由真正要用到的 skill 在需要的那一刻問**：

| 設定 | 誰來問 | 什麼時候問 |
|---|---|---|
| `resume_versions` | `/nextrole:resume` | 第一次要客製履歷、而且還沒登記版本時 |
| `hard_blockers` | `/nextrole:board` | 做契合度診斷時發現了一條，才建議加進去 |
| `google_email`／`spreadsheet_id` | `/nextrole:interview` | 產出面試題之後、要上傳之前 |

**為什麼**：在使用者還沒有脈絡的時候問，他答不好 —— 問「你有幾種履歷」時他連主履歷都還沒放進來，
問「你的硬門檻是什麼」時他還沒看過任何 JD。答得敷衍，資料就是壞的。
到了真正用得到的那一刻，他手上剛好有 JD、有履歷、有面試題，答案才準。

## Output Contract

- 唯一會寫的地方是 `~/.nextrole/`。不得把使用者的任何素材寫進 plugin 目錄或任何 git repo。
- `config.json` 只放設定，不放素材。素材放 `kit/`。
- 空欄位是**合法且預期**的狀態，不要為了填滿而問。

# SOP

## Phase 0 -- 建骨架

1. WRITE 跑 `init_store.py`。

   ⚠️ **第一次跑時 `~/.nextrole/bin` 還不存在**，所以不能用它當路徑。
   載入這個 skill 時，環境會印出一行 `Base directory for this skill: <路徑>`，
   腳本就在它的 `../../scripts/`。用那個**絕對路徑**跑：

   ```bash
   uv run "<Base directory>/../../scripts/init_store.py"
   ```

   例：base 是 `~/.claude/plugins/cache/nextrole/nextrole/0.3.0/skills/setup`，
   就跑 `uv run ~/.claude/plugins/cache/nextrole/nextrole/0.3.0/scripts/init_store.py`。

   ⛔ 不要用 `$CLAUDE_PLUGIN_ROOT` —— 它在 Bash 工具裡不會被設定，
   而且第一次跑時 `~/.nextrole/bin` 也還不存在，兩條路都會失敗、什麼都建不出來。

   跑完會建目錄、`bin` symlink、空的 `config.json` 與 `kit/` 範本。
   已存在的檔案不會被覆寫，可以重複跑。之後就能用 `~/.nextrole/bin` 了。

2. WRITE 回報建了什麼，然後**直接給下一步**，不要再問設定：

   > 建好了。接下來：
   > - `/nextrole:search` 做問卷並開始找職缺
   > - `/nextrole:board` 看職缺看板（搜尋完才有東西）
   >
   > 履歷版本、硬門檻、Google 試算表這些設定不用現在決定，
   > 用到的時候對應的 skill 會問你。

## Phase 1 -- 看設定 / 改設定（使用者主動要求時）

1. READ 讀 `~/.nextrole/config.json`，把目前的值列給使用者看，空的就標「未設定」。
2. WRITE 問他要改哪一項，**只改那一項**，其餘不動。用 `python3` 直接改即可。

| 欄位 | 意思 |
|---|---|
| `resume_versions` | 履歷版本清單，`[{"id","label","for"}]` |
| `hard_blockers` | 一條不符合就直接被刷掉的條件，字串陣列 |
| `fit_threshold` | 投遞門檻，滿分 13，預設 7。`calibrate.py` 會依實際結果建議 |
| `cover_letter_max_chars` | 求職信**目標字數**，預設 300。不是硬上限，實際抓 300–350 |
| `google_email`／`spreadsheet_id` | 面試題要同步到哪份 Google 試算表 |
| `sheets_declined` | 使用者說過不要同步試算表，設 `true` 之後就不再問 |

## Phase 2 -- 修復（其他 skill 說路徑壞掉時）

`~/.nextrole/bin` 是指向 plugin `scripts/` 的 symlink，plugin 更新後會指到舊版本目錄。
重跑 Phase 0 的 `init_store.py` 就會自動更新指向。

## 檔案位置

| 路徑 | 內容 |
|---|---|
| `~/.nextrole/config.json` | 設定（不放素材） |
| `~/.nextrole/kit/` | 事實庫、故事庫、口徑、弱點 — 由 `/nextrole:interview` 填 |
| `~/.nextrole/board.json` | 職缺主檔 |
| `~/.nextrole/resumes/` | 主履歷與各職缺的客製版 |
| `~/.nextrole/output/` | 搜尋結果與看板三頁 |
| `~/.nextrole/bin` | → 本 plugin 的 `scripts/` |

## 已知地雷

- 這個 plugin 的目錄底下**永遠不該出現使用者的素材**。發現有就是 bug，要移到 `~/.nextrole/`。
- 不要為了「設定完整」而追問。空欄位是預期狀態。
