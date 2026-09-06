"""~/.nextrole/ 本機資料層。所有個人素材只存在這裡，永遠不進 repo。

沿用 profile_io 的習慣：寫之前先備份成 <name>.<UTC ts>.<ext>。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time

ROOT = os.path.expanduser("~/.nextrole")

CONFIG = os.path.join(ROOT, "config.json")
BOARD = os.path.join(ROOT, "board.json")
BIN = os.path.join(ROOT, "bin")
KIT = os.path.join(ROOT, "kit")
RESUMES = os.path.join(ROOT, "resumes")
INTERVIEWS = os.path.join(ROOT, "interviews")
OUTPUT = os.path.join(ROOT, "output")

DIRS = [ROOT, KIT, RESUMES, INTERVIEWS, OUTPUT]

DEFAULT_CONFIG = {
    "version": 1,
    "google_email": None,
    "spreadsheet_id": None,
    "fit_threshold": 7,
    "hard_blockers": [],
    "resume_versions": [],
    "cover_letter_max_chars": 300,
}


def job_id(url: str) -> str:
    return hashlib.sha1((url or "").encode("utf-8")).hexdigest()[:10]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ensure_dirs():
    for d in DIRS:
        os.makedirs(d, exist_ok=True)


def _backup(path: str):
    if os.path.exists(path):
        base, ext = os.path.splitext(path)
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        shutil.copy2(path, f"{base}.{ts}{ext}")


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data, backup: bool = True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if backup:
        _backup(path)
    # 暫存檔名要唯一：serve.py 是多執行緒的，兩個請求共用 ".tmp" 會互相搶
    tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path


def load_config() -> dict:
    cfg = read_json(CONFIG)
    if cfg is None:
        return dict(DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    return merged


def save_config(cfg: dict):
    return write_json(CONFIG, cfg)


def job_dir(kind: str, jid: str) -> str:
    d = os.path.join({"resume": RESUMES, "interview": INTERVIEWS}[kind], jid)
    os.makedirs(d, exist_ok=True)
    return d


def rel(path: str) -> str:
    """回報用的相對路徑，避免把使用者的家目錄印出來。"""
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path
