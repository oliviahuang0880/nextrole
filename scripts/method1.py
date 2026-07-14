"""方法一（天賦）：邀請 5–6 位認識的人填「你眼中的他」純文字。

天賦的「彙整」由對話中的 AI 助手（Claude / Codex 等）直接做——把回覆濃縮成
共通天賦關鍵字、寫成 talents.json，再由 merge_talents.py 呼叫本檔的
merge_into() 併入 profile 的 method1_positive（天賦，權重 2）。
不呼叫任何 AI API、不需要 API key。
"""
from __future__ import annotations

import copy


def merge_into(base: dict | None, talents: list[dict]) -> dict:
    """把天賦併入既有 profile（多半來自技能問卷）；沒有 base 時建最小 profile。

    有方法二技能時 blend 0.6/0.4；只有方法一時 100% 方法一（但提醒仍需技能問卷產生搜尋詞）。
    """
    if base:
        p = copy.deepcopy(base)
    else:
        p = {
            "method2_positive": [], "negative": [], "field_terms": [],
            "filters": {"allowed_cities": ["台北", "新北"], "allow_remote": True},
            "scoring": {"method2_full": 12, "title_boost": 2.0, "threshold": 60, "use_field_terms": False},
        }
    p["method1_positive"] = talents
    total = sum(t.get("weight", 2) for t in talents) or 1
    has_m2 = bool(p.get("method2_positive"))
    sc = p.setdefault("scoring", {})
    sc["blend_method2"] = 0.6 if has_m2 else 0.0
    sc["blend_method1"] = 0.4 if has_m2 else 1.0
    sc["method1_full"] = max(8, round(0.5 * total))
    sc.setdefault("method2_full", 12)
    sc.setdefault("threshold", 60)
    sc.setdefault("title_boost", 2.0)
    sc.setdefault("use_field_terms", False)
    p.setdefault("_meta", {})["method1"] = "aggregated"
    return p
