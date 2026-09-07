"""職缺主檔 ~/.nextrole/board.json 的讀寫。

Merge 的鐵則：重跑搜尋只更新 job / eval / last_seen。
status、notes、fit、artifacts 是使用者的判斷，爬蟲不得覆寫。
"""
from __future__ import annotations

import functools
import os
import re
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store  # noqa: E402

# 三頁各管一件事，流動方向是單向的：收件匣 → 分析 → 投遞追蹤。
#   收件匣  stage="inbox"     還沒取捨的（not seen, not saved）
#   分析    stage="saved"     按了儲存、但還沒投的
#   追蹤    stage="tracker"   真的投出去了（status 不是 None）
STAGES = ["inbox", "saved", "tracker"]
# 不在任何一頁的表格裡，只活在彈窗中。離開收件匣的路是單向的：
# 按過 ✓、或從診斷頁移出的，都不會自己再回到收件匣。
ASIDE = ["dismissed", "removed"]

# 投遞之後的狀態。沒投遞的職缺 status 是 None，不在這個清單裡。
STATUSES = ["applied", "first", "second", "third", "offer", "thanks", "ghosted"]
STATUS_ZH = {
    "applied": "已投遞",
    "first": "一面",
    "second": "二面",
    "third": "三面",
    "offer": "Offer",
    "thanks": "感謝信",
    "ghosted": "無聲卡",
}
# 漏斗順序（tracker 頁的階段轉換率就是照這個算）。
# 感謝信與無聲卡是終點，不在漏斗上 —— 不知道是在哪一關掉的。
FUNNEL = ["applied", "first", "second", "third", "offer"]
ENDED = {"thanks", "ghosted"}

# 使用者可以從頁面上改的欄位，其他一律不接受
PATCHABLE = {"status", "notes", "seen", "saved", "applied_at"}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# v1 → v2：舊的單一 status 拆成 seen / saved / status
_V1_MAP = {
    "new":          {"seen": False, "saved": False, "status": None},
    "interested":   {"seen": True,  "saved": True,  "status": None},
    "skipped":      {"seen": True,  "saved": False, "status": None},
    "applied":      {"seen": True,  "saved": True,  "status": "applied"},
    "interviewing": {"seen": True,  "saved": True,  "status": "interviewing"},
    "offer":        {"seen": True,  "saved": True,  "status": "offer"},
    "rejected":     {"seen": True,  "saved": True,  "status": "rejected"},
}

# v2 → v3：面試階段改用一面／二面／三面，拒絕拆成感謝信與無聲卡
_V2_STATUS = {
    "screening": "applied",       # 「履歷審查」拿掉了，退回已投遞
    "interviewing": "first",
    "final": "third",
    "rejected": "thanks",
}

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


def _migrate(b: dict) -> bool:
    """升級舊版 board.json。回傳有沒有真的改到。"""
    v = b.get("version", 1)
    if v >= 4:
        return False
    if v < 2:
        for rec in b.get("jobs", {}).values():
            old = rec.pop("status", "new")
            rec.update(_V1_MAP.get(old, _V1_MAP["new"]))
    if v < 3:
        for rec in b.get("jobs", {}).values():
            st = rec.get("status")
            if st in _V2_STATUS:
                rec["status"] = _V2_STATUS[st]
    if v < 4:
        for rec in b.get("jobs", {}).values():
            rec.setdefault("ever_saved", bool(rec.get("saved") or rec.get("status")))
    b["version"] = 4
    return True


def load() -> dict:
    b = store.read_json(store.BOARD)
    if b is None:
        b = {"version": 4, "updated_at": store.now(), "jobs": {}}
    b.setdefault("jobs", {})
    if _migrate(b):
        store.write_json(store.BOARD, b)
    return b


def stage_of(rec: dict) -> str:
    if rec.get("status"):
        return "tracker"
    if rec.get("saved"):
        return "saved"
    if rec.get("ever_saved"):
        # 存過又移出診斷頁：使用者已經對它做過判斷了，不該再出現在收件匣
        # 等他重新取捨一次。要找回來是走診斷頁的「已移出」彈窗。
        return "removed"
    if rec.get("seen"):
        return "dismissed"
    return "inbox"


def in_stage(b: dict, stage: str) -> list[tuple[str, dict]]:
    return [(jid, r) for jid, r in b["jobs"].items() if stage_of(r) == stage]


def dismissed(b: dict) -> list[tuple[str, dict]]:
    """收件匣按了勾勾收起來的。存過又移出的不算在這裡 —— 那是 removed。"""
    return in_stage(b, "dismissed")


def removed_from_analysis(b: dict) -> list[tuple[str, dict]]:
    """曾經存進診斷頁、後來又移出的。"""
    return in_stage(b, "removed")


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
                "seen": False,
                "saved": False,
                "ever_saved": False,
                "status": None,
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
        st = fields["status"] or None
        if st is not None and st not in STATUSES:
            raise ValueError(f"未知狀態：{st}")
        if st is not None:
            # 投遞就代表這筆一定存過（要先進分析頁才投得出去）。
            # 但「看過」是另一回事 —— 那是收件匣的取捨動作，不要替使用者按。
            rec["saved"] = True
            rec["ever_saved"] = True
            if not rec.get("applied_at"):
                rec["applied_at"] = store.now()[:10]     # 只記日期，跟頁面上的日期選擇器一致
        rec["status"] = st
    if "seen" in fields:
        rec["seen"] = bool(fields["seen"])
    if "saved" in fields:
        rec["saved"] = bool(fields["saved"])
        if rec["saved"]:
            rec["ever_saved"] = True    # 記著曾經存過，移出分析後才找得回來
    if "applied_at" in fields:
        d = (fields["applied_at"] or "").strip()
        if d and not _DATE_RE.match(d):
            raise ValueError(f"投遞日要是 YYYY-MM-DD，收到 {d!r}")
        rec["applied_at"] = d or None
    if "notes" in fields:
        rec["notes"] = str(fields["notes"])[:2000]

    save(b)
    return rec


@_atomic
def set_fit(jid: str, fit: dict, board: dict | None = None) -> dict:
    """寫入契合度診斷。三指標 + 硬門檻，total 與 verdict 由這裡算，不信外面給的。"""
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
    """三頁各自的計數。前綴 _ 的是跨頁的總計。"""
    b = board if board is not None else load()
    out = {s: 0 for s in STATUSES}
    out.update({st: 0 for st in STAGES + ASIDE})
    rated = seen = 0
    for rec in b["jobs"].values():
        out[stage_of(rec)] += 1
        if rec.get("status"):
            out[rec["status"]] += 1
        if rec.get("fit", {}).get("total") is not None:
            rated += 1
        if rec.get("seen"):
            seen += 1
    # 導覽列的數字要等於收件匣頁面上實際畫得出來的列數。已儲存的仍然留在
    # 清單上（★ 亮著、不能再按），不畫的只有已投遞／按過 ✓／從診斷頁移出的。
    out["inbox"] += out["saved"]
    out["_total"] = len(b["jobs"])
    out["_rated"] = rated
    out["_seen"] = seen
    out["_dismissed"] = out["dismissed"]
    return out


def funnel(board: dict | None = None) -> list[dict]:
    """投遞漏斗。每一階段算的是「有走到這裡（含更後面）」的筆數。"""
    b = board if board is not None else load()
    applied = [r for r in b["jobs"].values() if r.get("status")]
    base = len(applied)
    reached: dict[str, int] = {}
    for i, st in enumerate(FUNNEL):
        if st == "applied":
            # 投出去的都算走到這一步，包含後來收到感謝信或無聲卡的
            reached[st] = base
            continue
        later = set(FUNNEL[i:])
        reached[st] = sum(1 for r in applied if r["status"] in later)
    # 感謝信與無聲卡不知道是在哪一關掉的，只計入「已投遞」，後面幾關不重複計算
    return [
        {"key": st, "label": STATUS_ZH[st], "n": reached[st],
         "pct": round(100 * reached[st] / base, 1) if base else 0.0}
        for st in FUNNEL
    ]
