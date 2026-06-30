# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "beautifulsoup4", "lxml"]
# ///
"""NextRole 搜尋主程式：讀 ~/.nextrole/profile.json → 廣撒搜尋 104/Cake/LinkedIn
→ 抓完整 JD → 評分 → 寫 ./output/ HTML + CSV。

用法：
    uv run run_search.py                       # 全部用 profile 預設、爬 104/Cake/LinkedIn
    uv run run_search.py --queries UX 產品     # 額外加領域查詢詞
    uv run run_search.py --from-cache          # 用 ./output/_jobs_cache.json 重算（不重爬）
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import time
from pathlib import Path

from score import score_job
from search_104 import search_104, fetch_104_full
from search_cake import search_cake, fetch_cake_full
from search_linkedin import search_linkedin, fetch_linkedin_full
from profile_io import load_profile

OUTPUT = os.path.abspath("./output")
JOBS_CACHE = os.path.join(OUTPUT, "_jobs_cache.json")


def collect_queries(cfg: dict, extra: list[str]) -> list[str]:
    queries = list(cfg.get("candidate_titles", []))
    for e in cfg.get("method2_positive", []):
        if not e.get("q"):
            continue
        for key in ("term", "en"):
            v = (e.get(key) or "").strip()
            if v:
                queries.append(v)
    queries.extend(x for x in (extra or []) if x.strip())
    return list(dict.fromkeys(queries))


def dedupe(jobs: list[dict]) -> list[dict]:
    """雙鍵去重：URL 一樣 → 同筆；同來源+公司+職稱 → 也視為同筆。

    後者是為了擋 LinkedIn 同職缺多次 listing（不同 job ID 但內容相同）。
    """
    seen_urls, seen_tuples, out = set(), set(), []
    for j in jobs:
        url = (j.get("url") or "").strip()
        title = (j.get("title") or "").strip()
        company = (j.get("company") or "").strip()
        tup = (j.get("source", ""), title, company)
        if url and url in seen_urls:
            continue
        if title and company and tup in seen_tuples:
            continue
        if url:
            seen_urls.add(url)
        if title and company:
            seen_tuples.add(tup)
        out.append(j)
    return out


APAC_KW = (
    "Singapore", "新加坡",
    "Tokyo", "Japan", "日本", "東京",
    "Hong Kong", "香港",
    "Korea", "Seoul", "韓國", "首爾",
    "Sydney", "Australia", "雪梨", "澳洲", "澳大利亞",
    "Kuala Lumpur", "Malaysia", "馬來西亞", "吉隆坡",
    "Bangkok", "Thailand", "泰國", "曼谷",
)

APAC_LINKEDIN_LOCS = (
    "Singapore", "Tokyo, Japan", "Hong Kong", "Seoul, South Korea",
    "Sydney, Australia", "Kuala Lumpur, Malaysia", "Bangkok, Thailand",
)

# 中英城市對應：LinkedIn 地點是英文（"Taipei, Taiwan"），104/Cake 多為中文。
# passes_filter 對 tw 城市檢查時兩種都比對，避免 LinkedIn 整批被丟（review #1）。
TW_CITY_EN = {
    "台北": ("Taipei",), "臺北": ("Taipei",),
    "新北": ("New Taipei",),
    "桃園": ("Taoyuan",),
    "新竹": ("Hsinchu",),
    "台中": ("Taichung",), "臺中": ("Taichung",),
    "台南": ("Tainan",), "臺南": ("Tainan",),
    "高雄": ("Kaohsiung",),
    "基隆": ("Keelung",),
    "嘉義": ("Chiayi",),
    "宜蘭": ("Yilan",),
}


def _tw_city_match(loc: str, cities: list[str]) -> bool:
    for c in cities:
        if c in loc:
            return True
        for en in TW_CITY_EN.get(c, ()):
            if en in loc:
                return True
    # ponytail: 沒指定城市時，只要任何台灣英文/中文線索都算 tw 命中
    if not cities and ("Taiwan" in loc or "台灣" in loc):
        return True
    return False


def passes_filter(job: dict, cfg: dict) -> bool:
    f = cfg.get("filters", {})
    regions = f.get("regions", ["tw"])
    loc = job.get("location") or ""
    if f.get("allow_remote") and job.get("remote"):
        return True
    cities = f.get("allowed_cities", [])
    for r in regions:
        if r == "tw" and (not cities or _tw_city_match(loc, cities)):
            return True
        if r == "apac" and any(k in loc for k in APAC_KW):
            return True
        if r == "global":
            return True
        if r == "remote" and job.get("remote"):
            return True
    return False


def gather(cfg: dict, max_per: int, extra: list[str]) -> list[dict]:
    queries = collect_queries(cfg, extra)
    regions = cfg.get("filters", {}).get("regions", ["tw"])
    all_jobs: list[dict] = []
    for q in queries:
        print(f"  搜尋「{q}」…")
        if "tw" in regions:
            all_jobs.extend(search_104(q, max_jobs=max_per, pages=1))
        all_jobs.extend(search_cake(q, max_jobs=max_per, pages=1))
        if "tw" in regions:
            all_jobs.extend(search_linkedin(q, max_jobs=30, pages=3, location="Taipei, Taiwan"))
        if "apac" in regions:
            for loc in APAC_LINKEDIN_LOCS:
                all_jobs.extend(search_linkedin(q, max_jobs=15, pages=2, location=loc))
        if "global" in regions:
            all_jobs.extend(search_linkedin(q, max_jobs=30, pages=3, location=""))
        if "remote" in regions:
            all_jobs.extend(search_linkedin(q, max_jobs=30, pages=3, location="", f_wt=2))
        time.sleep(1.5)
    return dedupe(all_jobs)


def enrich_and_filter(jobs: list[dict], cfg: dict, top_n: int, min_jd: int) -> list[dict]:
    pool = []
    for j in jobs:
        if not passes_filter(j, cfg):
            continue
        if score_job(j, cfg)["excluded"]:
            continue
        pool.append(j)
    pool.sort(key=lambda j: score_job(j, cfg)["score"], reverse=True)
    candidates = pool[:top_n]
    print(f"  粗篩後候選 {len(candidates)} 筆，開始抓完整 JD（104/LinkedIn/Cake）…")

    out, n_fetched, n_short = [], 0, 0
    short_by_src: dict[str, int] = {}
    for i, j in enumerate(candidates):
        src = j.get("source")
        if src == "104":
            full = fetch_104_full(j.get("url", ""))
        elif src == "LinkedIn":
            full = fetch_linkedin_full(j.get("url", ""))
        elif src == "Cake":
            full = fetch_cake_full(j.get("url", ""))
        else:
            full = ""
        if full:
            j["description"] = full
            n_fetched += 1
        if len((j.get("description") or "").strip()) >= min_jd:
            out.append(j)
        else:
            n_short += 1
            short_by_src[src or "?"] = short_by_src.get(src or "?", 0) + 1
        if (i + 1) % 50 == 0:
            print(f"    已處理 {i + 1}/{len(candidates)} …")
    short_breakdown = "、".join(f"{k}={v}" for k, v in sorted(short_by_src.items())) or "無"
    print(f"  抓了 {n_fetched} 筆完整 JD；剔除太短 {n_short} 筆（{short_breakdown}）；留下 {len(out)} 筆。")
    return out


def render_html(scored: list[dict], cfg: dict, path: str):
    threshold = cfg.get("scoring", {}).get("threshold", 60)
    recommended = [s for s in scored if s["eval"]["recommended"]]
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    def row(s, rank=None):
        j, e = s["job"], s["eval"]
        title = html.escape(j.get("title", ""))
        company = html.escape(j.get("company", ""))
        loc = html.escape(j.get("location", ""))
        url = html.escape(j.get("url", ""))
        src = html.escape(j.get("source", ""))
        pos = html.escape("、".join(e["matched_pos"][:8]))
        remote = "✅" if j.get("remote") else ""
        rk = f"<td>{rank}</td>" if rank is not None else ""
        new_mark = "✨" if s.get("is_new") else ""
        link = (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>'
            if url else title
        )
        return (
            f"<tr data-src='{src}'>{rk}<td class='new'>{new_mark}</td>"
            f"<td class='score'>{e['score']}</td>"
            f"<td class='sub'>{e.get('score_method2', '')}</td>"
            f"<td class='sub'>{e.get('score_method1', '')}</td>"
            f"<td>{link}</td>"
            f"<td>{company}</td><td>{src}</td><td>{remote}</td>"
            f"<td>{loc}</td><td class='kw'>{pos}</td></tr>"
        )

    rec_rows = "\n".join(row(s, i + 1) for i, s in enumerate(recommended))
    all_rows = "\n".join(row(s) for s in scored)

    doc = f"""<!doctype html>
<html lang="zh-TW"><head><meta charset="utf-8">
<title>NextRole 職缺結果 {now}</title>
<style>
 body{{font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif;margin:24px;color:#1a1a1a}}
 h1{{font-size:22px}} h2{{margin-top:32px;border-bottom:2px solid #eee;padding-bottom:6px}}
 .meta{{color:#666;font-size:13px}}
 table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}}
 th,td{{border:1px solid #e3e3e3;padding:6px 8px;text-align:left;vertical-align:top}}
 th{{background:#f6f8fa;position:sticky;top:0}}
 td.score{{font-weight:700;text-align:center;background:#f0f7ff}}
 td.new{{text-align:center;font-size:16px}}
 td.sub{{text-align:center;color:#666;font-size:12px}}
 td.kw{{color:#0a7a3f;font-size:12px}}
 tr:hover{{background:#fafafa}}
 a{{color:#0b66c2;text-decoration:none}} a:hover{{text-decoration:underline}}
 .pill{{display:inline-block;background:#0b66c2;color:#fff;border-radius:12px;padding:2px 10px;font-size:12px}}
 .fbtn{{margin:2px;padding:3px 12px;border:1px solid #ccc;border-radius:14px;background:#fff;cursor:pointer;font-size:13px}}
 .fbtn.on{{background:#0b66c2;color:#fff;border-color:#0b66c2}}
</style></head><body>
<h1>NextRole 職缺結果</h1>
<p class="meta">產生時間：{now}　|　總職缺：{len(scored)} 筆　|
<span class="pill">推薦（≥{threshold} 分）：{len(recommended)} 筆</span></p>

<h2>⭐ 推薦職缺（評分 ≥ {threshold}，依分數排序）</h2>
<p class="meta">總分 = 技能(60%) + 天賦(40%) − 負向懲罰。子分為各面向契合度(0–100)。</p>
<table><thead><tr><th>#</th><th>新</th><th>總分</th><th>技能</th><th>天賦</th><th>職缺</th><th>公司</th><th>來源</th>
<th>遠端</th><th>地點</th><th>命中關鍵字</th></tr></thead>
<tbody>{rec_rows or '<tr><td colspan=11>目前沒有達門檻的職缺，可調低 threshold 或增加關鍵字。</td></tr>'}</tbody></table>

<h2>📋 廣泛清單（全部職缺，依分數排序）</h2>
<p class="meta">依來源篩選：
<button class="fbtn on" data-f="">全部</button>
<button class="fbtn" data-f="104">104</button>
<button class="fbtn" data-f="Cake">Cake</button>
<button class="fbtn" data-f="LinkedIn">LinkedIn</button>
<span id="fcount" class="meta"></span></p>
<table id="allTable"><thead><tr><th>新</th><th>總分</th><th>技能</th><th>天賦</th><th>職缺</th><th>公司</th><th>來源</th>
<th>遠端</th><th>地點</th><th>命中關鍵字</th></tr></thead>
<tbody>{all_rows}</tbody></table>
<script>
(function(){{
  var btns=document.querySelectorAll('.fbtn');
  var rows=document.querySelectorAll('#allTable tbody tr');
  function apply(f){{
    var n=0;
    rows.forEach(function(r){{
      var show=!f||r.getAttribute('data-src')===f;
      r.style.display=show?'':'none'; if(show)n++;
    }});
    document.getElementById('fcount').textContent='　顯示 '+n+' 筆';
  }}
  btns.forEach(function(b){{
    b.onclick=function(){{
      btns.forEach(function(x){{x.classList.remove('on');}});
      b.classList.add('on'); apply(b.getAttribute('data-f'));
    }};
  }});
}})();
</script>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)


def write_csv(scored: list[dict], path: str):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["新", "總分", "技能", "天賦", "推薦", "職缺", "公司", "來源", "遠端", "地點", "命中關鍵字", "連結"])
        for s in scored:
            j, e = s["job"], s["eval"]
            w.writerow([
                "✨" if s.get("is_new") else "",
                e["score"], e.get("score_method2", ""), e.get("score_method1", ""),
                "Y" if e["recommended"] else "",
                j.get("title", ""), j.get("company", ""), j.get("source", ""),
                "Y" if j.get("remote") else "", j.get("location", ""),
                "、".join(e["matched_pos"]), j.get("url", ""),
            ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=25, help="每站每關鍵字抓取上限")
    ap.add_argument("--queries", nargs="*", default=[], help="額外加入的搜尋詞")
    ap.add_argument("--from-cache", action="store_true",
                    help="用 ./output/_jobs_cache.json 重算（不重爬網路）")
    ap.add_argument("--top", type=int, default=300, help="抓完整 JD 的候選數上限")
    ap.add_argument("--min-jd", type=int, default=250, help="完整 JD 最少字數")
    ap.add_argument("--diff-against", type=str, default=None,
                    help="一份之前的 results CSV 路徑：本次新出現的 URL 會被標 ✨")
    args = ap.parse_args()

    cfg = load_profile()
    if not cfg:
        raise SystemExit("找不到 ~/.nextrole/profile.json — 請先做完技能問卷")

    os.makedirs(OUTPUT, exist_ok=True)

    if args.from_cache and os.path.exists(JOBS_CACHE):
        with open(JOBS_CACHE, encoding="utf-8") as f:
            jobs = json.load(f)
        n_before = len(jobs)
        jobs = dedupe(jobs)  # 套用最新去重規則，方便調規則後立刻看效果
        if len(jobs) != n_before:
            print(f"從快取載入 {n_before} 筆 → 重新去重後 {len(jobs)} 筆，重新評分 …")
        else:
            print(f"從快取載入 {len(jobs)} 筆（未重爬），重新評分 …")
    else:
        print("開始廣撒搜尋 104 / Cake / LinkedIn …")
        jobs = gather(cfg, args.max, args.queries)
        print(f"去重後共 {len(jobs)} 筆。")
        jobs = enrich_and_filter(jobs, cfg, top_n=args.top, min_jd=args.min_jd)
        with open(JOBS_CACHE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False)
        print(f"已快取 {len(jobs)} 筆（含完整 JD），評分中 …")

    scored = []
    for j in jobs:
        if not passes_filter(j, cfg):
            continue
        ev = score_job(j, cfg)
        if ev["excluded"]:
            continue
        scored.append({"job": j, "eval": ev})

    scored.sort(key=lambda s: s["eval"]["score"], reverse=True)

    prev_urls: set[str] = set()
    if args.diff_against and Path(args.diff_against).exists():
        with open(args.diff_against, encoding="utf-8-sig") as f:
            prev_urls = {r["連結"] for r in csv.DictReader(f) if r.get("連結")}
    for s in scored:
        s["is_new"] = bool(prev_urls) and (s["job"].get("url") or "") not in prev_urls

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    html_path = os.path.join(OUTPUT, f"results_{stamp}.html")
    csv_path = os.path.join(OUTPUT, f"results_{stamp}.csv")
    render_html(scored, cfg, html_path)
    write_csv(scored, csv_path)
    rec = sum(1 for s in scored if s["eval"]["recommended"])
    print(f"\n完成！共 {len(scored)} 筆（推薦 {rec} 筆）")
    print(f"  網頁：{html_path}")
    print(f"  CSV ：{csv_path}")
    print(f"\n看 HTML：cd {OUTPUT} && python3 -m http.server 8765")
    print(f"  → 開 http://localhost:8765/results_{stamp}.html（不要用 file://，連結會空白）")


if __name__ == "__main__":
    main()
