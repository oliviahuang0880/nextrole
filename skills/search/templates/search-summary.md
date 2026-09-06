# 搜尋完成回報

## 這次撈到什麼

- 總筆數：{{TOTAL_COUNT}}（推薦區 {{RECOMMENDED_COUNT}} 筆，門檻 {{THRESHOLD}} 分）
- 新出現：{{NEW_COUNT}}（只有跑 `--diff-against` 才有，否則刪掉這行）
- 來源分佈：{{SOURCE_BREAKDOWN}}
- 搜尋條件：地區 {{REGIONS}}／城市 {{CITIES}}／領域加權 {{FIELD_TERMS_STATE}}

## 健檢

- 代碼：{{HEALTH_CODES}}
- 說明與建議：{{HEALTH_NOTES}}

## 怎麼看

```bash
cd output && python3 -m http.server 8765
```

開 `http://localhost:8765/{{HTML_FILENAME}}`

⚠️ 不要用 `file://` 開，職缺連結會空白（瀏覽器安全機制）。

## 下一步

{{NEXT_STEPS}}

<!--
填寫規則：
- HEALTH_CODES 直接抄 run_search.py 印的 `健檢代碼：` 那行。
- 代碼是 OK 時，HEALTH_NOTES 寫「一切正常」，這一節可壓成一行。
- 代碼不是 OK 時，依 rules/搜尋結果健檢判準.md 的對照表寫出原因與**具體可執行**的建議。
- FIELD_TERMS_STATE：`關閉（通用能力評分）` 或 `開啟：<詞1>、<詞2>…`。
- NEXT_STEPS 只提機制層面的選項（調地區／調門檻／加搜尋詞／貼 JD／每天跑 --diff-against auto），
  不得推測使用者該往哪個領域走。
- 所有填位符號都要替換掉，不得殘留 {{...}}。
-->
