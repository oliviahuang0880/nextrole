#!/usr/bin/env python3
"""用實際投遞結果校準投遞門檻。

框架給的門檻是 7 分，但每個人的命中率不同。這支看使用者投過的職缺裡，
哪個分數以下幾乎沒有進到面試 — 那才是他真正的門檻。

uv run calibrate.py [--min-sample 10]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as bd  # noqa: E402
import store  # noqa: E402

# 投出去之後有走到這些狀態，就算「有回應」
RESPONDED = {"interviewing", "offer"}
# 這些狀態代表確實投出去了
APPLIED = {"applied", "interviewing", "offer", "rejected"}


def collect(b: dict) -> list[dict]:
    out = []
    for rec in b["jobs"].values():
        if rec.get("status") not in APPLIED:
            continue
        fit = rec.get("fit") or {}
        if fit.get("total") is None:
            continue
        out.append({
            "company": rec.get("job", {}).get("company", ""),
            "total": fit["total"],
            "blocked": bool(fit.get("hard_blocker")),
            "responded": rec.get("status") in RESPONDED,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-sample", type=int, default=10)
    args = ap.parse_args()

    b = bd.load()
    rows = collect(b)
    cfg = store.load_config()
    current = cfg["fit_threshold"]

    print(f"目前門檻：{current} 分")
    if len(rows) < args.min_sample:
        print(f"樣本只有 {len(rows)} 筆（已投遞且已做契合度診斷），還不夠校準。")
        print(f"至少要 {args.min_sample} 筆才有參考價值 — 再投幾家，或把投過的舊職缺補做契合度診斷。")
        return

    print(f"樣本 {len(rows)} 筆（已投遞且已做契合度診斷）\n")
    print("  分數  投遞  有回應  回應率")
    by_score: dict[int, list[dict]] = {}
    for r in rows:
        by_score.setdefault(r["total"], []).append(r)

    suggested = None
    for total in sorted(by_score):
        g = by_score[total]
        hit = sum(1 for x in g if x["responded"])
        rate = hit / len(g)
        print(f"  {total:>4}  {len(g):>4}  {hit:>6}  {rate:>5.0%}")
        if suggested is None and hit > 0:
            suggested = total

    print()
    if suggested is None:
        print("投出去的還沒有任何一家進到面試 — 這不是門檻的問題，先看看是不是都踩到硬門檻。")
    elif suggested == min(by_score):
        print(f"最低分的 {suggested} 分也有回應，看不出下限。門檻維持 {current} 分就好。")
    else:
        print(f"建議門檻：{suggested} 分（{suggested} 分以下投了 "
              f"{sum(len(by_score[t]) for t in by_score if t < suggested)} 家、零回應）")
        if suggested != current:
            print(f"  → 跟目前的 {current} 分不同。要改的話，把 config.json 的 fit_threshold 設成 {suggested}。")

    blocked = [r for r in rows if r["blocked"]]
    if blocked:
        hit = sum(1 for r in blocked if r["responded"])
        print(f"\n踩到硬門檻仍投遞的有 {len(blocked)} 家，其中 {hit} 家有回應。")
        if hit == 0:
            print("  → 硬門檻的判斷是準的，被擋下來的不用再投。")

    no_resp = [r for r in rows if not r["responded"] and not r["blocked"]]
    if no_resp:
        print(f"\n⭐ 沒回應、也沒踩到已知硬門檻的有 {len(no_resp)} 家："
              f"{'、'.join(r['company'] for r in no_resp[:8])}"
              f"{'…' if len(no_resp) > 8 else ''}")
        print("  → 值得回頭看這幾家的 JD 有沒有共同的必要條件 — 那可能是還沒登記的硬門檻。")


if __name__ == "__main__":
    main()
