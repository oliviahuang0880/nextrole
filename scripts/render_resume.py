#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown"]
# ///
"""把 Markdown 履歷／求職信轉成可列印的 A4 網頁。

在瀏覽器按 Cmd+P 就能存成 PDF，邊界與分頁都設好了。

uv run render_resume.py <input.md> [-o output.html] [--title "履歷"]
"""
from __future__ import annotations

import argparse
import os
import sys

import markdown

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CSS = """
:root{ --ink:#1a1a1a; --muted:#5b6470; --rule:#d8dde3; --accent:#0b66c2; }
*{box-sizing:border-box}
body{font-family:-apple-system,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;
     color:var(--ink);margin:0;background:#f2f4f7;line-height:1.65;font-size:14px}
.page{background:#fff;width:210mm;min-height:297mm;margin:16px auto;padding:16mm 18mm;
      box-shadow:0 1px 4px rgba(0,0,0,.12)}
h1{font-size:26px;margin:0 0 2px;letter-spacing:.5px}
h1+p{color:var(--muted);margin:0 0 18px;font-size:13px}
h2{font-size:15px;margin:22px 0 8px;padding-bottom:4px;border-bottom:2px solid var(--rule);
   letter-spacing:.5px}
h3{font-size:14px;margin:14px 0 2px}
h3+p{color:var(--muted);font-size:12.5px;margin:0 0 6px}
ul{margin:6px 0;padding-left:1.15em} li{margin:3px 0}
p{margin:6px 0}
a{color:var(--accent);text-decoration:none}
strong{font-weight:650}
hr{border:0;border-top:1px solid var(--rule);margin:18px 0}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}
th,td{border:1px solid var(--rule);padding:5px 8px;text-align:left}
th{background:#f6f8fa}
blockquote{margin:8px 0;padding:6px 12px;border-left:3px solid var(--rule);color:var(--muted)}
code{background:#f2f4f7;padding:1px 4px;border-radius:3px;font-size:.92em}

@media print{
  body{background:#fff}
  .page{width:auto;min-height:0;margin:0;padding:0;box-shadow:none}
  h2{break-after:avoid-page} h3{break-after:avoid-page}
  li,h3+p{break-inside:avoid}
  a{color:var(--ink);text-decoration:none}
}
@page{ size:A4; margin:16mm 16mm; }
"""


def render(md_path: str, out_path: str, title: str | None = None) -> str:
    with open(md_path, encoding="utf-8") as f:
        src = f.read()

    body = markdown.markdown(
        src, extensions=["tables", "sane_lists", "nl2br"], output_format="html5"
    )
    if not title:
        first = next((ln for ln in src.splitlines() if ln.startswith("# ")), "")
        title = first[2:].strip() or os.path.splitext(os.path.basename(md_path))[0]

    doc = (
        '<!doctype html>\n<html lang="zh-TW"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title>\n<style>{CSS}</style></head>\n"
        f'<body><main class="page">\n{body}\n</main></body></html>'
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Markdown 檔")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    out = args.output or os.path.splitext(args.input)[0] + ".html"
    path = render(args.input, out, args.title)
    print(f"已產生 {path}")
    print("在瀏覽器開啟後按 Cmd+P → 另存為 PDF，A4 邊界與分頁已設好。")


if __name__ == "__main__":
    main()
