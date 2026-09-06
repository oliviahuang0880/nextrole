#!/usr/bin/env python3
"""開職缺看板。只綁 127.0.0.1，只接受白名單欄位的寫回。

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

    def do_GET(self):  # noqa: N802
        if self.path == "/favicon.ico":
            self.send_response(204)
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
        except KeyError:
            return self._json(404, {"error": f"查無職缺 {jid}"})
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        return self._json(200, {"ok": True, "status": rec["status"], "notes": rec["notes"]})

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
    render_board.render(bd.load(), os.path.join(store.OUTPUT, "board.html"), cfg["fit_threshold"])

    os.makedirs(store.OUTPUT, exist_ok=True)
    handler = partial(Handler, directory=store.OUTPUT)
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}/board.html"
    print(f"看板：{url}")
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
