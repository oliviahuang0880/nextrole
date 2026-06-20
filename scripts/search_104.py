"""查 104 人力銀行公開職缺搜尋介面，回傳統一格式的職缺清單。

104 的搜尋頁背後是一個會回傳 JSON 的 list endpoint。需要帶 Referer，
否則會被擋。每個關鍵字抓前幾頁、彙整成統一的 job dict。
"""
from __future__ import annotations

import time

import http_client

LIST_URL = "https://www.104.com.tw/jobs/search/api/jobs"
# 後備：舊版 list endpoint（若上面改版時嘗試）
LIST_URL_FALLBACK = "https://www.104.com.tw/jobs/search/list"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://www.104.com.tw/jobs/search/",
    "Accept": "application/json, text/plain, */*",
}


def _normalize_link(link: str) -> str:
    if not link:
        return ""
    if link.startswith("//"):
        return "https:" + link
    if link.startswith("http"):
        return link
    return "https://www.104.com.tw" + link


def search_104(keyword: str, max_jobs: int = 25, pages: int = 2, delay: float = 1.0):
    """回傳該關鍵字的職缺清單（統一格式）。失敗時回傳空清單並印出原因。"""
    jobs = []
    for page in range(1, pages + 1):
        params = {
            "ro": 0,           # 0=不限全職/兼職
            "kwop": 7,         # 關鍵字比對方式
            "keyword": keyword,
            "order": 14,       # 相關度排序
            "asc": 0,
            "page": page,
            "mode": "s",
            "jobsource": "2018indexpoc",
        }
        try:
            resp = http_client.get(LIST_URL, params=params, headers=HEADERS, timeout=20)
            data = resp.json()
        except Exception as e:  # noqa: BLE001
            print(f"[104] 關鍵字「{keyword}」第 {page} 頁失敗：{e}")
            break

        items = data.get("data") or []
        if not items:
            break

        for it in items:
            link = it.get("link") or {}
            jobs.append(
                {
                    "source": "104",
                    "title": it.get("jobName", "").strip(),
                    "company": it.get("custName", "").strip(),
                    "url": _normalize_link(link.get("job", "")),
                    "location": it.get("jobAddrNoDesc", "") or it.get("jobAddress", ""),
                    "description": it.get("description", "").strip(),
                    "salary": it.get("salaryLow"),
                    # 104 remoteWorkType: 0/None=無, 1=部分遠端, 2=完全遠端
                    "remote": bool(it.get("remoteWorkType")),
                }
            )
            if len(jobs) >= max_jobs:
                return jobs
        time.sleep(delay)
    return jobs


def _jobno_from_url(url: str) -> str:
    return (url or "").split("?")[0].rstrip("/").split("/")[-1]


def fetch_104_full(url: str, delay: float = 0.3) -> str:
    """抓 104 職缺的完整 JD 文字（搜尋 API 只回約 100 字摘要）。失敗回空字串。"""
    jobno = _jobno_from_url(url)
    if not jobno:
        return ""
    api = f"https://www.104.com.tw/job/ajax/content/{jobno}"
    headers = dict(HEADERS)
    headers["Referer"] = f"https://www.104.com.tw/job/{jobno}"
    headers["Accept"] = "application/json, text/plain, */*"
    try:
        resp = http_client.get(api, headers=headers, timeout=15)
        data = (resp.json() or {}).get("data") or {}
        jd = data.get("jobDetail") or {}
        parts = [
            jd.get("jobDescription", ""),
            (jd.get("otherRequirement") or ""),
        ]
        cond = data.get("condition") or {}
        parts.append(cond.get("other", "") or "")
        time.sleep(delay)
        return "\n".join(p for p in parts if p).strip()
    except Exception as e:  # noqa: BLE001
        print(f"[104] 抓完整 JD 失敗（{jobno}）：{e}")
        return ""


if __name__ == "__main__":
    import json
    import sys

    kw = sys.argv[1] if len(sys.argv) > 1 else "數據分析"
    result = search_104(kw, max_jobs=10, pages=1)
    print(f"關鍵字「{kw}」抓到 {len(result)} 筆")
    print(json.dumps(result[:3], ensure_ascii=False, indent=2))
