#!/usr/bin/env python3
"""開職缺看板（三頁）。只綁 127.0.0.1，只接受白名單欄位的寫回。

用法：uv run serve.py [--port 8765] [--no-open]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as bd  # noqa: E402
import render_board  # noqa: E402
import store  # noqa: E402

MAX_BODY = 64 * 1024


class Handler(SimpleHTTPRequestHandler):
    def _json(self, code: int, payload: dict):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def end_headers(self):
        # 三頁是靜態檔，但每次寫回都會重新產生。不擋快取的話，
        # 使用者在收件匣按了儲存、切到分析頁會看到舊的那一份。
        if self.path.endswith(".html") or self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def do_GET(self):  # noqa: N802
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if self.path in ("/", "/index.html", "/board.html"):
            self.send_response(302)
            self.send_header("Location", "/inbox.html")
            self.end_headers()
            return
        return super().do_GET()

    def do_PATCH(self):  # noqa: N802
        if not self.path.startswith("/api/job/"):
            return self._json(404, {"error": "not found"})
        jid = self.path[len("/api/job/"):].strip("/")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_BODY:
                raise ValueError("body 長度不合法")
            fields = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(fields, dict):
                raise ValueError("body 必須是物件")
            rec = bd.patch(jid, fields)
            # 改動會影響其他兩頁的計數與內容，直接全部重畫
            render_board.render_all(bd.load(), store.load_config())
        except KeyError:
            return self._json(404, {"error": f"查無職缺 {jid}"})
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        return self._json(200, {"ok": True, "status": rec.get("status"),
                                "seen": rec.get("seen"), "saved": rec.get("saved"),
                                "notes": rec.get("notes", "")})

    def log_message(self, fmt, *args):
        # log_error 會傳 HTTPStatus 進來，不能直接當字串用
        first = str(args[0]) if args else ""
        if "/api/" in first or "error" in fmt.lower():
            super().log_message(fmt, *args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    cfg = store.load_config()
    render_board.render_all(bd.load(), cfg)

    os.makedirs(store.OUTPUT, exist_ok=True)
    handler = partial(Handler, directory=store.OUTPUT)

    # 連 port 被佔用都要好好講。往後找 10 個，找不到再放棄。
    httpd = None
    port = args.port
    for port in range(args.port, args.port + 10):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError as exc:
            if exc.errno not in (48, 98):        # EADDRINUSE
                raise
            print(f"  port {port} 被佔用了，換一個…")
    if httpd is None:
        print(f"❌ {args.port}–{args.port + 9} 都被佔用。用 --port 指定一個空的。")
        raise SystemExit(1)
    if port != args.port:
        print(f"  （原本要用 {args.port}）")
    url = f"http://127.0.0.1:{port}/inbox.html"
    print(f"看板：{url}")
    print("  ① 收件匣 /inbox.html　② 分析 /analysis.html　③ 投遞追蹤 /tracker.html")
    print(f"  資料來源：{store.ROOT}")
    print("Ctrl-C 結束。")
    if not args.no_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
