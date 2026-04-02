# Project Guidance: sbx-quickstart

## What This Repo Is

A hands-on guide for new users of Docker Sandboxes (`sbx`), using **DevBoard** — a full-stack Next.js + FastAPI issue tracker — as the exercise app. The guide lives in `README.md` on the `guide-update` branch. The old guide (`docker-sandboxes-guide.md`) has been deleted; all content now lives in `README.md`.

## Reference Documentation

Official Docker Sandboxes docs: **https://docs.docker.com/ai/sandboxes/**

Key sub-pages:
- Get started / usage
- Agents (claude-code, codex, copilot, gemini, docker-agent, kiro, opencode, custom-environments)
- Architecture, security, credentials
- Troubleshooting / FAQ

## Current Task

Audit and improve `README.md` for:
1. Technical accuracy against current docs
2. Complete feature coverage
3. Good flow (no abrupt topic jumps, no unnecessary context switches)
4. No duplicated concepts

**Do not make changes until the user instructs you to fix specific issues.**

---

## Known Issues in README.md

### TECHNICAL ACCURACY

**Issue 1 — `sbx create` missing workspace path (§5, Appendix B)**
Guide uses `sbx create --name=quickstart claude` but docs require an explicit workspace argument: `sbx create --name=quickstart claude .` (the `.` for current directory). Same problem in Appendix B quick reference.

**Issue 2 — Wrong worktree path text (§9, line ~415)**
Guide says worktrees go under `.sbx/sandbox-worktrees` but correct path is `.sbx/<sandbox-name>-worktrees/<branch>`. For the `quickstart` sandbox that's `.sbx/quickstart-worktrees/`. The parallel agents section later (line ~483) gets it right; the single-branch section doesn't.

**Issue 3 — Spurious `git add`/`git commit` in PR workflow (§9)**
After branch mode, Claude already committed. But the review/PR block shows:
```bash
git add .
git commit -m "fixing bugs"
git push origin fix-bugs
```
The `git add` and `git commit` would run in the *main* working tree (wrong branch), not the worktree. Should be removed — just diff, push, and PR.

**Issue 4 — `sbx policy deny` command may not exist (§12, Appendix B)**
Guide shows `sbx policy deny network ads.example.com` but the docs only document `sbx policy allow`. No `deny` subcommand appears in the docs. Needs verification; if it doesn't exist, remove it.

**Issue 5 — `sbx policy log <sandbox-name>` may not support filtering (Appendix B)**
Appendix B shows `sbx policy log quickstart` to filter by sandbox, but docs only show `sbx policy log` with no arguments. Needs verification.

**Issue 6 — `sbx policy set-default balanced` not confirmed in docs (Appendix B)**
Listed in Appendix B quick reference but not found in current docs. May not exist; `sbx policy reset` is the documented way to change default policy.

**Issue 7 — Secrets table missing three services (§4)**
Table lists: `anthropic`, `openai`, `github`, `google`, `groq`, `aws`.
Docs also include: `mistral`, `nebius`, `xai` — all missing from the guide.

### FLOW / DUPLICATION

**Issue 8 — Same bugs fixed twice (§8 and §9)** ← user-identified
Section 8 (direct mode) has Claude fix the pagination bug and `updated_at` bug.
Section 9 (branch mode) tells Claude to fix "the pagination bug in backend/app/routers/issues.py and the updated_at bug in backend/app/models.py" — the exact same bugs.
Branch mode needs a different task (e.g., the search or notifications feature, or a different bug).

**Issue 9 — New sandbox created in §13 with no explanation** ← user-identified
Section 13 (Multiple workspaces) suddenly creates `--name=devboard-full` when the entire guide has used `quickstart`. No explanation of why a new sandbox is needed (it isn't — multiple workspaces work with existing sandboxes). Should either reuse `quickstart` or explain the intentional choice.

### MISSING FEATURES

**Issue 10 — Custom templates not covered** ← user-identified
Guide only uses `--template` for the Windows Docker variant. Custom templates (building a Dockerfile FROM a sandbox template, pushing it, referencing with `--template`) are a key power feature and aren't mentioned. At minimum, add a callout pointing to docs.

**Issue 11 — `--branch auto` not mentioned (§9)**
Docs show `sbx run claude --branch auto` to auto-generate a branch name. A small addition but useful to mention alongside named branches.

**Issue 12 — Host service access not mentioned**
Docs document `host.docker.internal` as the hostname for reaching host services from inside a sandbox (e.g., a local Ollama instance). Not mentioned anywhere in the guide.

**Issue 13 — Clock drift troubleshooting missing (Appendix C)**
Laptop sleep/wake causes VM clock drift. Fix: `sbx stop <name> && sbx run <name>`. Called out explicitly in the official docs troubleshooting section; not in the guide.

**Issue 14 — Agent config not inherited — not mentioned**
`~/.claude`, `~/.codex`, etc. from the host are NOT available inside the sandbox. Only project-level config in the workspace directory is picked up. This is a common gotcha that's not mentioned anywhere.

**Issue 15 — `.sbx/` not recommended for .gitignore**
Docs recommend adding `.sbx/` to `.gitignore` since that's where worktrees are stored. Not mentioned in §9 or elsewhere.

**Issue 16 — Other agent types not acknowledged**
The guide is Claude-only (appropriate for scope) but never acknowledges that `sbx` supports other agents (codex, copilot, gemini, kiro, opencode, shell). A single sentence noting this would help orient users.

### POLISH / MINOR

**Issue 17 — "[output placeholder]" left in §12** ← OWNER WILL FIX MANUALLY, DO NOT TOUCH
`sbx policy log` section contains the literal text `[output placeholder]` — owner needs to supply real example output.

**Issue 18 — Inconsistent framing of prompts**
Some sections say "Give Claude this prompt:" and others say "Issue the following command" for prompts given interactively inside the Claude session. Should use consistent framing throughout.

---

## DevBoard App Structure (for reference)

- `backend/` — FastAPI + SQLAlchemy + Postgres, JWT auth, pytest tests
- `frontend/` — Next.js
- `docker-compose.yml` — ties backend + Postgres + frontend together
- `prompts/` — pre-written prompt files for parallel agent exercises
  - `prompts/implement-search.txt`
  - `prompts/implement-notifications.txt`

### Intentional bugs in DevBoard (used by guide)

- Pagination off-by-one in `backend/app/routers/issues.py`
- Missing `onupdate=` on `updated_at` field in `backend/app/models.py`
- `GET /issues/search?q=` returns 501 (unimplemented)
- `send_status_change_notification()` is a no-op stub

---

## Key sbx CLI Facts (from docs, for verification)

- `sbx create` requires explicit workspace path: `sbx create --name=foo claude .`
- `sbx run` infers current dir: `sbx run claude` or reconnect with `sbx run <sandbox-name>`
- Worktrees stored at `.sbx/<sandbox-name>-worktrees/<branch>/`
- Multiple workspaces: first path = primary (rw), extras append `:ro` for read-only
- `sbx policy deny` — confirmed valid (allow, deny, log, ls, reset, rm, set-default all confirmed via `sbx policy --help`)
- Global secrets inject at creation time; sandbox-scoped secrets inject immediately
- Services must bind to `0.0.0.0` (not `127.0.0.1`) for port forwarding to work
- `host.docker.internal` to reach host services from inside sandbox
- `SBX_NO_TELEMETRY=1` to disable telemetry
