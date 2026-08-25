━━━ 方法一：天賦關鍵字（朋友彙整 {{TALENT_COUNT}} 個）━━━
{{TALENT_LINES}}

━━━ 方法二：技能關鍵字 ━━━
🔥 On Fire
{{ON_FIRE_LINES}}
♨️ Heating Up
{{HEATING_LINES}}
（🔍 = 會拿去三站搜尋的關鍵字）

━━━ 會扣分／排除的 ━━━
{{NEGATIVE_LINES}}

━━━ JD 補充關鍵字 ━━━
{{EXTRA_QUERY_LINES}}

<!--
填寫規則：
- TALENT_LINES：從 profile 的 method1_positive 讀，每行 `  ⭐×weight 詞`（weight 2 = ⭐⭐）。
  沒做天賦問卷就整段刪掉。
- ON_FIRE_LINES / HEATING_LINES：從 method2_positive 讀，每行縮排兩格；
  `q:true` 的前面加 `🔍 `，其餘只留縮排對齊。
- NEGATIVE_LINES：從 negative 讀，每行 `  ✕ 詞 — 職稱命中即剔除` 或 `  ✕ 詞 — 內文命中扣分`。
  零負向詞就寫 `  （無，你沒有設定排除條件）`。
- EXTRA_QUERY_LINES：只有跑過 Phase 4c 才有；沒有就整段刪掉。
- 這是強制動作：每次跑完 build_profile.py 都要主動輸出，不要等使用者問。
-->
