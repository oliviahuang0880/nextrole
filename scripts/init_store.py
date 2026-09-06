#!/usr/bin/env python3
"""建立 ~/.nextrole/ 骨架：目錄、bin symlink、空的 config.json 與 kit/ 範本。

已存在的檔案一律不覆寫 — 這支可以重複跑。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store  # noqa: E402

KIT_TEMPLATES = {
    "facts.md": """# 事實庫

工具只會用這裡寫的東西，不會自己補。寫不出來的就先空著，之後補。

## 經歷
<!-- 公司／職稱／期間／負責什麼。職稱寫實際的那個，不要美化 -->

## 專案
<!-- 每個專案：在解什麼問題、你負責哪一段、上線後的數字 -->

## 數字
<!-- 一個數字一行，寫清楚它是什麼口徑。
     例：「X 是月活躍用戶，不是累計次數」——口徑混用在面試現場會被追問到穿幫 -->
""",
    "stories.md": """# 故事庫

敘事公式：大家原本以為是 A → 我發現其實是 B → 所以我做了 C → 結果＋數字 → 所以對你們。

沒有張力（衝突、意外、有人反對、資源不夠）的不是故事，是履歷條目。
「所以對你們」是**公司專屬**的，每家要現寫，不要存進這裡。

---

## 故事 1：<名稱>
- 🎯 想展現的特質：
- 🏷️ Tag：
- S（情境）：
- T（任務）：
- A（行動）：
- R（結果＋數字）：
- ⚠️ 注意：<不能跟哪個故事同場並用、哪些細節不能講>
""",
    "voice.md": """# 口徑與地雷

產出任何履歷、求職信、面試稿之前都會先讀這份。

## 職稱口徑
<!-- 哪個職稱是真的、哪個容易被講錯 -->

## 數字口徑
<!-- 容易混用的數字，寫清楚各自是什麼 -->

## 不能講的
<!-- 前公司的敏感資訊、面同業時要避開的、不能 claim 的技能 -->

## 薪資
<!-- 期望帶、底線（底線絕不主動說出口）、要不要反問對方的薪資帶 -->
""",
    "weaknesses.md": """# 我的臨場弱點（模擬面試累積）

一開始是空的。每次模擬面試後由 `/nextrole:mock` 往下加。
每次模擬前會先讀這份，照著盯。

<!-- 格式：
- **<弱點名稱>**：<症狀> → <修法>
-->
""",
}


def main():
    store.ensure_dirs()
    created, skipped = [], []

    # config.json
    if not os.path.exists(store.CONFIG):
        store.write_json(store.CONFIG, dict(store.DEFAULT_CONFIG), backup=False)
        created.append(store.rel(store.CONFIG))
    else:
        skipped.append(store.rel(store.CONFIG))

    # board.json
    if not os.path.exists(store.BOARD):
        store.write_json(store.BOARD, {"version": 1, "updated_at": store.now(), "jobs": {}}, backup=False)
        created.append(store.rel(store.BOARD))
    else:
        skipped.append(store.rel(store.BOARD))

    # kit 範本
    for name, body in KIT_TEMPLATES.items():
        p = os.path.join(store.KIT, name)
        if os.path.exists(p):
            skipped.append(store.rel(p))
            continue
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        created.append(store.rel(p))

    # bin symlink -> 本 plugin 的 scripts/
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    link_note = ""
    if os.path.islink(store.BIN):
        if os.path.realpath(store.BIN) != os.path.realpath(scripts_dir):
            os.unlink(store.BIN)
            os.symlink(scripts_dir, store.BIN)
            link_note = f"bin -> {scripts_dir}（已更新指向）"
        else:
            link_note = "bin -> 已是最新"
    elif os.path.exists(store.BIN):
        link_note = f"⚠️ {store.BIN} 存在但不是 symlink，沒有動它"
    else:
        os.symlink(scripts_dir, store.BIN)
        link_note = f"bin -> {scripts_dir}"

    print(f"資料夾：{store.ROOT}")
    print(f"  新建：{'、'.join(created) if created else '無'}")
    print(f"  已存在跳過：{'、'.join(skipped) if skipped else '無'}")
    print(f"  {link_note}")
    print("完成。個人素材只會存在這個資料夾，不會進 repo。")


if __name__ == "__main__":
    main()
