# NextRole — Agent Guide

NextRole is a job-hunt profiling tool for the Taiwan market (with APAC / global / remote options). The flow: run a dual questionnaire with the user (talents as seen by friends + a 35-item skill self-assessment), build a personalized keyword profile, then crawl **104 / Cake / LinkedIn**, score every job against the profile, and produce a filterable HTML report.

- All data stays on the user's machine (`~/.nextrole/profile.json`, reports in `./output/`).
- **No API keys are needed.** All AI reasoning (aggregating friends' descriptions, extracting keywords from a pasted JD, running the questionnaire) is done by *you*, the conversing agent.
- Conversation with the user is in Traditional Chinese by default; follow the user's language.

## How to run this repo as an agent

The full conversational playbook is [`SKILL.md`](SKILL.md) (written in Traditional Chinese — read it as-is). It was originally written for Claude Code, so apply these three translation rules:

1. **"對話的 Claude" (the conversing Claude) means you** — whatever agent is running (Codex included). Wherever SKILL.md says Claude should aggregate text, generate keywords, or judge an answer, do it yourself in the conversation. Never call an external AI API for these steps.
2. **Replace the install path** `~/.claude/skills/nextrole/scripts` with this repo's own `scripts/` directory. Example:
   ```bash
   cd scripts && uv run run_search.py
   ```
3. **Ignore the skill trigger-phrase machinery** (the YAML frontmatter). The user simply saying "help me find a job" / 「幫我找工作」 is your cue to start the SKILL.md flow from step 1.

`SKILL.md` is deliberately a thin SOP skeleton. The detailed criteria live in [`rules/`](rules/) and the fixed output formats in [`templates/`](templates/) — **read them on demand**, at the step that cites them, not all up front:

| File | Read it at |
|---|---|
| `rules/環境偵測與降級模式判準.md` | Phase 0 — uv detection, degraded mode |
| `rules/技能問卷對話節奏判準.md` | Phase 3 — progress bar, per-question scenarios, option wording |
| `rules/提問與選項撰寫判準.md` | Phase 4 — Context + one question + option table + Others |
| `rules/中立與加權判準.md` | Phase 4 — neutrality, `field_terms` vs `extra_queries`, negative-term format |
| `rules/搜尋結果健檢判準.md` | Phase 5 — what each health-check code means and what to tell the user |
| `templates/keywords-report.md` | Phase 3 — the keyword listing |
| `templates/search-summary.md` | Phase 5 — the search report |

Each template has a matching `.example.md` showing it filled in.

**Health check:** `run_search.py` ends with a `━━━ 健檢 ━━━` block and a final `健檢代碼：<CODE>,…` line. A zero exit code does **not** mean the result is healthy — read the codes and follow `rules/搜尋結果健檢判準.md` before telling the user it worked.

## Quick command reference

```bash
cd scripts
uv run run_search.py                       # full crawl → score → ./output/results_<ts>.html + .csv
uv run run_search.py --from-cache          # re-score cached jobs (fast; after keyword tweaks)
uv run run_search.py --diff-against auto   # also mark jobs new since the previous run with ✨
uv run merge_talents.py /tmp/talents.json  # merge aggregated talents into the profile
echo '<JSON>' | uv run build_profile.py    # write questionnaire results into the profile
```

- Profile: `~/.nextrole/profile.json` (auto-backed-up before overwrite)
- Reports: `./output/` — tell the user to serve them, **never** open via `file://` (job links break):
  ```bash
  cd output && python3 -m http.server 8765   # → http://localhost:8765/results_<ts>.html
  ```

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — the only dependency; scripts declare their own Python deps inline (PEP 723).
- **No API keys, no `.env` file.** Nothing in this repo reads a `.env`, and there are no secrets to store.

## Optional: proxy (when a job board blocks the crawler)

If 104 / Cake / LinkedIn start returning errors or empty results (rate-limiting or IP blocks), the crawler can be routed through an HTTP proxy via environment variables — set them in the shell before running, no config file involved:

```bash
export PROXY_URL=http://user:pass@host:port        # sets both http and https
# or override per-scheme:
export PROXY_URL_HTTP=http://host:port
export PROXY_URL_HTTPS=http://host:port
```

Unset (the default) means a direct connection. Handled in [`scripts/http_client.py`](scripts/http_client.py).

## Principles (same as SKILL.md)

- **Neutral scoring**: if the user names no field preference, search and score with neutral skill keywords. Do not steer results by guessing what industry suits them — let the scores speak, let the user decide.
- **Local-only data**: never upload the profile or results anywhere.
