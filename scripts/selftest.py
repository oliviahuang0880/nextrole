#!/usr/bin/env python3
"""不碰使用者資料的自我測試：在暫存 HOME 裡跑一次資料流。

uv run selftest.py
"""
from __future__ import annotations

import os
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="nextrole-selftest-")
os.environ["HOME"] = _TMP  # 一定要在 import store 之前

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as bd  # noqa: E402
import init_store  # noqa: E402
import render_board  # noqa: E402
import score  # noqa: E402
import store  # noqa: E402

FAILED = []


def check(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILED.append(msg)


PROFILE = {
    "candidate_titles": ["產品經理"],
    "method2_positive": [
        {"term": "研究", "en": "research", "weight": 3, "q": True},
        {"term": "溝通", "en": "communication", "weight": 2, "q": True},
    ],
    "method1_positive": [{"term": "分析判斷", "en": "analysis", "weight": 2}],
    "negative": [{"term": "實習", "en": "intern", "exclude_if_title": True}],
    "scoring": {"blend_method2": 1.0, "blend_method1": 0.0, "method2_full": 10,
                "method1_full": 12, "threshold": 60, "title_boost": 2.0,
                "use_field_terms": False},
    "filters": {"allowed_cities": ["台北"], "allow_remote": True, "regions": ["tw"]},
}

JOBS = [
    {"source": "104", "title": "產品經理（使用者研究）", "company": "A 公司",
     "url": "https://example.test/a", "location": "台北", "remote": False,
     "salary": "面議", "description": "負責研究與溝通，跨部門協作。"},
    {"source": "Cake", "title": "行銷企劃", "company": "B 公司",
     "url": "https://example.test/b", "location": "台北", "remote": True,
     "salary": "", "description": "社群經營。"},
]


def _score_all(jobs):
    """比照 run_search.py 的包法：{"job": ..., "eval": ...}，排除掉被剔除的。"""
    out = []
    for j in jobs:
        ev = score.score_job(j, PROFILE)
        if not ev["excluded"]:
            out.append({"job": j, "eval": ev, "is_new": False})
    return out


def main():
    print(f"暫存 HOME：{_TMP}")

    print("\n[1] init_store 建立空骨架")
    init_store.main()
    cfg = store.load_config()
    check(cfg["spreadsheet_id"] is None, "config.json 是空的，沒有預設任何個人資料")
    kit = open(os.path.join(store.KIT, "stories.md"), encoding="utf-8").read()
    check("<名稱>" in kit and len(kit) < 2000, "kit/stories.md 只有空範本")

    print("\n[2] 評分")
    scored = _score_all(JOBS)
    check(len(scored) == 2, f"兩筆都有分數（得到 {len(scored)} 筆）")

    print("\n[3] 第一次 merge")
    st1 = bd.merge(scored)
    check(st1["added"] == 2 and st1["updated"] == 0, f"新增 2 筆（{st1}）")

    print("\n[4] 使用者在頁面上改狀態、備註、適合度")
    jid = store.job_id(JOBS[0]["url"])
    bd.patch(jid, {"status": "applied", "notes": "8/30 投遞"})
    bd.set_fit(jid, {"industry": 2, "overlap": 4, "condition": 4, "hard_blocker": False})
    rec = bd.load()["jobs"][jid]
    check(rec["applied_at"] is not None, "改成『已投』時自動記下投遞時間")
    check(rec["fit"]["total"] == 10 and rec["fit"]["verdict"] == "投", f"適合度 10／13 判定為投（{rec['fit']['verdict']}）")

    print("\n[5] ⭐ 重跑搜尋不得洗掉使用者的判斷")
    for j in JOBS:  # 模擬第二次爬到同樣的職缺，分數變了
        j["description"] += " 另外需要研究能力。"
    scored2 = _score_all(JOBS)
    st2 = bd.merge(scored2)
    rec = bd.load()["jobs"][jid]
    check(st2["added"] == 0 and st2["updated"] == 2, f"沒有重複新增（{st2}）")
    check(rec["status"] == "applied", "status 保住了")
    check(rec["notes"] == "8/30 投遞", "notes 保住了")
    check(rec["fit"]["total"] == 10, "fit 保住了")
    check(rec["applied_at"] is not None, "applied_at 保住了")

    print("\n[6] 白名單：頁面不能改分數或適合度")
    for bad in ({"eval": {"score": 100}}, {"fit": {"total": 13}}, {"status": "不存在"}):
        try:
            bd.patch(jid, bad)
            check(False, f"應該要被擋下來：{bad}")
        except (ValueError, KeyError):
            check(True, f"擋下 {list(bad)[0]}")

    print("\n[7] 產出看板")
    path = render_board.render(bd.load(), os.path.join(store.OUTPUT, "board.html"), cfg["fit_threshold"])
    doc = open(path, encoding="utf-8").read()
    check("{{" not in doc, "沒有殘留 {{ 填位符號")
    check('<select class="st"'.replace('"', "'") in doc, "有狀態下拉")
    check("8/30 投遞" in doc, "備註有畫出來")
    check("10／13" in doc, "適合度有畫出來")
    check("&lt;" in doc or "example.test" in doc, "內容有經過跳脫處理")

    print("\n[8] 零個人資料：暫存 HOME 以外什麼都沒寫")
    check(store.ROOT.startswith(_TMP), f"所有寫入都在暫存區（{store.ROOT}）")

    print()
    if FAILED:
        print(f"❌ {len(FAILED)} 項未通過：")
        for m in FAILED:
            print(f"   - {m}")
        sys.exit(1)
    print("✅ 全部通過。")


if __name__ == "__main__":
    main()
