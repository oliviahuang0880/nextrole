"""方法一（天賦）：邀請 5–6 位認識的人填「你眼中的他」純文字，AI 一次彙整出
共通天賦 → 併入 keywords.json 的 method1_positive（天賦，權重 2）。

開發期省 token：FINDWORK_MOCK_AI（預設 "1"=開）時不呼叫 Claude，回一組合理的
預設共通天賦；上線前設 FINDWORK_MOCK_AI=0 並提供 ANTHROPIC_API_KEY 才走真 AI。
"""
from __future__ import annotations

import copy
import json
import os

MODEL = os.environ.get("FINDWORK_MODEL", "claude-sonnet-4-6")
MOCK_AI = os.environ.get("FINDWORK_MOCK_AI", "1") == "1"

RELATIONS = ["家人", "朋友", "同事"]

# 預設共通天賦（mock 用；對齊原本 6 人彙整的方向）
_DEFAULT_TALENTS = [
    ("傾聽溝通", "communication"),
    ("親和力", "approachability"),
    ("建立關係", "building relationships"),
    ("分析判斷", "analysis"),
    ("給建議", "advising"),
    ("協調", "coordination"),
    ("同理鼓勵", "empathy"),
    ("策略思考", "strategic thinking"),
    ("責任感", "responsibility"),
    ("細心", "attention to detail"),
]


def aggregate_talents(responses: list[dict], weight: int = 2) -> list[dict]:
    """彙整受邀者文字 → 共通天賦關鍵字 [{term, en, weight}]。"""
    texts = [(r.get("text") or "").strip() for r in responses]
    texts = [t for t in texts if t]
    if MOCK_AI or not os.environ.get("ANTHROPIC_API_KEY") or not texts:
        return [{"term": t, "en": e, "weight": weight} for t, e in _DEFAULT_TALENTS[:8]]
    try:
        import anthropic

        client = anthropic.Anthropic()
        joined = "\n\n".join(f"[{r.get('relation', '')}] {r.get('text', '')}" for r in responses)
        prompt = (
            "以下是幾位認識某人的人，描述「你眼中的他」。請彙整出 6–10 個最常被提到的"
            "共通天賦或特質，用繁體中文短語（單詞或短語，不要句子）。只回 JSON 陣列，"
            '例如 ["傾聽溝通","分析判斷"]。\n\n' + joined[:6000]
        )
        msg = client.messages.create(
            model=MODEL, max_tokens=400, messages=[{"role": "user", "content": prompt}]
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        s, e = text.find("["), text.rfind("]")
        arr = json.loads(text[s:e + 1])
        out = [{"term": str(x).strip(), "weight": weight} for x in arr if str(x).strip()][:10]
        return out or [{"term": t, "en": en, "weight": weight} for t, en in _DEFAULT_TALENTS[:8]]
    except Exception as ex:  # noqa: BLE001
        print(f"[method1] AI 失敗，用預設：{ex}")
        return [{"term": t, "en": en, "weight": weight} for t, en in _DEFAULT_TALENTS[:8]]


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
