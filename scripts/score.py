"""職缺評分引擎（雙面向）：讀 profile/keywords.json，對每筆職缺算 0–100 分。

總分 = 100 × (方法二權重 × 方法二契合度 + 方法一權重 × 方法一契合度) − 負向懲罰

- 方法二契合度 = 命中 method2_positive 關鍵字的加權分 / method2_full，上限 1。
  命中出現在「職稱」者再乘 title_boost。
- 方法一契合度 = 命中 method1_positive（6 人共通天賦）的加權分 / method1_full，上限 1。
- 兩面向都要高度命中才拿高分 → 100 分稀有。
- 負向：命中 penalty 扣分；命中含 exclude 的詞 → 整筆剔除（score=0）。
- 達 threshold 者標記為「推薦」。
"""
from __future__ import annotations

import json
import os
import re

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "..", "profile")
DEFAULT_KEYWORDS = os.path.join(PROFILE_DIR, "keywords.json")


def load_config(path: str = DEFAULT_KEYWORDS) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _terms(entry: dict) -> list[str]:
    out = []
    for key in ("term", "en"):
        v = (entry.get(key) or "").strip()
        if v:
            out.append(v.lower())
    return out


def _match(term: str, text: str) -> bool:
    """ASCII 詞用 word boundary（避免 perform 命中 performance），
    中文/Unicode 詞用子字串（中文沒詞界線）。"""
    if term.isascii():
        return re.search(r"(?<![A-Za-z0-9_])" + re.escape(term) + r"(?![A-Za-z0-9_])", text) is not None
    return term in text


def _any_match(terms: list[str], text: str) -> bool:
    return any(_match(t, text) for t in terms)


def _dimension_raw(entries: list[dict], body: str, title: str, title_boost: float):
    """回傳 (加權命中分, 命中詞清單)。

    命中越多分越高：把「所有」命中的有效權重全部累加（不取前 N）。
    有效權重 = 權重 ×(在職稱再乘 title_boost)。
    """
    raw = 0.0
    matched = []
    for entry in entries:
        terms = _terms(entry)
        if not terms or not _any_match(terms, body):
            continue
        weight = entry.get("weight", 1)
        in_title = _any_match(terms, title)
        raw += weight * (title_boost if in_title else 1)
        matched.append(entry.get("term") or entry.get("en"))
    return raw, matched


def score_job(job: dict, config: dict) -> dict:
    s = config.get("scoring", {})
    title_boost = s.get("title_boost", 2.0)
    threshold = s.get("threshold", 60)
    w2 = s.get("blend_method2", 0.6)
    w1 = s.get("blend_method1", 0.4)
    m2_full = s.get("method2_full", 24) or 24
    m1_full = s.get("method1_full", 12) or 12

    title = (job.get("title") or "").lower()
    body = (
        (job.get("title") or "")
        + " "
        + (job.get("description") or "")
        + " "
        + (job.get("company") or "")
    ).lower()

    # 方法二關鍵字：預設只用通用技能詞；use_field_terms 開啟時才併入 UX/產品領域詞
    m2_entries = list(config.get("method2_positive", []))
    if s.get("use_field_terms"):
        m2_entries += config.get("field_terms", [])

    raw2, matched2 = _dimension_raw(m2_entries, body, title, title_boost)
    raw1, matched1 = _dimension_raw(config.get("method1_positive", []), body, title, title_boost)

    # 不設每面向上限：命中越多 → fit 越大 → 分數越高（最後總分才夾到 100）
    fit2 = raw2 / m2_full
    fit1 = raw1 / m1_full

    # 負向
    excluded = False
    matched_neg = []
    penalty = 0.0
    for entry in config.get("negative", []):
        terms = _terms(entry)
        if not terms:
            continue
        if _any_match(terms, body):
            matched_neg.append(entry.get("term") or entry.get("en"))
            if entry.get("exclude"):
                excluded = True
            elif entry.get("exclude_if_title") and _any_match(terms, title):
                # Cold 詞出現在職稱＝主要職務 → 排除；只在內文 → 改重扣分
                excluded = True
            else:
                penalty += entry.get("penalty", 0)

    base = 100 * (w2 * fit2 + w1 * fit1)
    score = max(0, min(100, round(base - penalty)))

    return {
        "score": 0 if excluded else int(score),
        "score_method2": min(100, round(100 * fit2)),
        "score_method1": min(100, round(100 * fit1)),
        "penalty": int(penalty),
        "matched_pos": matched2 + matched1,
        "matched_method2": matched2,
        "matched_method1": matched1,
        "matched_neg": matched_neg,
        "excluded": excluded,
        "recommended": (not excluded) and score >= threshold,
    }


if __name__ == "__main__":
    # 自測：用 build_profile 即時生一份 config（不依賴外部 keywords.json）
    from method2 import build_profile
    cfg = build_profile({"research": "on_fire", "analyze": "on_fire", "perform": "cold"}, base={}, notes={})

    # ponytail: 兩個 assert 同時測 word-boundary 修法（#2）與正常評分
    asc_body = "data analytics and high-performance marketing"
    assert _match("perform", asc_body) is False, "word-boundary 失效：perform 不該命中 performance"
    assert _match("analytics", asc_body) is True

    sample = {
        "title": "資深使用者研究員 UX Researcher",
        "description": "進行使用者研究與訪談、分析資料找出洞察；需具備良好溝通、跨部門協作與同理心，主動且當責。",
        "company": "範例公司",
    }
    print(json.dumps(score_job(sample, cfg), ensure_ascii=False, indent=2))
