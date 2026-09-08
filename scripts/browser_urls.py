#!/usr/bin/env python3
"""降級模式用：產生 104 / Cake / LinkedIn 的搜尋網址，讓使用者自己貼到瀏覽器。

這台機器不能跑爬蟲時（沒有 uv、或站點擋了）改走這條路。
不要假裝有跑 —— 明講「我給你搜尋網址，你自己開來看」。

uv run browser_urls.py [--json] [--max-queries 8]
"""
from __future__ import annotations

import argparse
import json
from urllib.parse import quote

from profile_io import load_profile

# LinkedIn 的 f_WT：2＝完全遠端、3＝混合
LINKEDIN_REMOTE = "2%2C3"


def url_104(keyword: str) -> str:
    # 104 的地區篩選要用它自己的區域代碼，這裡不做 —— 使用者在頁面上點比較快
    return f"https://www.104.com.tw/jobs/search/?keyword={quote(keyword)}&order=15"


def url_cake(keyword: str) -> str:
    return f"https://www.cake.me/jobs?query={quote(keyword)}"


def url_linkedin(keyword: str, location: str = "Taiwan", remote: bool = True) -> str:
    params = [f"keywords={quote(keyword)}"]
    if location:
        params.append(f"location={quote(location)}")
    if remote:
        params.append(f"f_WT={LINKEDIN_REMOTE}")
    return "https://www.linkedin.com/jobs/search/?" + "&".join(params)


def linkedin_locations(cfg: dict) -> list[str]:
    regions = cfg.get("filters", {}).get("regions", ["tw"])
    out: list[str] = []
    if "tw" in regions:
        out.append("Taiwan")
    if "apac" in regions:
        out += ["Singapore", "Hong Kong", "Tokyo, Japan", "Seoul, South Korea",
                "Sydney, Australia", "Kuala Lumpur, Malaysia", "Bangkok, Thailand"]
    if "global" in regions:
        out.append("")
    if "remote" in regions and not out:
        out.append("")
    return out or ["Taiwan"]


def build_urls(cfg: dict | None = None, max_queries: int = 8) -> dict:
    """從 ~/.nextrole/profile.json 取設定，產生三站的搜尋網址。"""
    if cfg is None:
        cfg = load_profile()
    if not cfg:
        raise SystemExit("找不到 ~/.nextrole/profile.json — 請先做完技能問卷")

    # 搜尋詞 = 候選職稱（較像職缺名）＋ 權重最高的幾個正向關鍵字
    titles = cfg.get("candidate_titles", [])
    top_pos = [
        e.get("term") or e.get("en")
        for e in sorted(cfg.get("method2_positive", []), key=lambda e: -e.get("weight", 1))
        if e.get("q")
    ]
    queries = list(dict.fromkeys([*titles, *top_pos]))[:max_queries]

    regions = cfg.get("filters", {}).get("regions", ["tw"])
    cities = cfg.get("filters", {}).get("allowed_cities", [])
    locs = linkedin_locations(cfg)

    out: dict = {"queries": queries, "104": [], "cake": [], "linkedin": []}
    for q in queries:
        if "tw" in regions:  # 104 只有台灣職缺
            out["104"].append({"q": q, "url": url_104(q)})
        out["cake"].append({"q": q, "url": url_cake(q)})
        for loc in locs:
            out["linkedin"].append({"q": q, "loc": loc or "全球", "url": url_linkedin(q, loc)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="輸出 JSON 而不是人看的清單")
    ap.add_argument("--max-queries", type=int, default=8)
    args = ap.parse_args()

    data = build_urls(max_queries=args.max_queries)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print("這台機器不能跑爬蟲，以下是搜尋網址，請自己貼到瀏覽器開。\n")
    print(f"搜尋詞（{len(data['queries'])} 個）：{'、'.join(data['queries'])}\n")
    for site, label in (("104", "104"), ("cake", "Cake"), ("linkedin", "LinkedIn")):
        rows = data[site]
        if not rows:
            continue
        print(f"━━━ {label}（{len(rows)} 個連結）━━━")
        for r in rows:
            loc = f"［{r['loc']}］" if "loc" in r else ""
            print(f"  {r['q']}{loc}\n    {r['url']}")
        print()
    if cities := (load_profile() or {}).get("filters", {}).get("allowed_cities", []):
        print(f"⚠️ 104 的地區篩選要在頁面上點，記得選：{'、'.join(cities)}\n")
    print("看完之後，把有興趣的職缺貼回對話，我幫你評分並加進看板。")


if __name__ == "__main__":
    main()
