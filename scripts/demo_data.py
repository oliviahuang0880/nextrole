#!/usr/bin/env python3
"""產生一份示範資料，用來看版面或截圖。公司名與職缺全部是虛構的。

⚠️ 預設寫到 ~/.nextrole-demo/，**不會碰到你自己的 ~/.nextrole/**。
   真的要蓋掉自己的資料才加 --home ~ （會再問一次）。

    uv run demo_data.py                 # 產生示範資料
    uv run demo_data.py --jobs 80       # 多一點
    uv run demo_data.py --home ~/x      # 指定家目錄
"""
from __future__ import annotations

import argparse
import os
import random
import sys

DEFAULT_HOME = os.path.expanduser("~/.nextrole-demo")

TITLES = {
    "strong": [
        "產品經理（使用者研究）", "資深產品經理", "Product Manager", "產品經理 · 數據產品",
        "Senior Product Manager, Growth", "產品企劃 / PM", "數位產品經理",
        "Product Manager（B2B SaaS）", "產品經理 · 訂閱制", "Associate Product Manager",
        "Product Manager, Platform", "資深產品企劃",
    ],
    "mid": [
        "產品設計師 / Product Designer", "UX 設計師", "專案經理 PM", "商業分析師",
        "Product Owner", "服務設計師", "數據分析師（產品）", "使用者研究員",
        "Growth Marketing Manager",
    ],
    "weak": [
        "行銷企劃專員", "社群小編", "業務代表", "客戶成功專員", "電話銷售專員",
        "產品行銷實習生", "平面設計師", "門市儲備幹部",
    ],
}
COMPANIES = [
    "晨星科技", "和光數位", "青禾生醫", "Lumen Labs", "織雲資訊", "百川金融科技",
    "鹿野學習", "北極星軟體", "微光互動", "岩石數據", "海潮電商", "拾光旅遊",
    "麥禾農業科技", "藍鵲物流", "常青健康", "初芽教育", "River Delta", "橙嶼設計",
    "石墨科技", "潮汐健身", "木衛二資安", "Kestrel AI", "遠望醫療", "同心保險科技",
    "白鷺物聯", "曉風文創", "北緯資通", "沐光生活",
]
LOCS = ["台北市信義區", "台北市中山區", "台北市內湖區", "新北市板橋區",
        "新北市新店區", "台北市大安區", "台北市松山區", "新北市中和區"]
SALARY = ["月薪 60,000~90,000", "月薪 55,000 以上", "待遇面議",
          "年薪 90 萬~130 萬", "", "月薪 45,000~65,000", "月薪 70,000~100,000"]

JD = {
    "strong": [
        "負責產品從 0 到 1 的規劃與落地，透過使用者訪談與數據分析釐清痛點。",
        "撰寫 PRD 與規格文件，與工程、設計跨部門協作推動開發。",
        "定義核心指標，用數據驗證產品假設並持續迭代。",
        "執行使用者研究與可用性測試，把研究洞察轉成產品決策。",
        "負責產品路線圖規劃與優先序排定，對商業結果負責。",
        "製作原型與流程圖，與工程團隊確認技術可行性。",
    ],
    "mid": [
        "維護既有產品線，蒐集需求並排定開發順序。",
        "與設計師合作優化介面，提升使用體驗。",
        "整理報表與營運數據，提供團隊決策參考。",
        "協助專案時程管理與跨團隊溝通。",
    ],
    "weak": [
        "負責社群經營與活動企劃，提升品牌聲量。",
        "開發新客戶並維護既有客戶關係，達成每月業績獎金目標。",
        "製作行銷素材與活動視覺。",
    ],
}
TAIL = "需具備良好的溝通能力與獨立作業能力。歡迎有興趣的夥伴加入我們，一起把產品做好。"

PROFILE = {
    "candidate_titles": ["產品經理", "Product Manager"],
    "method2_positive": [
        {"term": "使用者研究", "en": "user research", "weight": 3, "q": True},
        {"term": "數據", "en": "data", "weight": 3, "q": True},
        {"term": "跨部門", "en": "cross-functional", "weight": 2, "q": True},
        {"term": "規格", "en": "spec", "weight": 3, "q": True},
        {"term": "訪談", "en": "interview", "weight": 2, "q": True},
        {"term": "原型", "en": "prototype", "weight": 2, "q": True},
        {"term": "路線圖", "en": "roadmap", "weight": 2, "q": True},
    ],
    "method1_positive": [],
    "negative": [
        {"term": "實習", "en": "intern", "exclude_if_title": True},
        {"term": "電話銷售", "en": "telesales", "exclude": True},
        {"term": "業績獎金", "en": "commission", "penalty": 15},
    ],
    # 沒做天賦問卷 → 100% 技能，跟 merge_talents 沒跑過時一致
    "scoring": {"blend_method2": 1.0, "blend_method1": 0.0, "method2_full": 14,
                "method1_full": 12, "threshold": 60, "title_boost": 2.0,
                "use_field_terms": False},
    "filters": {"allowed_cities": ["台北", "新北"], "allow_remote": True, "regions": ["tw"]},
}

# 備註要跟狀態對得上，否則示範資料自己在打架
NOTES_BY_STATUS = {
    "applied": ["8/28 投遞，用 PM 版履歷", "投遞訊息有附作品集連結", "", "9/1 投遞"],
    "first":   ["一面約在下週三，HR 面", "一面 9/9 14:00，用人主管", ""],
    "second":  ["二面過了，等三面時間", "二面問了很多數據的題目"],
    "third":   ["三面要見創辦人，準備產品觀察題", "等最後結果，HR 說月底前"],
    "offer":   ["9/2 拿到 offer，考慮中"],
    "thanks":  ["履歷階段收感謝信", "面試後收到婉拒信", ""],
    "ghosted": ["投了兩週沒回音", "面試完就沒消息了", ""],
}
NOTES_SAVED = ["產品有興趣，等寫完履歷再投", "薪資帶要問清楚", "", "通勤有點遠但職務很合", ""]


def build(n_jobs: int, seed: int):
    random.seed(seed)
    jobs, i = [], 0
    mix = [("strong", int(n_jobs * 0.52)), ("mid", int(n_jobs * 0.32)),
           ("weak", n_jobs - int(n_jobs * 0.52) - int(n_jobs * 0.32))]
    for kind, count in mix:
        for _ in range(count):
            i += 1
            remote = random.random() < 0.16
            pool = JD[kind]
            body = " ".join(random.sample(pool, min(len(pool), random.randint(3, 4))))
            jobs.append({
                "source": random.choice(["104", "104", "104", "Cake", "Cake", "LinkedIn"]),
                "title": random.choice(TITLES[kind]),
                "company": random.choice(COMPANIES),
                "url": f"https://example.test/job/{i:04d}",
                "location": "Remote" if remote else random.choice(LOCS),
                "remote": remote,
                "salary": random.choice(SALARY),
                "description": body + " " + TAIL * 2,
            })
    random.shuffle(jobs)
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", default=DEFAULT_HOME, help=f"寫到哪（預設 {DEFAULT_HOME}）")
    ap.add_argument("--jobs", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--yes", action="store_true", help="覆寫既有資料不再詢問")
    args = ap.parse_args()

    home = os.path.abspath(os.path.expanduser(args.home))
    real = os.path.expanduser("~")
    if home == real and not args.yes:
        print("⚠️ 這會把示範資料寫進你自己的 ~/.nextrole/，蓋掉真實的求職紀錄。")
        print("   確定的話加 --yes。要看版面的話直接用預設就好：uv run demo_data.py")
        sys.exit(1)

    os.makedirs(home, exist_ok=True)
    os.environ["HOME"] = home
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import board as bd
    import init_store
    import render_board
    import score
    import store

    init_store.main()
    store.write_json(os.path.join(store.ROOT, "profile.json"), PROFILE, backup=False)

    raw = build(args.jobs, args.seed)
    scored = [{"job": j, "eval": ev, "is_new": False}
              for j in raw if not (ev := score.score_job(j, PROFILE))["excluded"]]
    # 重來一份乾淨的 board，不要跟上一次的示範資料疊在一起
    store.write_json(store.BOARD, {"version": 2, "updated_at": store.now(), "jobs": {}},
                     backup=False)
    bd.merge(scored)

    b = bd.load()
    ids = sorted(b["jobs"], key=lambda k: -b["jobs"][k]["eval"]["score"])
    rnd = random.Random(args.seed)

    # ── ③ 投遞追蹤：從高分往下挑 14 筆，鋪滿漏斗各階段
    track_plan = [
        ("offer",   (2, 4, 4), False, ""),
        ("third",   (3, 4, 4), False, ""),
        ("second",  (2, 4, 3), False, ""),
        ("second",  (1, 4, 4), False, ""),
        ("first",   (2, 4, 4), False, ""),
        ("first",   (2, 3, 4), False, ""),
        ("first",   (1, 4, 3), False, ""),
        ("applied", (2, 3, 3), False, ""),
        ("applied", (2, 4, 3), False, ""),
        ("applied", (1, 3, 4), False, ""),
        ("thanks",  (3, 4, 2), True,  "必備 5 年以上 PM 年資"),
        ("thanks",  (2, 3, 2), True,  "必備 B2B SaaS 實戰"),
        ("ghosted", (1, 3, 3), False, ""),
        ("ghosted", (1, 2, 3), False, ""),
    ]
    import datetime as _dt
    today = _dt.date.today()
    cursor = 0
    for offset, (status, fit, blocked, note) in enumerate(track_plan):
        jid = ids[cursor]; cursor += 1
        bd.set_fit(jid, {"industry": fit[0], "overlap": fit[1], "condition": fit[2],
                         "hard_blocker": blocked, "blocker_note": note})
        bd.patch(jid, {"status": status})
        bd.patch(jid, {"applied_at": str(today - _dt.timedelta(days=3 + offset * 2))})
        n = rnd.choice(NOTES_BY_STATUS[status])
        if n:
            bd.patch(jid, {"notes": n})

    # 有些已經做過履歷與面試題
    for k, arts in ((0, ("resume", "cover_letter", "qa", "sheet_tab")),
                    (1, ("resume", "cover_letter", "qa", "sheet_tab")),
                    (2, ("resume", "cover_letter", "qa")),
                    (3, ("resume", "cover_letter")),
                    (4, ("resume", "cover_letter")),
                    (6, ("resume",))):
        for key in arts:
            v = "示範頁籤" if key == "sheet_tab" else f"{key}/{ids[k]}.md"
            bd.set_artifact(ids[k], key, v)

    # ── ② 分析頁：10 筆已儲存。七筆評過（涵蓋 投／邊緣／不投／硬門檻），三筆還沒評
    saved_plan = [
        (3, 4, 4, False, ""),                       # 11 投
        (2, 4, 4, False, ""),                       # 10 投
        (2, 4, 3, False, ""),                       #  9 投
        (1, 3, 3, False, ""),                       #  7 邊緣
        (2, 2, 3, False, ""),                       #  7 邊緣
        (1, 2, 2, False, ""),                       #  5 不投
        (3, 4, 4, True, "全英文工作環境，需與海外團隊協作"),
        None, None, None,                           # 還沒評
    ]
    for plan in saved_plan:
        jid = ids[cursor]; cursor += 1
        bd.patch(jid, {"saved": True})
        if plan:
            bd.set_fit(jid, {"industry": plan[0], "overlap": plan[1], "condition": plan[2],
                             "hard_blocker": plan[3], "blocker_note": plan[4]})
        n = rnd.choice(NOTES_SAVED)
        if n:
            bd.patch(jid, {"notes": n})

    # ── ① 收件匣：再標幾筆「看過但沒存」，示範它會被收起來
    for _ in range(6):
        bd.patch(ids[cursor], {"seen": True}); cursor += 1

    render_board.render_all()
    b = bd.load()
    c = bd.counts(b)
    seen_only = c["_seen"] - c["saved"] - c["tracker"]
    rated = sum(1 for _, r in bd.in_stage(b, "saved")
                if (r.get("fit") or {}).get("total") is not None)
    print()
    print(f"示範資料寫到 {store.ROOT}")
    print(f"  ① 收件匣 {c['inbox']:>3} 筆（其中 {seen_only} 筆標為看過，預設收起來）")
    print(f"  ② 分析　 {c['saved']:>3} 筆（已評 {rated}、未評 {c['saved'] - rated}）")
    print(f"  ③ 追蹤　 {c['tracker']:>3} 筆（Offer {c['offer']}、進行中 "
          f"{c['applied'] + c['first'] + c['second'] + c['third']}、"
          f"感謝信 {c['thanks']}、無聲卡 {c['ghosted']}）")
    print()
    print("看版面：")
    print(f"  HOME={home} uv run serve.py")
    print("  → http://127.0.0.1:8765/inbox.html")


if __name__ == "__main__":
    main()
