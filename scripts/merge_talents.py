# /// script
# requires-python = ">=3.10"
# ///
"""把 SKILL.md 對話中的 Claude 整理好的天賦關鍵字合併進 profile。

argv[1]: talents.json 路徑；內容範例：
  [{"term":"傾聽溝通","en":"communication","weight":2}, {"term":"分析判斷","weight":2}, ...]
"""
from __future__ import annotations

import json
import sys

from method1 import merge_into
from profile_io import load_profile, save_profile


def main():
    if len(sys.argv) < 2:
        sys.exit("用法：merge_talents.py <talents.json>")
    with open(sys.argv[1], encoding="utf-8") as f:
        talents = json.load(f)
    new = merge_into(load_profile(), talents)
    path = save_profile(new)
    print(json.dumps({"ok": True, "path": path, "talents": len(new.get("method1_positive", []))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
