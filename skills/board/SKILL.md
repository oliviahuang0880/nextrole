---
name: board
description: NextRole 職缺看板：打開可篩選排序的職缺資料表、看求職進度、更新投遞狀態、對指定職缺做適合度評分（產業關係／職務重疊／條件符合 13 分制＋硬門檻）決定投不投、以及依實際投遞結果校準投遞門檻。使用者說「看職缺清單」「我投到哪了」「求職進度」「這個職缺值得投嗎」「幫我評這幾個職缺」「開看板」時使用。
---

# 職缺看板

`~/.nextrole/board.json` 是求職全流程的唯一真實來源 — 搜尋、履歷、面試題都掛在同一筆職缺上。

## Output Contract

- 只寫 `~/.nextrole/board.json`（經 `board.py`，會自動備份）。不得手改 JSON 的結構。
- **爬蟲不得覆寫使用者的判斷**：`status`／`notes`／`fit`／`artifacts` 只能由使用者或本 skill 改。
- 適合度評分**只評使用者指定的職缺**，不主動全跑 — 每一筆都要讀完整 JD，全跑既慢又貴。
- 評分要有依據。JD 上找不到的東西就標「JD 未提」，**不要猜**。

# SOP

## Phase 0 -- 開看板

1. READ 確認 `~/.nextrole/board.json` 存在。不存在就先跑 `/nextrole:setup`，再叫使用者跑 `/nextrole:search`。
2. WRITE 開看板：

   ```bash
   cd ~/.nextrole/bin && uv run serve.py
   ```

   ⚠️ **不要用 `file://` 開**，職缺連結會空白、狀態也存不回去。
3. WRITE 回報現況：共幾筆、各狀態幾筆、已評適合度幾筆、有幾筆還沒評。

## Phase 1 -- 適合度評分（決定投不投）

1. THINK 先確認要評哪幾筆。使用者說「評一評」而沒指定時，**問他要評哪些**，或建議「機器分最高的前 N 筆」「還沒評的」。不要自己全跑。
2. READ 讀取 `rules/適合度評分判準.md` 與 `~/.nextrole/config.json`（拿 `fit_threshold` 與 `hard_blockers`）。
3. READ 從 `board.json` 取出這幾筆的完整 `job.description`。JD 太短（<250 字）就標明「JD 資訊不足，評分信心低」。
4. WRITE 逐筆輸出評分表給使用者看：三個指標各幾分＋為什麼、硬門檻有沒有踩到、總分與建議。
5. THINK 使用者有不同意見就照他的改 — 他比工具清楚自己的條件。
6. WRITE 寫回：

   ```bash
   cd ~/.nextrole/bin && uv run -c "
   import board; board.set_fit('<job_id>', {'industry':N,'overlap':N,'condition':N,
                                            'hard_blocker':False,'blocker_note':''})"
   ```

   `total` 與 `verdict` 由 `board.py` 算，不要自己填。
7. WRITE 重畫看板：`uv run render_board.py`。

## Phase 2 -- 更新狀態

使用者通常直接在看板頁面上改（下拉選單即時存回）。他在對話裡講的時候才走這裡：

1. READ 找出對應的 `job_id`（用公司名或職缺名比對）。
2. WRITE `board.patch(job_id, {"status": "...", "notes": "..."})`。
   狀態：`new` 新／`interested` 想投／`applied` 已投／`interviewing` 面試中／`offer`／`rejected` 已拒／`skipped` 略過。
   改成 `applied` 時 `applied_at` 會自動記下，不用手填。

## Phase 3 -- 校準投遞門檻

1. THINK 只有在 `applied` 的筆數 ≥ 10 時才有意義。不夠就直說「樣本還不夠，再投幾家」。
2. WRITE 跑 `uv run calibrate.py`，它會統計各分數段投遞後進到面試的比例。
3. WRITE 把結果講給使用者聽，重點是**哪個分數以下幾乎沒進面試**，那就是他的實際門檻。
   問過他之後才寫進 `config.json` 的 `fit_threshold`。
4. THINK ⭐ 順便看**沒進面試的那幾筆有沒有共同點**。最常見的是踩到某個硬門檻 —
   發現了就建議補進 `config.json` 的 `hard_blockers`，下次評分就會先擋。

## 檔案位置

- 職缺主檔：`~/.nextrole/board.json`（每次寫入自動備份）
- 看板頁面：`~/.nextrole/output/board.html`（由 `render_board.py` 產生）
- 設定：`~/.nextrole/config.json`

## 已知地雷

- `cd ~/.nextrole/bin` 失敗時（通常是 plugin 更新過，symlink 指向舊版本），跑一次 `/nextrole:setup` 就會重新指好。
- 看板頁面是靜態檔，靠 `serve.py` 的 `PATCH /api/job/<id>` 寫回。**沒起 server 就改東西**只會存在瀏覽器的 localStorage，頁面會跳黃色提示 — 照提示把暫存內容貼回來補寫。
- `PATCH` 只收 `status` 與 `notes`。適合度與分數不能從頁面改，只能走 Phase 1。
- 重跑搜尋會更新分數，**但不會動使用者的判斷**。分數變了而狀態沒變是正常的。
