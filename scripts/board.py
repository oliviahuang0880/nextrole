"""職缺主檔 ~/.nextrole/board.json 的讀寫。

Merge 的鐵則：重跑搜尋只更新 job / eval / last_seen。
status、notes、fit、artifacts 是使用者的判斷，爬蟲不得覆寫。
"""
from __future__ import annotations

import functools
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store  # noqa: E402

STATUSES = ["new", "interested", "applied", "interviewing", "offer", "rejected", "skipped"]
STATUS_ZH = {
    "new": "新",
    "interested": "想投",
    "applied": "已投",
    "interviewing": "面試中",
    "offer": "Offer",
    "rejected": "已拒",
    "skipped": "略過",
}
# 使用者可以從頁面上改的欄位，其他一律不接受
PATCHABLE = {"status", "notes"}

# board.json 的讀→改→寫必須是不可分割的。serve.py 用 ThreadingHTTPServer，
# 兩個請求同時進來，後寫的會拿著舊快照蓋掉先寫的。
_LOCK = threading.RLock()


def _atomic(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with _LOCK:
            return fn(*args, **kwargs)
    return wrapper


def _empty_fit():
    return {
        "industry": None, "overlap": None, "condition": None, "total": None,
        "hard_blocker": None, "blocker_note": "", "verdict": None, "rated_at": None,
    }


def load() -> dict:
    b = store.read_json(store.BOARD)
    if b is None:
        b = {"version": 1, "updated_at": store.now(), "jobs": {}}
    b.setdefault("jobs", {})
    return b


def save(b: dict):
    b["updated_at"] = store.now()
    return store.write_json(store.BOARD, b)


@_atomic
def merge(scored: list[dict], board: dict | None = None) -> dict:
    """把一次搜尋的評分結果併進 board。回傳統計。"""
    b = board if board is not None else load()
    jobs = b["jobs"]
    ts = store.now()
    added = updated = 0

    for s in scored:
        job, ev = s["job"], s["eval"]
        jid = store.job_id(job.get("url", ""))
        if jid in jobs:
            rec = jobs[jid]
            rec["job"] = job
            rec["eval"] = ev
            rec["last_seen"] = ts
            updated += 1
        else:
            jobs[jid] = {
                "job": job,
                "eval": ev,
                "fit": _empty_fit(),
                "status": "new",
                "notes": "",
                "first_seen": ts,
                "last_seen": ts,
                "applied_at": None,
                "artifacts": {"resume": None, "cover_letter": None, "qa": None, "sheet_tab": None},
            }
            added += 1

    save(b)
    return {"added": added, "updated": updated, "total": len(jobs)}


@_atomic
def patch(jid: str, fields: dict, board: dict | None = None) -> dict:
    """從頁面來的修改。只接受 PATCHABLE 白名單。"""
    b = board if board is not None else load()
    rec = b["jobs"].get(jid)
    if rec is None:
        raise KeyError(jid)

    unknown = set(fields) - PATCHABLE
    if unknown:
        raise ValueError(f"不允許的欄位：{'、'.join(sorted(unknown))}")

    if "status" in fields:
        st = fields["status"]
        if st not in STATUSES:
            raise ValueError(f"未知狀態：{st}")
        if st == "applied" and not rec.get("applied_at"):
            rec["applied_at"] = store.now()
        rec["status"] = st
    if "notes" in fields:
        rec["notes"] = str(fields["notes"])[:2000]

    save(b)
    return rec


@_atomic
def set_fit(jid: str, fit: dict, board: dict | None = None) -> dict:
    """寫入適合度評分。三指標 + 硬門檻，total 與 verdict 由這裡算，不信外面給的。"""
    b = board if board is not None else load()
    rec = b["jobs"].get(jid)
    if rec is None:
        raise KeyError(jid)

    industry = int(fit["industry"])
    overlap = int(fit["overlap"])
    condition = int(fit["condition"])
    for name, v, hi in (("industry", industry, 4), ("overlap", overlap, 4), ("condition", condition, 5)):
        if not 1 <= v <= hi:
            raise ValueError(f"{name} 必須介於 1–{hi}，收到 {v}")

    total = industry + overlap + condition
    blocked = bool(fit.get("hard_blocker"))
    threshold = store.load_config()["fit_threshold"]
    if blocked:
        verdict = "不投"
    elif total >= threshold + 1:
        verdict = "投"
    elif total >= threshold:
        verdict = "邊緣"
    else:
        verdict = "不投"

    rec["fit"] = {
        "industry": industry, "overlap": overlap, "condition": condition,
        "total": total, "hard_blocker": blocked,
        "blocker_note": str(fit.get("blocker_note", ""))[:500],
        "verdict": verdict, "rated_at": store.now(),
    }
    save(b)
    return rec["fit"]


@_atomic
def set_artifact(jid: str, key: str, value, board: dict | None = None):
    b = board if board is not None else load()
    rec = b["jobs"].get(jid)
    if rec is None:
        raise KeyError(jid)
    if key not in {"resume", "cover_letter", "qa", "sheet_tab"}:
        raise ValueError(f"未知產出欄位：{key}")
    rec["artifacts"][key] = value
    save(b)
    return rec["artifacts"]


def counts(board: dict | None = None) -> dict:
    b = board if board is not None else load()
    out = {s: 0 for s in STATUSES}
    rated = 0
    for rec in b["jobs"].values():
        out[rec.get("status", "new")] = out.get(rec.get("status", "new"), 0) + 1
        if rec.get("fit", {}).get("total") is not None:
            rated += 1
    out["_total"] = len(b["jobs"])
    out["_rated"] = rated
    return out
