"""查 Cake（cakeresume）職缺搜尋，回傳統一格式的職缺清單。

Cake 是 Next.js 網站，職缺資料藏在頁面的 <script id="__NEXT_DATA__"> JSON
裡的 props.pageProps.initialState.jobSearch.entityByPathId。直接解析這段，
不需要瀏覽器渲染。
"""
from __future__ import annotations

import json
import re
import time
from urllib.parse import quote

from bs4 import BeautifulSoup

import http_client

SEARCH_URL = "https://www.cake.me/jobs"

_NEXT_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)


def _get_with_retry(url: str, retries: int = 4):
    """走共享 Session（含代理）抓取；429/5xx 退避重試由 http_client 處理。"""
    return http_client.get(url, timeout=20, retries=retries)


def _job_url(entity: dict) -> str:
    page = entity.get("page") or {}
    company_path = page.get("path", "")
    job_path = entity.get("path", "")
    if company_path and job_path:
        return f"https://www.cake.me/companies/{company_path}/jobs/{job_path}"
    return ""


def _is_remote(entity: dict) -> bool:
    locs = " ".join(entity.get("locations") or [])
    return ("remote" in locs.lower()) or ("遠端" in locs) or ("遠距" in locs)


def search_cake(keyword: str, max_jobs: int = 25, pages: int = 2, delay: float = 1.0):
    """回傳該關鍵字的 Cake 職缺清單（統一格式）。失敗回傳空清單。"""
    jobs = []
    for page in range(1, pages + 1):
        url = f"{SEARCH_URL}?q={quote(keyword)}&page={page}"
        try:
            resp = _get_with_retry(url)
            m = _NEXT_RE.search(resp.text)
            if not m:
                print(f"[Cake] 關鍵字「{keyword}」第 {page} 頁找不到資料區塊")
                break
            data = json.loads(m.group(1))
            entities = (
                data.get("props", {})
                .get("pageProps", {})
                .get("initialState", {})
                .get("jobSearch", {})
                .get("entityByPathId", {})
            )
        except Exception as e:  # noqa: BLE001
            print(f"[Cake] 關鍵字「{keyword}」第 {page} 頁失敗：{e}")
            break

        if not entities:
            break

        for ent in entities.values():
            page_info = ent.get("page") or {}
            jobs.append(
                {
                    "source": "Cake",
                    "title": ent.get("title", "").strip(),
                    "company": page_info.get("name", "").strip(),
                    "url": _job_url(ent),
                    "location": " / ".join(ent.get("locations") or []),
                    "description": (ent.get("description") or "").strip(),
                    "salary": (ent.get("salary") or {}).get("min"),
                    "remote": _is_remote(ent),
                }
            )
            if len(jobs) >= max_jobs:
                return jobs
        time.sleep(delay)
    return jobs


def fetch_cake_full(url: str, delay: float = 0.4) -> str:
    """抓 Cake 職缺頁的完整 JD（job.description + requirements，去 HTML）。失敗回空字串。

    ponytail: 走 SSR 的 __NEXT_DATA__，不需要瀏覽器渲染。
              ceiling: Cake 改頁面結構或欄位名時會失效，下游靠 min_jd 兜底。
    """
    if not url:
        return ""
    try:
        resp = _get_with_retry(url, retries=2)
    except Exception as e:  # noqa: BLE001
        print(f"[Cake] 抓完整 JD 失敗：{e}")
        return ""
    m = _NEXT_RE.search(resp.text)
    if not m:
        return ""
    try:
        data = json.loads(m.group(1))
        job = data.get("props", {}).get("pageProps", {}).get("job", {}) or {}
    except Exception:  # noqa: BLE001
        return ""
    parts = []
    for k in ("description", "requirements"):
        v = job.get(k) or ""
        if v:
            parts.append(BeautifulSoup(v, "html.parser").get_text("\n", strip=True))
    time.sleep(delay)
    return "\n\n".join(p for p in parts if p)


if __name__ == "__main__":
    import sys

    kw = sys.argv[1] if len(sys.argv) > 1 else "data analysis"
    result = search_cake(kw, max_jobs=10, pages=1)
    print(f"關鍵字「{kw}」抓到 {len(result)} 筆")
    print(json.dumps(result[:3], ensure_ascii=False, indent=2))
    if result:
        full = fetch_cake_full(result[0]["url"])
        print(f"\n第一筆完整 JD 長度：{len(full)}；前 150 字：{full[:150]}")
