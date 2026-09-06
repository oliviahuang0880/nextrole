#!/bin/bash
# 每天自動重跑一次搜尋，把新職缺標 ✨ 併進看板。
#
# 安裝（讓 launchd 每天叫它）：
#   ln -sf ~/.nextrole/bin/daily_run.sh ~/.nextrole/daily_run.sh
#   launchctl unload ~/Library/LaunchAgents/com.olivia.nextrole.daily.plist 2>/dev/null
#   launchctl load  ~/Library/LaunchAgents/com.olivia.nextrole.daily.plist
#
# 停用：
#   launchctl unload ~/Library/LaunchAgents/com.olivia.nextrole.daily.plist
set -euo pipefail

BIN="${HOME}/.nextrole/bin"
LOG_DIR="${HOME}/.nextrole/daily"
mkdir -p "$LOG_DIR"

# launchd 的 PATH 很乾淨，uv 通常不在裡面
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

if ! command -v uv >/dev/null 2>&1; then
  echo "[$(date '+%F %T')] 找不到 uv，跳過。裝好 uv 或把它的路徑加進這支腳本的 PATH。" >&2
  exit 1
fi

if [ ! -d "$BIN" ]; then
  echo "[$(date '+%F %T')] 找不到 $BIN。先跑一次 init_store.py。" >&2
  exit 1
fi

cd "$BIN"
echo "[$(date '+%F %T')] 開始每日搜尋"
# --diff-against auto：跟上一份結果比對，本次新出現的職缺標 ✨
uv run run_search.py --diff-against auto
echo "[$(date '+%F %T')] 完成。開看板：cd ~/.nextrole/bin && uv run serve.py"
