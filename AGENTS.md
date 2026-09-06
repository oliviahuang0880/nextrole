# NextRole — Agent Guide

NextRole is an end-to-end job-hunt tool for the Taiwan market (with APAC / global / remote options): search jobs → score → decide whether to apply → tailor the résumé → prepare interview questions → run a mock interview → track progress. One dataset carries through all of it.

It is packaged as a plugin with six skills, each with its own `SKILL.md`:

| Skill | What it does |
|---|---|
| `skills/setup/` | Create and maintain `~/.nextrole/` |
| `skills/search/` | Dual questionnaire → crawl 104 / Cake / LinkedIn → score |
| `skills/board/` | Job data table, progress tracking, fit scoring, threshold calibration |
| `skills/resume/` | Tailored résumé + cover letter |
| `skills/interview/` | Build the user's material, then per-company interview prep |
| `skills/mock/` | Mock interview and debrief |

The search flow (`skills/search/`) is the original tool and the one to read first.

- All data stays on the user's machine, under `~/.nextrole/`. **This repo is public and must never contain anyone's job-hunt material** — no story banks, no real figures, no spreadsheet IDs, no salary bands. `uv run scripts/selftest.py` audits for exactly that.
- **No API keys are needed.** All AI reasoning (aggregating friends' descriptions, extracting keywords from a pasted JD, running the questionnaire) is done by *you*, the conversing agent.
- Conversation with the user is in Traditional Chinese by default; follow the user's language.

## How to run this repo as an agent

The conversational playbooks are the six `skills/*/SKILL.md` files (written in Traditional Chinese — read them as-is). Start with [`skills/search/SKILL.md`](skills/search/SKILL.md). They were written for Claude Code, so apply these three translation rules:

1. **"對話的 Claude" (the conversing Claude) means you** — whatever agent is running (Codex included). Wherever SKILL.md says Claude should aggregate text, generate keywords, or judge an answer, do it yourself in the conversation. Never call an external AI API for these steps.
2. **Replace `~/.nextrole/bin` with this repo's own `scripts/` directory.** In Claude Code that path is a symlink created by `init_store.py`; outside it, just use `scripts/`:
   ```bash
   cd scripts && uv run run_search.py
   ```
3. **Ignore the skill trigger-phrase machinery** (the YAML frontmatter) and the `/nextrole:*` command names. The user simply saying "help me find a job" / 「幫我找工作」 is your cue to start the search flow from step 1. For the other skills, read the matching `SKILL.md` when the user asks for that thing.

Every `SKILL.md` is deliberately a thin SOP skeleton. The detailed criteria live in that skill's `rules/` and the fixed output formats in its `templates/` — **read them on demand**, at the step that cites them, not all up front. For `skills/search/`:

| File | Read it at |
|---|---|
| `skills/search/rules/環境偵測與降級模式判準.md` | Phase 0 — uv detection, degraded mode |
| `skills/search/rules/技能問卷對話節奏判準.md` | Phase 3 — progress bar, per-question scenarios, option wording |
| `skills/search/rules/提問與選項撰寫判準.md` | Phase 4 — Context + one question + option table + Others |
| `skills/search/rules/中立與加權判準.md` | Phase 4 — neutrality, `field_terms` vs `extra_queries`, negative-term format |
| `skills/search/rules/搜尋結果健檢判準.md` | Phase 5 — what each health-check code means and what to tell the user |
| `skills/search/templates/keywords-report.md` | Phase 3 — the keyword listing |
| `skills/search/templates/search-summary.md` | Phase 5 — the search report |

Each template has a matching `.example.md` showing it filled in.

**Health check:** `run_search.py` ends with a `━━━ 健檢 ━━━` block and a final `健檢代碼：<CODE>,…` line. A zero exit code does **not** mean the result is healthy — read the codes and follow `skills/search/rules/搜尋結果健檢判準.md` before telling the user it worked.

## Quick command reference

```bash
cd scripts
uv run run_search.py                       # crawl → score → ~/.nextrole/output/ + merge into the board
uv run run_search.py --from-cache          # re-score cached jobs (fast; after keyword tweaks)
uv run run_search.py --diff-against auto   # also mark jobs new since the previous run with ✨
uv run merge_talents.py /tmp/talents.json  # merge aggregated talents into the profile
echo '<JSON>' | uv run build_profile.py    # write questionnaire results into the profile
uv run init_store.py                       # create the ~/.nextrole/ skeleton (safe to re-run)
uv run serve.py                            # open the job board at http://127.0.0.1:8765
uv run render_board.py                     # re-render the board without serving it
uv run calibrate.py                        # suggest a fit threshold from real application outcomes
uv run render_resume.py <file.md>          # Markdown résumé → printable A4 page
uv run selftest.py                         # data-flow test + personal-data audit of this repo
```

- Profile: `~/.nextrole/profile.json`; job master file: `~/.nextrole/board.json` (both auto-backed-up before overwrite)
- Reports and board: `~/.nextrole/output/` — **never** open via `file://` (job links break and board edits cannot save):
  ```bash
  uv run serve.py   # → http://127.0.0.1:8765/board.html
  ```
- ⭐ **Re-running a search updates scores only.** `status` / `notes` / `fit` / `artifacts` are the user's judgement and must never be overwritten by the crawler — `board.merge()` enforces this and `selftest.py` pins it.

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

## Principles

- **Neutral scoring**: if the user names no field preference, search and score with neutral skill keywords. Do not steer results by guessing what industry suits them — let the scores speak, let the user decide.
- **Local-only data**: never upload the profile or results anywhere.
- **Nothing personal in this repo.** The plugin ships method, not material. Everything specific to a user lives in `~/.nextrole/` and is created by the user through the tool.
- **Never invent material.** Résumés and interview answers may only use facts the user supplied. If something is missing, ask — do not fill the gap.
- **Ask before writing to Google Sheets.** The user is often editing the same spreadsheet in a browser.
