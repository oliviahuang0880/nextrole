# 搜尋完成回報

## 這次撈到什麼

- 總筆數：312（推薦區 0 筆，門檻 60 分）
- 來源分佈：104=180、Cake=64、LinkedIn=68
- 搜尋條件：地區 台灣＋全遠端／城市 台北、新北／領域加權 關閉（通用能力評分）

## 健檢

- 代碼：`NO_RECOMMENDED`
- 說明與建議：有 312 筆結果，但沒有任何一筆到 60 分的推薦門檻，最高分是 54 分。
  這通常代表門檻對目前的關鍵字組合來說偏高。兩個做法：
  1. 把門檻降到 50 分先看看推薦區長什麼樣（改 `~/.nextrole/profile.json` 的 `scoring.threshold`）
  2. 貼一份你最近看到喜歡的 JD 給我，我抽幾個搜尋詞進去拓寬撈到的範圍

  兩種都可以直接用快取重算，不用重爬（約 5 秒）：
  ```bash
  uv run run_search.py --from-cache
  ```

## 怎麼看

```bash
cd output && python3 -m http.server 8765
```

開 `http://localhost:8765/results_20260824_2130.html`

⚠️ 不要用 `file://` 開，職缺連結會空白（瀏覽器安全機制）。

## 下一步

- 想每天自動標出新職缺：`uv run run_search.py --diff-against auto`
- 想放寬地區：目前只收台北、新北，可以加桃園／新竹或整個台灣
- 想調關鍵字：跟我說要加減哪些技能詞，我改完用 `--from-cache` 秒算給你看
