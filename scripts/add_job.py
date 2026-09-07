# /// script
# requires-python = ">=3.10"
# ///
"""把使用者貼進來的 JD 加進職缺看板，評分後直接放進契合度診斷頁。

    uv run add_job.py --company 某某科技 --title 產品經理 --url https://... < jd.txt
    pbpaste | uv run add_job.py --company 某某科技 --title 產品經理

⭐ **有原始網址就一定要給。** `job_id` 是網址的 sha1，給了網址，這筆就會跟爬蟲
撈到的同一個職缺合而為一（`board.merge` 只更新分數與 last_seen，你的判斷不動），
不給的話會多出一筆重複的。沒有網址時才用合成的 `nextrole:paste/<公司>/<職稱>`。
"""
from __future__ import annotations

import argparse
import sys

import board as _board
import store
from profile_io import load_profile
from score import score_job

SHORT_JD = 250      # 跟 skills/board 的判準同一條線


def synth_url(company: str, title: str) -> str:
    return f"nextrole:paste/{company.strip()}/{title.strip()}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", required=True, help="公司名")
    ap.add_argument("--title", required=True, help="職缺名稱")
    ap.add_argument("--url", default="", help="原始職缺網址。有就一定要給，才不會跟爬到的重複")
    ap.add_argument("--location", default="", help="地點")
    ap.add_argument("--source", default="貼上", help="來源標記")
    ap.add_argument("--remote", action="store_true", help="標成遠端職缺")
    ap.add_argument("--file", default=None, help="JD 檔案路徑，不給就從 stdin 讀")
    ap.add_argument("--no-save", action="store_true",
                    help="只加進收件匣，不直接放進契合度診斷頁")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            desc = f.read()
    else:
        desc = sys.stdin.read()
    desc = desc.strip()
    if not desc:
        raise SystemExit("沒有讀到 JD 內容。用 --file 指定檔案，或把 JD 從 stdin 餵進來。")

    url = args.url.strip() or synth_url(args.company, args.title)
    job = {
        "source": args.source,
        "title": args.title.strip(),
        "company": args.company.strip(),
        "url": url,
        "location": args.location.strip(),
        "description": desc,
        "salary": None,
        "remote": bool(args.remote),
    }

    cfg = load_profile() or {}
    ev = score_job(job, cfg)

    jid = store.job_id(url)
    existed = jid in _board.load()["jobs"]
    _board.merge([{"job": job, "eval": ev}])   # merge 自己會存，不要再存一次
    if not args.no_save:
        _board.patch(jid, {"saved": True})

    print(f"job_id：{jid}")
    print(f"{'更新了看板上既有的一筆' if existed else '新增到看板'}："
          f"{job['company']} · {job['title']}")
    if not args.url.strip():
        print(f"  沒有給網址，用合成的：{url}")
        print("  ⚠️ 之後爬蟲撈到同一個職缺時會變成兩筆。有網址的話重跑一次並帶 --url。")
    if not args.no_save:
        print("  已放進契合度診斷頁（第二頁）")

    if not cfg:
        print("\n⚠️ 還沒有 profile，評分是 0 分。評分要先做技能問卷（/nextrole:search），"
              "但契合度診斷不吃評分，照樣可以做。")
    else:
        print(f"\n評分 {ev['score']}｜命中 {'、'.join(ev['matched_pos']) or '無'}")

    if len(desc) < SHORT_JD:
        print(f"\n⚠️ JD 只有 {len(desc)} 字。契合度診斷要逐條對照職責清單，"
              f"少於 {SHORT_JD} 字通常代表貼漏了，診斷結果要標明信心低。")

    print(f"\n下一步：做契合度診斷（/nextrole:board），job_id 是 {jid}")


if __name__ == "__main__":
    main()
