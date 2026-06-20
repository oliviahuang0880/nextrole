"""產生 LinkedIn / JobFrog 的搜尋網址，供瀏覽器自動化（Claude-in-Chrome）使用。

這兩站需要登入或前端渲染，不能用腳本直接爬；這支只負責把關鍵字組成
搜尋網址，由 Claude 操作使用者已登入的 Chrome 開啟、讀取職缺，再回填
到同一份評分流程（output/browser_jobs.json）。
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "..", "profile")


def linkedin_url(keyword: str, taiwan: bool = True, remote: bool = True) -> str:
    params = [f"keywords={quote(keyword)}"]
    if taiwan:
        params.append("location=Taiwan")
    if remote:
        # f_WT=2 完全遠端, 3 混合；用 2,3 同時含遠端與混合
        params.append("f_WT=2%2C3")
    return "https://www.linkedin.com/jobs/search/?" + "&".join(params)


def jobfrog_url(keyword: str) -> str:
    return f"https://job-frog.com/search?q={quote(keyword)}"


def build_urls(keywords_path: str = os.path.join(PROFILE_DIR, "keywords.json")) -> dict:
    with open(keywords_path, encoding="utf-8") as f:
        cfg = json.load(f)
    # 搜尋詞 = 候選職稱（較像職缺名）+ 權重最高的幾個正向關鍵字
    titles = cfg.get("candidate_titles", [])
    top_pos = [
        e.get("en") or e.get("term")
        for e in sorted(cfg.get("method2_positive", []), key=lambda e: -e.get("weight", 1))[:6]
    ]
    queries = list(dict.fromkeys([*titles, *top_pos]))  # 去重保序
    return {
        "linkedin": [{"q": q, "url": linkedin_url(q)} for q in queries],
        "jobfrog": [{"q": q, "url": jobfrog_url(q)} for q in queries],
    }


if __name__ == "__main__":
    print(json.dumps(build_urls(), ensure_ascii=False, indent=2))
