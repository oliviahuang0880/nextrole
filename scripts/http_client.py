"""共享 HTTP 連線層 —— 所有對外抓取（104/Cake/LinkedIn）都走這裡。

集中兩件事：
1. **代理插座**：若設了環境變數 ``PROXY_URL``（如 ``http://user:pass@host:port``），
   所有請求自動走該代理；沒設就直連、零影響、零成本。等之後要公開、或被 IP
   封鎖時，只要設這個環境變數即可生效，不必改任何爬蟲程式。
   也可用 ``PROXY_URL_HTTP`` / ``PROXY_URL_HTTPS`` 分別指定。
2. **共享 Session**：重用 TCP 連線、統一預設標頭，順手做 429/5xx 退避重試。

各爬蟲原本的 ``requests.get(...)`` 改成 ``http_client.get(...)`` 即可。
"""
from __future__ import annotations

import os
import time

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def _build_proxies() -> dict | None:
    """從環境變數組出 requests 用的 proxies dict；沒設回 None（直連）。"""
    both = os.environ.get("PROXY_URL")
    http_p = os.environ.get("PROXY_URL_HTTP") or both
    https_p = os.environ.get("PROXY_URL_HTTPS") or both
    proxies = {}
    if http_p:
        proxies["http"] = http_p
    if https_p:
        proxies["https"] = https_p
    return proxies or None


_session: requests.Session | None = None


def get_session() -> requests.Session:
    """取得（並快取）共享 Session，已套用預設標頭與代理設定。"""
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(DEFAULT_HEADERS)
        proxies = _build_proxies()
        if proxies:
            s.proxies.update(proxies)
            print(f"[http] 已啟用代理：{list(proxies.keys())}")
        _session = s
    return _session


def using_proxy() -> bool:
    return _build_proxies() is not None


def get(
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: int = 20,
    retries: int = 4,
    backoff_statuses: tuple[int, ...] = (429, 502, 503, 504),
) -> requests.Response:
    """走共享 Session 的 GET，對 429/5xx 做退避重試。

    ``headers`` 會疊加在預設標頭之上（例如 104 需要的 Referer）。
    最後一次仍失敗則 raise_for_status()，由呼叫端決定如何處理。
    """
    session = get_session()
    last: requests.Response | None = None
    for attempt in range(retries):
        resp = session.get(url, params=params, headers=headers, timeout=timeout)
        if resp.status_code in backoff_statuses:
            last = resp
            # 429 退避久一點；5xx 退避短一點
            wait = (5 if resp.status_code == 429 else 1.5) * (attempt + 1)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp
    if last is not None:
        last.raise_for_status()
    return resp  # type: ignore[return-value]
