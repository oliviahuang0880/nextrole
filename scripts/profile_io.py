"""讀寫 ~/.nextrole/profile.json。寫之前自動備份舊檔成 profile.<UTC ts>.json。"""
from __future__ import annotations

import json
import os
import shutil
import time

ROOT = os.path.expanduser("~/.nextrole")
PATH = os.path.join(ROOT, "profile.json")


def load_profile():
    if not os.path.exists(PATH):
        return None
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def save_profile(p):
    os.makedirs(ROOT, exist_ok=True)
    if os.path.exists(PATH):
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        shutil.copy2(PATH, os.path.join(ROOT, f"profile.{ts}.json"))
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)
    return PATH
