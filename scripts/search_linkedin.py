"""查 LinkedIn 職缺（免登入的訪客 API），回傳統一格式的職缺清單。

LinkedIn 需登入才能看完整站，但有一個公開的「訪客」端點會回傳職缺卡片
HTML，不需登入：
  https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
單一職缺的完整 JD 也有對應訪客端點：
  https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/<jobId>
"""
from __future__ import annotations

import re
import time

from bs4 import BeautifulSoup

import http_client

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JD_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def _jobid(url: str) -> str:
    m = re.search(r"-(\d+)(?:[/?]|$)", url or "")
    return m.group(1) if m else ""


_REMOTE_HINTS = ("remote", "遠端", "遠距")


def _looks_remote(text: str) -> bool:
    s = (text or "").lower()
    return any(h in s for h in _REMOTE_HINTS)


def search_linkedin(keyword: str, max_jobs: int = 20, location: str = "Taipei, Taiwan",
                    pages: int = 1, delay: float = 1.0, f_wt: int | None = None):
    """回傳該關鍵字的 LinkedIn 職缺卡片（統一格式，description 先留空，候選階段再補）。

    f_wt: LinkedIn work type filter — 1=onsite, 2=remote, 3=hybrid。
    ponytail: 訪客 API 無公開文件，f_WT 是觀察值；下游靠 job.remote 兜底。
    """
    jobs = []
    for page in range(pages):
        params: dict = {"keywords": keyword, "location": location, "start": page * 10}
        if f_wt is not None:
            params["f_WT"] = f_wt
        try:
            resp = http_client.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
        except Exception as e:  # noqa: BLE001
            print(f"[LinkedIn] 關鍵字「{keyword}」失敗：{e}")
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("li")
        if not cards:
            break
        for li in cards:
            t = li.select_one(".base-search-card__title")
            if not t:
                continue
            co = li.select_one(".base-search-card__subtitle")
            loc = li.select_one(".job-search-card__location")
            a = li.select_one("a.base-card__full-link") or li.select_one("a")
            url = a["href"].split("?")[0] if (a and a.has_attr("href")) else ""
            loc_text = loc.get_text(strip=True) if loc else ""
            title_text = t.get_text(strip=True)
            jobs.append({
                "source": "LinkedIn",
                "title": title_text,
                "company": co.get_text(strip=True) if co else "",
                "url": url,
                "location": loc_text,
                "description": "",
                "remote": _looks_remote(loc_text) or _looks_remote(title_text) or f_wt == 2,
            })
            if len(jobs) >= max_jobs:
                return jobs
        time.sleep(delay)
    return jobs


def fetch_linkedin_full(url: str, delay: float = 0.4) -> str:
    """抓 LinkedIn 職缺完整 JD（訪客端點）。失敗回空字串。"""
    jid = _jobid(url)
    if not jid:
        return ""
    try:
        resp = http_client.get(JD_URL.format(jid=jid), headers=HEADERS, timeout=15)
    except Exception as e:  # noqa: BLE001
        print(f"[LinkedIn] 抓完整 JD 失敗（{jid}）：{e}")
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    d = soup.select_one(".show-more-less-html__markup") or soup.select_one(".description__text")
    time.sleep(delay)
    return d.get_text("\n", strip=True) if d else ""


if __name__ == "__main__":
    import sys

    kw = sys.argv[1] if len(sys.argv) > 1 else "研究"
    res = search_linkedin(kw, max_jobs=8)
    print(f"關鍵字「{kw}」抓到 {len(res)} 筆")
    for j in res[:5]:
        print(f"  {j['title']} | {j['company']} | {j['location']}")
    if res:
        jd = fetch_linkedin_full(res[0]["url"])
        print(f"\n第一筆 JD 長度：{len(jd)}；前 150 字：{jd[:150]}")
