---
name: resume
description: 針對單一職缺客製履歷與求職信（104 投遞訊息）。從職缺看板挑一筆或直接貼 JD，判斷該用哪個版本的履歷，只調措辭與順序、不動事實，產出 Markdown 原稿與可列印的 A4 網頁，需要時匯出成 Google Docs。使用者說「幫我改履歷」「客製履歷」「這份 JD 我履歷要怎麼調」「寫求職信」「寫投遞訊息」「幫我準備投遞材料」時使用。
---

# 客製履歷與求職信

一份主履歷 → 針對這份 JD 調出一版。**事實不動，只調措辭、補既有實績、調順序。**

## Output Contract

- 產出寫 `~/.nextrole/resumes/<job_id>/`：`resume.md`、`resume.html`、`cover-letter.md`。
- 素材只能取自 `~/.nextrole/kit/facts.md`、`~/.nextrole/resumes/master-*.md` 與使用者當場給的。
  **不足就問，不要補洞。**
- ⛔ **不得新增使用者沒做過的經歷、沒有的數字、沒拿過的職稱。** 客製化是重新排序與換措辭，不是編故事。
- 給使用者審核過才算完成；沒說可以就不要匯出 Google Docs。
- 完成後把路徑寫回 `board.json` 的 `artifacts`。

# SOP

## Phase 0 -- 收齊材料

1. READ 確認 `~/.nextrole/kit/facts.md` 與 `~/.nextrole/resumes/` 底下有主履歷。
   - 沒有主履歷 → 請使用者貼上或指路徑，存成 `~/.nextrole/resumes/master-<id>.md`。
   - `facts.md` 是空的但**主履歷有內容** → 直接開工，主履歷本身就是素材。
     `facts.md` 是補充（數字口徑、履歷放不下的細節），不是前提，不要為了它擋住流程。
   - 主履歷和 `facts.md` **兩邊都空** → 請他貼經歷，或先跑 `/nextrole:interview` 建素材。
2. READ 拿 JD。從看板來就讀 `board.json` 的 `job.description`；使用者直接貼就用貼的，
   並問要不要把這筆加進看板。
3. READ 讀 `~/.nextrole/kit/voice.md`（口徑與地雷）。**每次產出前都要讀** — 這份擋的是
   職稱講錯、數字口徑混用這類會在面試現場穿幫的錯。

## Phase 1 -- 判版本

1. READ 讀取 `rules/履歷版本判斷.md` 與 `config.json` 的 `resume_versions`。
   ⭐ **`resume_versions` 是空的時候，就是現在問**（不要叫他去跑 setup）：

   > 「你手上有幾種履歷？各自是投什麼方向的？」

   他手上剛好有履歷、也剛好在看一份 JD，這時候答得最準。
   收到答案寫進 `config.json`，格式 `[{"id","label","for"}]`，之後就不用再問。
   他說「只有一種」就寫一筆；說「先不分」就留空，這次直接用他給的那份。
2. THINK 依 JD 的訊號判斷用哪一版。只有一版就跳過這步。
3. WRITE 把判斷結果與理由告訴使用者。**兩邊訊號都強時要講出來讓他選**，不要自己決定。
   都不適合就老實說，並指出缺口 — 這比硬寫一份沒用的履歷有價值。

## Phase 2 -- 讀懂這份 JD

1. READ 讀取 `rules/客製化判準.md`。
2. THINK 找出 **JD 的重心**：職責清單裡哪幾條是主軸，哪幾條是陪襯。
3. THINK ⭐ 找出 **JD 的異常之處** — 一般同類職缺不會寫、但這份寫了的東西。
   那通常就是這家公司真正缺的人，也是履歷該把哪一段拉到前面的依據。
4. WRITE 把這兩點講給使用者聽，再開始動筆。他不同意就別寫下去。

## Phase 3 -- 產出

1. WRITE **履歷** `~/.nextrole/resumes/<job_id>/resume.md`
   - 開頭加一段 `> 客製方向：<這份 JD 的重心>｜底本：<哪一版>`，之後回頭看才知道當初為什麼這樣改。
   - 照 `rules/客製化判準.md` 動刀：調順序、換措辭、把命中 JD 的既有實績補上來、把不相關的縮短。
2. WRITE **求職信** `~/.nextrole/resumes/<job_id>/cover-letter.md`
   - 讀 `rules/求職信結構.md`（三件事、四段結構、字數怎麼處理）。
   - 讀 `rules/去AI味檢查.md`，**一開始就照著寫，不是事後洗**。交稿前搜一次 `—` 與 `——`。
   - 第 ④ 段要引具體的一句。**來源優先用 JD 本身**，其次公司介紹；
     已經跑過 `/nextrole:interview` 的「準備一家公司」就直接用那邊的研究成果。
     ⛔ 不要為了寫求職信另外做一輪公司研究，那是面試準備的工作。
   - ⛔ **引不到就留白並註明缺什麼，不要自己編。** 「我很欣賞貴公司在 X 領域的投入」
     這種句子換成任何一家同業都成立，讀起來很順、使用者不會發現，面試被追問就穿幫。
   - 字數：**先寫完整版**，再回報字數與「要壓短該砍哪一段、代價是什麼」，讓使用者決定。
     不要自己先砍掉最有力的一手。
3. WRITE 產可列印版：

   ```bash
   cd ~/.nextrole/bin && uv run render_resume.py ~/.nextrole/resumes/<job_id>/resume.md
   ```

   告訴使用者：瀏覽器開啟後 Cmd+P 就能存成 PDF。
4. WRITE 給使用者審核。修到他滿意為止。

## Phase 4 -- 收尾

1. WRITE 問過使用者之後，才用 `mcp__google_workspace__import_to_google_doc`
   匯出到 Google Docs（帳號讀 `config.json` 的 `google_email`）。沒設定就跳過。
2. WRITE 寫回看板：

   ```bash
   cd ~/.nextrole/bin && uv run -c "
   import board
   board.set_artifact('<job_id>','resume','resumes/<job_id>/resume.md')
   board.set_artifact('<job_id>','cover_letter','resumes/<job_id>/cover-letter.md')"
   ```

3. WRITE 順手問要不要把看板狀態改成「想投」或「已投」。

## 檔案位置

- 主履歷：`~/.nextrole/resumes/master-<id>.md`
- 客製版：`~/.nextrole/resumes/<job_id>/{resume.md,resume.html,cover-letter.md}`
- 素材：`~/.nextrole/kit/facts.md`、`~/.nextrole/kit/voice.md`

## 已知地雷

- `cd ~/.nextrole/bin` 失敗時（通常是 plugin 更新過，symlink 指向舊版本），跑一次 `/nextrole:setup` 就會重新指好。
- ⚠️ **最容易出錯的是「補洞」。** 素材裡沒有的成果，不要為了對上 JD 而寫。
  使用者自己看得出來，而且面試被追問就穿幫。
- ⚠️ **數字口徑**。同一件事常有好幾個數字（月活躍 vs 累計次數、上線首月 vs 全年），
  混用在面試現場會被追問到答不出來。有疑慮就回 `kit/voice.md` 對，對不到就問。
- 履歷 HTML 用 `render_resume.py` 產生，列印邊界已設好。不要自己另外寫一份排版。
