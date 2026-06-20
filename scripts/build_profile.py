# /// script
# requires-python = ">=3.10"
# ///
"""把技能問卷分類結果寫進 ~/.nextrole/profile.json。

stdin JSON: {"classifications": {<skill_key>: "on_fire|heating|burnout|cold", ...},
             "notes": {<round_category>: "自由補充", ...}}
"""
from __future__ import annotations

import json
import sys

from method2 import build_profile
from profile_io import load_profile, save_profile


def main():
    data = json.load(sys.stdin)
    new = build_profile(
        data["classifications"],
        base=load_profile(),
        notes=data.get("notes", {}),
    )
    path = save_profile(new)
    print(json.dumps({"ok": True, "path": path, "talents": len(new.get("method1_positive", []))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
