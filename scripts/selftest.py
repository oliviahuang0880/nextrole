#!/usr/bin/env python3
"""不碰使用者資料的自我測試：在暫存 HOME 裡跑一次資料流。

uv run selftest.py
"""
from __future__ import annotations

import os
import re
import subprocess
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


# 這個 plugin 是公開的，裡面不能有任何一個使用者的求職素材。
# 只列「一定是某個人的東西」的樣態，不列通用詞。
PERSONAL_PATTERNS = [
    r"\b1[A-Za-z0-9_-]{25,}\b",          # Google 試算表／文件 ID
    r"[\w.+-]+@(?!example\.)[\w-]+\.[\w.]+",  # Email（example.* 是文件用的假網域）
    r"\+?886[\d-]{8,}|09\d{2}-?\d{3}-?\d{3}",  # 台灣手機
    r"(?:月薪|年薪|期望待遇)[^\n]{0,12}\d{2,}",   # 具體薪資帶
]
# 這些是 repo 自己的身分，不是求職素材
ALLOWED = [r"github\.com/[\w-]+/nextrole", r"0900-000-000"]


def audit_repo(root: str) -> list[str]:
    hits = []
    files = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True,
                           text=True, check=True).stdout.split()
    for rel in files:
        if rel == "scripts/selftest.py":   # 樣態本身就寫在這支裡
            continue
        path = os.path.join(root, rel)
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        for pat in PERSONAL_PATTERNS:
            for m in re.finditer(pat, text):
                frag = m.group(0)
                if any(re.search(a, frag) for a in ALLOWED):
                    continue
                line = text[:m.start()].count("\n") + 1
                if any(re.search(a, text.splitlines()[line - 1]) for a in ALLOWED):
                    continue
                hits.append(f"{rel}:{line}  {frag}")
    return hits


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

    print("\n[4] 三頁的單向流動：收件匣 → 分析 → 投遞追蹤")
    jid = store.job_id(JOBS[0]["url"])
    other = store.job_id(JOBS[1]["url"])
    check(bd.stage_of(bd.load()["jobs"][jid]) == "inbox", "新職缺一開始在收件匣")

    bd.patch(other, {"seen": True})
    check(bd.stage_of(bd.load()["jobs"][other]) == "inbox", "只按『看過』還是留在收件匣（只是預設不顯示）")

    bd.patch(jid, {"saved": True})
    rec = bd.load()["jobs"][jid]
    check(bd.stage_of(rec) == "saved", "按『儲存』後進到分析頁")
    check(rec["seen"] is True, "儲存會順便標成看過，收件匣不用再出現")

    bd.set_fit(jid, {"industry": 2, "overlap": 4, "condition": 4, "hard_blocker": False})
    rec = bd.load()["jobs"][jid]
    check(rec["fit"]["total"] == 10 and rec["fit"]["verdict"] == "投",
          f"適合度 10／13 判定為投（{rec['fit']['verdict']}）")

    bd.patch(jid, {"status": "applied", "notes": "8/30 投遞"})
    rec = bd.load()["jobs"][jid]
    check(bd.stage_of(rec) == "tracker", "按『開始投遞』後進到投遞追蹤")
    check(rec["applied_at"] is not None, "投遞時自動記下時間")
    c = bd.counts()
    check(c["inbox"] == 1 and c["saved"] == 0 and c["tracker"] == 1,
          f"三頁計數正確（收件匣 {c['inbox']}／分析 {c['saved']}／追蹤 {c['tracker']}）")

    print("\n[5] ⭐ 重跑搜尋不得洗掉使用者的判斷")
    before = bd.load()["jobs"][jid]
    check(before["saved"] and before["status"] == "applied", "（前置）這筆已投遞")
    for j in JOBS:  # 模擬第二次爬到同樣的職缺，分數變了
        j["description"] += " 另外需要研究能力。"
    scored2 = _score_all(JOBS)
    st2 = bd.merge(scored2)
    rec = bd.load()["jobs"][jid]
    check(st2["added"] == 0 and st2["updated"] == 2, f"沒有重複新增（{st2}）")
    check(rec["status"] == "applied", "status 保住了")
    check(rec["seen"] is True and rec["saved"] is True, "seen／saved 保住了")
    check(rec["notes"] == "8/30 投遞", "notes 保住了")
    check(rec["fit"]["total"] == 10, "fit 保住了")
    check(rec["applied_at"] is not None, "applied_at 保住了")

    print("\n[6] 白名單：頁面不能改分數或適合度")
    for bad in ({"eval": {"score": 100}}, {"fit": {"total": 13}}, {"status": "不存在"},
                {"applied_at": "2020-01-01"}):
        try:
            bd.patch(jid, bad)
            check(False, f"應該要被擋下來：{bad}")
        except (ValueError, KeyError):
            check(True, f"擋下 {list(bad)[0]}")

    print("\n[7] 產出三頁")
    paths = render_board.render_all(bd.load(), cfg)
    check(len(paths) == 3, f"產出三個檔案（{[os.path.basename(p) for p in paths]}）")
    docs = {os.path.basename(p): open(p, encoding="utf-8").read() for p in paths}
    for name, doc in docs.items():
        check("{{" not in doc, f"{name} 沒有殘留 {{{{ 填位符號")
    check("8/30 投遞" in docs["tracker.html"], "備註畫在投遞追蹤頁")
    check("10" in docs["tracker.html"], "適合度畫在投遞追蹤頁")
    check("act-save" in docs["inbox.html"], "收件匣有儲存按鈕")
    check("act-apply" in docs["analysis.html"] or "還沒有要分析" in docs["analysis.html"],
          "分析頁有開始投遞按鈕或空狀態")
    check("&lt;" in docs["inbox.html"] or "example.test" in docs["inbox.html"],
          "內容有經過跳脫處理")

    print("\n[7b] 每一頁只放屬於自己的職缺")
    check(jid in docs["tracker.html"], "已投遞的在追蹤頁")
    check(jid not in docs["analysis.html"], "已投遞的不會留在分析頁")

    print("\n[7c] v1 舊資料要能升級")
    old = {"version": 1, "updated_at": store.now(), "jobs": {
        "a": {"job": {"url": "u"}, "eval": {}, "fit": {}, "status": "interested",
              "notes": "", "artifacts": {}},
        "b": {"job": {"url": "v"}, "eval": {}, "fit": {}, "status": "offer",
              "notes": "", "artifacts": {}}}}
    store.write_json(store.BOARD, old)
    m = bd.load()
    check(m["version"] == 2, "版本升到 2")
    check(m["jobs"]["a"]["saved"] is True and m["jobs"]["a"]["status"] is None,
          "舊的『想投』變成 saved、還沒投遞")
    check(m["jobs"]["b"]["status"] == "offer" and bd.stage_of(m["jobs"]["b"]) == "tracker",
          "舊的『Offer』留在投遞追蹤")

    print("\n[8] 零個人資料：暫存 HOME 以外什麼都沒寫")
    check(store.ROOT.startswith(_TMP), f"所有寫入都在暫存區（{store.ROOT}）")

    print("\n[9] 零個人資料：repo 本身")
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hits = audit_repo(repo)
    check(not hits, "repo 裡查無試算表 ID／Email／電話／薪資帶")
    for h in hits:
        print(f"     {h}")

    print()
    if FAILED:
        print(f"❌ {len(FAILED)} 項未通過：")
        for m in FAILED:
            print(f"   - {m}")
        sys.exit(1)
    print("✅ 全部通過。")


if __name__ == "__main__":
    main()
