"""方法二（技能評估）問卷引擎。

流程：AI 用情境題分批問 → 把 ~35 個技能分類成 On Fire / Heating Up / Burnout /
Cold → 用 build_profile() 產出可直接餵給 score.py 的 keywords.json。

開發期省 token：環境變數 FINDWORK_MOCK_AI（預設 "1"=開）時走腳本式假問答，
不呼叫 Claude；上線前設 FINDWORK_MOCK_AI=0 並提供 ANTHROPIC_API_KEY 才走真 AI。
"""
from __future__ import annotations

import json
import os

MODEL = os.environ.get("FINDWORK_MODEL", "claude-sonnet-4-6")
MOCK_AI = os.environ.get("FINDWORK_MOCK_AI", "1") == "1"

# ── 35 個技能（取自 profile/method2_skills_checklist.md）──
# cat：A 分析 / B 管理 / C 人際 / D 創意
# search：是否適合當「職缺搜尋關鍵字」（過於通用的詞不拿去搜，避免噪音）
# hard_cold：屬「硬性不適合」，若 Cold 且出現在職稱→整筆排除
def _s(key, zh, en, cat, search=False, hard_cold=False):
    return {"key": key, "zh": zh, "en": en, "cat": cat, "search": search, "hard_cold": hard_cold}


SKILLS = [
    # A 分析
    _s("research", "研究", "research", "A", search=True),
    _s("analyze", "分析", "analyze", "A", search=True),
    _s("data_mgmt", "資料管理與計算", "data management", "A", hard_cold=True),
    _s("metrics", "建立指標", "establish metrics", "A", search=True),
    _s("budget", "預算", "budget", "A", hard_cold=True),
    _s("forecast", "預測", "forecast", "A"),
    # B 管理
    _s("lead", "領導", "lead", "B"),
    _s("manage_people", "管理人員", "manage people", "B"),
    _s("manage_projects", "專案管理", "project management", "B", search=True),
    _s("planning", "規劃", "planning", "B", search=True),
    _s("envision", "擘劃願景", "envision", "B"),
    _s("decisions", "做決策", "make decisions", "B"),
    _s("initiate", "主動發起", "initiate", "B"),
    _s("process_improve", "流程改善", "process improvement", "B", search=True),
    _s("problem_solving", "解決問題", "problem solving", "B", search=True),
    # C 人際
    _s("teach", "教學", "teach", "C", search=True),
    _s("coach", "教練", "coach", "C"),
    _s("counsel", "諮商", "counsel", "C"),
    _s("consult", "顧問", "consult", "C", search=True),
    _s("stakeholder", "利害關係人管理", "stakeholder management", "C"),
    _s("facilitate", "引導團體", "facilitate groups", "C"),
    _s("resolve_conflict", "化解衝突", "resolve conflict", "C"),
    _s("negotiation", "談判", "negotiation", "C", search=True),
    _s("collaborate", "協作", "collaborate", "C"),
    _s("customer_service", "客戶服務", "customer service", "C", search=True),
    _s("relationships", "建立關係", "building relationships", "C"),
    _s("connecting", "牽線連結", "connecting people", "C"),
    # D 創意
    _s("design", "設計", "design", "D", search=True),
    _s("create_images", "影像創作", "create images", "D", hard_cold=True),
    _s("draft", "草圖", "draft", "D"),
    _s("perform", "表演", "perform", "D", hard_cold=True),
    _s("ideation", "發想", "ideation", "D"),
    _s("make_connections", "連結概念", "make connections", "D"),
    _s("write_creative", "創意寫作", "creative writing", "D", hard_cold=True),
    _s("storytelling", "說故事", "storytelling", "D", search=True),
]
SKILL_BY_KEY = {s["key"]: s for s in SKILLS}
VALID_CATS = {"on_fire", "heating", "burnout", "cold"}

# 通用負向（與問卷無關的求職衛生；對齊 profile/keywords.json 規則）
BASE_NEGATIVE = [
    {"term": "電話銷售", "en": "telesales", "exclude": True},
    {"term": "實習", "en": "intern", "exclude_if_title": True},
    {"term": "兼職", "en": "part-time", "exclude_if_title": True},
    {"term": "工讀", "exclude_if_title": True},
    {"term": "系統架構", "en": "system architect", "exclude_if_title": True, "penalty": 30},
    {"term": "都市", "en": "urban planning", "exclude_if_title": True, "penalty": 30},
    {"term": "土木", "exclude_if_title": True, "penalty": 30},
    {"term": "韌體", "en": "firmware", "penalty": 20},
]


# ───────────────────────── 問卷：按面向分組、逐技能歸類 ─────────────────────────
# 每個技能一句話說明，幫使用者準確判斷
DESC = {
    "research": "調查與研究資料、建立事實、得出結論",
    "analyze": "分析資料/想法之間的關係、找出洞察",
    "data_mgmt": "收集與清理大量資料、計算",
    "metrics": "設定衡量成效的指標",
    "budget": "編列與管理預算（偏財務）",
    "forecast": "做趨勢或數字的預測",
    "lead": "激勵他人認同想法、朝願景前進",
    "manage_people": "支持員工朝目標前進",
    "manage_projects": "設定目標時程、追進度把專案完成",
    "planning": "做計畫安排、排優先順序",
    "envision": "提出構想或大方向目標",
    "decisions": "權衡選項、自主做決定",
    "initiate": "少監督下主動發起行動",
    "process_improve": "改良想法、概念或流程",
    "problem_solving": "拆解並解決問題",
    "teach": "指導或訓練他人理解內容",
    "coach": "協助他人改善表現、達成目標",
    "counsel": "支持他人面對個人/心理問題",
    "consult": "評估需求、提供專業建議",
    "stakeholder": "管理各方利害關係人",
    "facilitate": "帶領團體討論與活動",
    "resolve_conflict": "協助各方化解衝突、達成共識",
    "negotiation": "進行協商與談判",
    "collaborate": "與他人共同創造或策劃",
    "customer_service": "提供客戶服務",
    "relationships": "建立人際關係",
    "connecting": "把人與人牽線連結起來",
    "design": "設計專案、計畫或產品",
    "create_images": "攝影、平面設計、繪畫等視覺創作",
    "draft": "速寫/繪圖以傳達概念",
    "perform": "演戲、唱歌、跳舞、演奏",
    "ideation": "產生新概念或點子",
    "make_connections": "連結不相干的想法或概念",
    "write_creative": "寫故事、詩、文案等",
    "storytelling": "用故事來溝通",
}

# 按面向分組（每組 4–8 個技能），每組用一段情境帶入，再逐技能歸到四類
ROUNDS = [
    ("分析類",
     "想像你接到一個還沒人搞懂的專案，手上只有一堆零散資料和模糊的方向。面對「把事情查清楚、"
     "找出答案」這件事，下面這些能力，哪些你很想做、哪些一看到就累？",
     ["research", "analyze", "metrics", "forecast", "data_mgmt", "budget"]),
    ("管理類（一）",
     "假設你被指派帶一個小團隊，要把一個目標一路推到完成。從定方向、帶人、到把專案管到底，"
     "下面這些角色，你各自的真實感受是？",
     ["lead", "manage_people", "manage_projects", "planning", "envision"]),
    ("管理類（二）",
     "工作中常需要你自己判斷、主動推進、把事情變更好。遇到要拍板決定、要起頭發起、要改善流程或"
     "拆解難題時，哪些讓你有衝勁、哪些讓你卻步？",
     ["decisions", "initiate", "process_improve", "problem_solving"]),
    ("人際類（一）",
     "想像同事或客戶來找你，需要被指導、被支持，或要你給專業建議。在這些「幫助與引導他人」的"
     "情境裡，下面每件事你的真實感受是？",
     ["teach", "coach", "counsel", "consult", "stakeholder", "facilitate"]),
    ("人際類（二）",
     "團隊與客戶之間難免有摩擦、要協調、還要長期經營關係。在這些「協作與處理關係」的情境裡，"
     "哪些你做得開心、哪些會讓你耗電？",
     ["resolve_conflict", "negotiation", "collaborate", "customer_service", "relationships", "connecting"]),
    ("創意類",
     "最後輪到「創造與表達」。從想點子、做設計、到把概念說出來，每個人擅長和喜歡的環節都不同。"
     "下面這些，哪些是你的菜、哪些不是？",
     ["design", "create_images", "draft", "perform", "ideation", "make_connections", "write_creative", "storytelling"]),
]

FACETS = [
    {"v": "on_fire", "label": "我很拿手，而且每天都想做",
     "hint": "一做就有勁、會忘記時間；別人也常找我做這個。"},
    {"v": "heating", "label": "還不夠熟，但很想多做、想變強",
     "hint": "目前做得還不夠好，但很有興趣，願意多花時間累積經驗。"},
    {"v": "burnout", "label": "做得來，但做久了會累",
     "hint": "能勝任、別人覺得我行，可是常做會心累、不想每天都碰。"},
    {"v": "cold", "label": "不太拿手，也提不起勁",
     "hint": "既不擅長、也沒什麼興趣，能不做就不做。"},
]


def next_turn(answered: dict | None = None) -> dict:
    """回傳下一個待分類的面向組；全部分完則回 result。已分類的用 answered 帶上來。"""
    ans = {k: v for k, v in (answered or {}).items() if k in SKILL_BY_KEY and v in VALID_CATS}
    for i, (cat, scenario, keys) in enumerate(ROUNDS):
        if not all(k in ans for k in keys):
            return {
                "type": "classify", "category": cat, "scenario": scenario,
                "round": i + 1, "total": len(ROUNDS), "facets": FACETS,
                "skills": [{"key": k, "zh": SKILL_BY_KEY[k]["zh"], "desc": DESC.get(k, "")} for k in keys],
            }
    return {"type": "result", "classifications": _sanitize(ans)}


def _sanitize(cls: dict) -> dict:
    out = {}
    for k, v in (cls or {}).items():
        if k in SKILL_BY_KEY and v in VALID_CATS:
            out[k] = v
    for s in SKILLS:  # 缺漏的補 cold（保守）
        out.setdefault(s["key"], "cold")
    return out


# ───────────────────────── 產出 profile ─────────────────────────
def build_profile(classifications: dict, *, base: dict | None = None, notes: dict | None = None) -> dict:
    """把分類結果轉成 keywords.json（可直接給 score.py）。notes：各組的自由補充，存進 _meta。"""
    cls = _sanitize(classifications)
    positive, negative, q_count = [], list(BASE_NEGATIVE), 0
    total_w = 0
    for s in SKILLS:
        c = cls[s["key"]]
        if c == "on_fire" or c == "heating":
            w = 3 if c == "on_fire" else 2
            q = bool(s["search"]) and q_count < 10  # 限制搜尋詞數，避免噪音
            if q:
                q_count += 1
            positive.append({"term": s["zh"], "en": s["en"], "weight": w, "q": q})
            total_w += w
        elif c == "burnout":
            negative.append({"term": s["zh"], "en": s["en"], "penalty": 20})
        else:  # cold
            entry = {"term": s["zh"], "en": s["en"], "penalty": 30}
            if s["hard_cold"]:
                entry["exclude_if_title"] = True
            negative.append(entry)

    method1 = list((base or {}).get("method1_positive", []))  # 方法一（階段三）；現在通常為空
    has_m1 = bool(method1)
    method2_full = max(10, round(0.4 * total_w))

    clean_notes = {k: v for k, v in (notes or {}).items() if isinstance(v, str) and v.strip()}
    return {
        "_meta": {"source": "method2_questionnaire", "notes": clean_notes},
        "candidate_titles": [],
        "method2_positive": positive,
        "method1_positive": method1,
        "field_terms": list((base or {}).get("field_terms", [])),
        "negative": negative,
        "scoring": {
            "blend_method2": 1.0 if not has_m1 else 0.6,
            "blend_method1": 0.0 if not has_m1 else 0.4,
            "method2_full": method2_full,
            "method1_full": 12,
            "threshold": 60,
            "title_boost": 2.0,
            "use_field_terms": False,
        },
        "filters": {"allowed_cities": ["台北", "新北"], "allow_remote": True},
    }


def summarize(classifications: dict) -> dict:
    """給前端顯示：四類各有哪些技能（中文）。"""
    cls = _sanitize(classifications)
    buckets = {"on_fire": [], "heating": [], "burnout": [], "cold": []}
    for s in SKILLS:
        buckets[cls[s["key"]]].append(s["zh"])
    return buckets
