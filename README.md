# Docker Sandboxes: A Hands-On Guide with Claude

> **Status**: This guide covers Docker Sandboxes as of its experimental launch.
> All commands use the `sbx` CLI.

---

## What you'll learn

By the end of this guide you'll be able to:

- Install and configure the `sbx` CLI on macOS or Windows
- Run Claude Code autonomously inside an isolated microVM sandbox
- Use branch mode to let Claude work on its own Git branch without touching your working tree
- Forward live ports from a sandbox to your browser
- Manage network policies so Claude can only reach what you allow
- Mount multiple workspaces and run multi-agent workflows
- Handle credentials securely without passing raw API keys into the sandbox

The guide uses **DevBoard** — a full-stack Next.js + FastAPI issue tracker included
alongside this file (`backend/`, `frontend/`, `docker-compose.yml`). DevBoard has
real-world complexity: a REST API, a Postgres database, JWT auth, tests, and a handful
of intentional bugs and unfinished features that make ideal exercises for Claude.

---

## Table of contents

1. [How Docker Sandboxes work](#1-how-docker-sandboxes-work)
2. [Fork and clone this repo](#2-fork-and-clone-this-repo)
3. [Installation](#3-installation)
4. [Authentication](#4-authentication)
5. [Orient yourself: first sandbox run](#5-orient-yourself-first-sandbox-run)
6. [The interactive TUI dashboard](#6-the-interactive-tui-dashboard)
7. [Branch mode: safe parallel development](#7-branch-mode-safe-parallel-development)
8. [Exercise: run the test suite](#8-exercise-run-the-test-suite)
9. [Exercise: bug hunt (pagination + updated_at)](#9-exercise-bug-hunt)
10. [Docker Compose inside the sandbox](#10-docker-compose-inside-the-sandbox)
11. [Port forwarding with `sbx ports`](#11-port-forwarding-with-sbx-ports)
12. [Exercise: implement issue search](#12-exercise-implement-issue-search)
13. [Network policies](#13-network-policies)
14. [Multiple workspaces](#14-multiple-workspaces)
15. [Debugging with `sbx exec`](#15-debugging-with-sbx-exec)
16. [Production patterns](#16-production-patterns)
17. [Appendix A: prompt library](#appendix-a-prompt-library)
18. [Appendix B: CLI quick reference](#appendix-b-cli-quick-reference)
19. [Appendix C: troubleshooting](#appendix-c-troubleshooting)

---

## 1. How Docker Sandboxes work

When you run `sbx run claude`, Docker Sandboxes:

1. Spins up a **lightweight microVM** — its own Linux kernel, not just a container namespace.
2. Gives the VM a **private Docker daemon**, so Claude can run `docker build` or `docker compose up` without touching your host Docker.
3. **Mounts your workspace directory** at its exact host path inside the VM. File changes are instant in both directions — no copy-on-write delay.
4. Routes all HTTP/HTTPS traffic from the VM through a **host-side proxy** that enforces your network policy and injects API credentials. Claude never sees raw API keys.
5. Starts Claude Code with `--dangerously-skip-permissions` so it can act autonomously without prompting you on every file change.

The result: Claude can build images, install packages, run tests, and edit your code —
and none of that can escape the VM to touch your host system, your other containers,
or any network destination you haven't explicitly allowed.

```
Your machine
├── Host Docker daemon    ← your stuff, untouched
├── Host filesystem       ← workspace dir shared (read/write); nothing else
│
└── Sandbox (microVM)
    ├── Private Docker daemon  ← Claude builds here
    ├── /your/workspace        ← live-mounted from host
    └── Outbound HTTP proxy    ← enforces network policy, injects creds
```

---

## 2. Fork and clone this repo

Before diving into the exercises, fork this repo to your GitHub account so you can push branches and open pull requests as you work through the guide.

**Step 1** — Fork on GitHub by clicking the **Fork** button at the top of the repo page.

**Step 2** — Clone your fork to your local machine:

```bash
git clone https://github.com/<your-username>/sbx-quickstart.git ~/sbx-quickstart
cd ~/sbx-quickstart
```

From this point on, all commands assume you're in `~/sbx-quickstart`. No further `cd` into the repo directory is needed.

---

## 3. Installation

### macOS (Apple Silicon required)

**Step 1** — Install the CLI via Homebrew:

```bash
brew install docker/tap/sbx
```

**Step 2** — Sign in with your Docker account:

```bash
sbx login
```

This opens a browser for Docker OAuth. The CLI needs a Docker account to tie sandboxes
to a verified identity and enable governance features. Your code and prompts are never
sent to Docker.

**Step 3** — Verify:

```bash
sbx version
```

> Docker Desktop is **not** required.

---

### Windows (x86_64, Windows 11 required)

**Step 1** — Enable the Windows Hypervisor Platform (requires an elevated terminal):

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -All
```

Restart your machine when prompted.

**Step 2** — Download and install the `sbx` CLI from the Docker website, or via `winget`:

```powershell
winget install Docker.Sbx
```

**Step 3** — Sign in:

```powershell
sbx login
```

**Step 4** — Verify:

```powershell
sbx version
```

> **Windows note**: By default, Windows sandboxes use non-Docker template variants —
> the `docker` command isn't available inside the VM. If you need Docker-in-sandbox
> (required for the Docker Compose exercise), pass `--template`:
>
> ```powershell
> sbx run --template docker.io/docker/sandbox-templates:claude-code-docker claude
> ```

---

## 4. Authentication

The recommended way to authenticate Claude Code is via the **interactive OAuth flow**. When you launch a sandbox for the first time, Claude Code will prompt you to log in through your browser — no API keys or environment variables required.

```bash
sbx run claude
```

On first run, if you're not already authenticated, Claude Code opens a browser window and walks you through the OAuth flow. Once complete, the token is managed by the proxy — Claude inside the sandbox can call the API but never has access to the raw credential.

---

## 5. Orient yourself: first sandbox run

Open a terminal in `~/sbx-quickstart` and launch Claude:

```bash
sbx run claude
```

On your **very first run** (and after `sbx policy reset`) the daemon prompts you to
choose a network policy:

```
Choose a default network policy:

     1. Open         — All network traffic allowed, no restrictions.
     2. Balanced     — Default deny, with common dev sites allowed.
     3. Locked Down  — All network traffic blocked unless you allow it.

  Use ↑/↓ to navigate, Enter to select, or press 1–3.
```

Choose **Balanced** for this guide. It allows AI provider APIs, package managers
(npm, pip, PyPI), GitHub, and container registries out of the box. You can add more
hosts later with `sbx policy allow`.

The first run pulls the agent image (~1–2 minutes). Subsequent starts reuse the cache
and are nearly instant.

Once Claude starts, give it this orientation prompt:

```
Explore this codebase and give me:
1. A summary of the architecture and tech stack
2. How to run it locally (without Docker Compose if possible)
3. Any obvious issues or areas of concern you spot at a glance
4. What the test suite covers
```

Claude will read the source files, parse the README, check the requirements, and
report back. Because the workspace is mounted directly into the VM, Claude sees your
actual files — including any changes you make on the host while it's running.

### The detach/reattach pattern

`sbx run` is interactive — it occupies your terminal as a live agent session. Any time
you need to run a host-side command (`sbx ls`, `sbx ports`, `git diff`, etc.) you have
two options:

- **Open a new terminal tab** and leave Claude running in the original tab.
- **Detach** by pressing `Ctrl-C`. The agent keeps running in the background. Reattach
  any time with `sbx run <name>`.

This guide calls out which approach to use at each step. The key thing to remember:
detaching doesn't stop Claude — it just disconnects your view of the session.

**Check what's running** (new terminal or after detaching):

```bash
sbx ls
```

```
NAME                STATUS   UPTIME
devboard-guide      running  2m14s
```

---

## 6. The interactive TUI dashboard

The `sbx` TUI is a host-side command — run it in a **new terminal tab** while Claude
is running in another, or after detaching with `Ctrl-C`.

```bash
sbx
```

The dashboard shows:

- All sandboxes as cards with live **CPU and memory usage**
- Keyboard shortcuts for common actions

From the dashboard you can:

| Key      | Action                                          |
|----------|-------------------------------------------------|
| `c`      | Create a new sandbox                            |
| `s`      | Start or stop the selected sandbox              |
| `Enter`  | Attach to the agent session (same as `sbx run`) |
| `x`      | Open a shell inside the sandbox (`sbx exec`)    |
| `r`      | Remove the selected sandbox                     |
| `Tab`    | Switch between the Sandboxes panel and Network panel |
| `?`      | Show all shortcuts                              |

The **Network panel** (press `Tab`) shows a live log of every outbound connection the
sandbox makes — which hosts were reached, which were blocked, and which policy rule
applied. This is the fastest way to debug "why can't Claude install this package?"

Press `q` or `Ctrl-C` to exit the dashboard without stopping any sandboxes.

---

## 7. Branch mode: safe parallel development

By default, `sbx run` uses **direct mode** — Claude edits your working tree in place.
That's fine for quick tasks, but gets messy when you want to review changes before they
land, or run multiple agents at the same time.

**Branch mode** gives Claude its own Git worktree and branch, isolated from your main
working tree. You keep working normally; Claude works on its branch; you review the
diff and merge when you're happy.

### Before you start

Branch mode requires a Git repo with a GitHub remote. Since you already forked and cloned the repo in step 2, you're all set. Just make sure your fork is the configured remote:

```bash
git remote -v
```

You should see your fork listed as `origin`. Also store your GitHub token so Claude can push and open PRs from inside the sandbox:

```bash
echo "$(gh auth token)" | sbx secret set -g github
```

### Start a sandbox in branch mode

```bash
sbx run claude --name devboard-bugs --branch claude/fix-bugs
```

`sbx` creates a worktree under `.sbx/` in your repo root. All of Claude's changes land
in that worktree, not in your main working tree.

**Give Claude a concrete task immediately** — branch mode is most useful when the agent
has a clear goal to work toward autonomously:

```
The test suite has failing tests. Do the following without stopping:

1. Install backend dependencies: pip install -r backend/requirements.txt
2. Run the test suite: cd backend && pytest tests/ -v
3. Fix the pagination bug in backend/app/routers/issues.py
   (the skip calculation is wrong — look at list_issues())
4. Fix the updated_at bug in backend/app/models.py
   (the onupdate parameter is missing from both updated_at columns)
5. Re-run the full test suite and confirm all tests pass
6. Commit the fixes with a descriptive message
```

### Monitor progress without interrupting Claude

While Claude works, open a new terminal tab to watch the changes accumulate:

```bash
# Confirm the sandbox is running
sbx ls

# See the worktree Claude is working in
git worktree list

# Watch Claude's changes in real time
git diff main..claude/fix-bugs
```

You don't need to touch the session — Claude will work through all five steps
autonomously and report back when done.

### Reattach to review or follow up

Once you're ready to check in, reattach to the session:

```bash
sbx run devboard-bugs
```

You'll see the full conversation history. If you want Claude to do more before you
review, add a follow-up prompt:

```
Good. Now also add a brief comment above each fix explaining
the root cause, so the PR description is self-documenting.
```

### Review the diff and open a PR

When you're satisfied, detach (`Ctrl-C`) and review everything Claude changed:

```bash
# Full diff of all changes
git diff main..claude/fix-bugs

# Push the branch to GitHub
cd .sbx/devboard-bugs-worktrees/claude/fix-bugs
git push -u origin claude/fix-bugs

# Open a PR
gh pr create \
  --title "Fix: pagination offset and missing onupdate" \
  --body "Fixes off-by-one error in list_issues() and adds missing onupdate= to models."
```

### Clean up

```bash
sbx rm devboard-bugs
# Removes the VM, worktree, and local branch automatically
```

> **Running agents in parallel**: because each branch-mode sandbox works in its own
> worktree, you can run multiple agents on the same repo at the same time with no
> conflicts:
>
> ```bash
> sbx run claude ~/sbx-quickstart --name agent-search --branch claude/search
> sbx run claude ~/sbx-quickstart --name agent-notifications --branch claude/notifications
> ```

---

## 8. Exercise: run the test suite

This exercise gets Claude to set up the Python environment and run the backend tests
autonomously — a common first task when landing on an unfamiliar codebase.

**Start a named sandbox:**

```bash
sbx run claude --name devboard-tests --branch auto
```

**Give Claude this prompt:**

```
Set up the Python environment for the FastAPI backend and run the test suite.
Report:
- Which tests pass
- Which tests fail, with the full error output
- Your diagnosis of each failure

Use pytest with verbose output: cd backend && pytest tests/ -v
```

Claude will:
1. `pip install -r backend/requirements.txt`
2. `cd backend && pytest tests/ -v`
3. Report the results — including the failures planted in the codebase

Installed packages **persist** across agent restarts for this sandbox. If you stop and
re-run `sbx run devboard-tests`, you won't need to `pip install` again.

**Expected output** (before any fixes):

```
PASSED  tests/test_auth.py::test_register_new_user
PASSED  tests/test_auth.py::test_login_success
...
FAILED  tests/test_issues.py::test_pagination_first_page_returns_results
FAILED  tests/test_issues.py::test_pagination_second_page
FAILED  tests/test_issues.py::test_updated_at_changes_on_update
PASSED  tests/test_issues.py::test_search_returns_501_until_implemented
```

---

## 9. Exercise: bug hunt

With the failing tests identified, ask Claude to fix them. Continue in the same session
you opened in Section 7:

**Prompt:**

```
Three tests are failing. Fix each bug:

1. test_pagination_first_page_returns_results — the pagination offset is wrong
2. test_pagination_second_page — related to the same bug
3. test_updated_at_changes_on_update — the updated_at field never changes

For each fix:
- Explain what the bug is and why it causes the failure
- Show the diff of your change
- Re-run the specific test to confirm it passes before moving on
```

### What Claude should find

**Bug 1 & 2 — Pagination offset** (`backend/app/routers/issues.py`):

```python
# Buggy
skip = page * page_size

# Fixed
skip = (page - 1) * page_size
```

**Bug 3 — updated_at never refreshes** (`backend/app/models.py`):

```python
# Buggy — onupdate is missing
updated_at = Column(DateTime, default=datetime.utcnow)

# Fixed
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Watch file sync in action

While Claude is working, open the files in your editor on the **host**. You'll see
Claude's edits appear in real time as it writes them — the workspace mount is
bidirectional and instant. No copy step, no polling delay.

**After the fixes, run the full suite:**

```
# Prompt Claude:
Run the full test suite and confirm all tests pass (or are intentionally skipped).
```

---

## 10. Docker Compose inside the sandbox

Each sandbox has its own private Docker daemon. Claude can run `docker compose up`,
build images, and start containers — none of which appear in your host's `docker ps`.

**Start (or reconnect to) a named sandbox:**

```bash
sbx run claude --name devboard-compose
```

**Give Claude this prompt:**

```
Start the full application stack using Docker Compose.
Once everything is healthy:
1. Confirm the backend API is responding at http://localhost:8000/health
2. Create a test user via the API
3. Create a project and two issues for that user
4. Report the final state (user, project, issues) as JSON

Use the API docs at http://localhost:8000/docs if helpful.
Make sure all servers bind to 0.0.0.0 so I can reach them via port forwarding.
```

Claude will:
1. `docker compose up --build -d`
2. Wait for the `db` healthcheck to pass
3. Hit the API endpoints with `curl` or `httpx`

> **Windows users**: remember to pass `--template docker.io/docker/sandbox-templates:claude-code-docker`
> when creating this sandbox if you want Docker inside the VM.

The containers Claude starts live entirely inside the sandbox. When you `sbx rm`
the sandbox, all images, containers, and Postgres data are deleted automatically.

---

## 11. Port forwarding with `sbx ports`

Sandboxes are network-isolated — your browser can't reach a server inside one by
default. `sbx ports` punches a hole from a host port to a sandbox port.

> **Terminal note**: `sbx ports` is a host-side command. Run it in a **new terminal
> tab** while Claude is running, or detach first (`Ctrl-C`) then run it.

### Forward the API

With the Docker Compose stack running from the previous exercise:

```bash
sbx ports devboard-compose --publish 8080:8000
```

Now open your browser to `http://localhost:8080/docs` — that's the live Swagger UI
running inside the sandbox.

### Forward the frontend

```bash
sbx ports devboard-compose --publish 3001:3000
open http://localhost:3001
```

### Check active ports

```bash
sbx ls
# SANDBOX             AGENT   STATUS   PORTS                                        WORKSPACE
# devboard-compose    claude  running  127.0.0.1:8080->8000, 127.0.0.1:3001->3000  /…/devboard-guide

sbx ports devboard-compose
```

### Stop forwarding

```bash
sbx ports devboard-compose --unpublish 8080:8000
```

> **Gotcha**: services inside the sandbox must bind to `0.0.0.0`, not `127.0.0.1`.
> Most dev servers default to `127.0.0.1`. That's why the Section 9 prompt explicitly
> asks Claude to bind to `0.0.0.0`.

> **Gotcha**: published ports don't survive a sandbox stop/restart. Re-run
> `sbx ports` after restarting.

---

## 12. Exercise: implement issue search

The `GET /projects/{project_id}/issues/search` endpoint exists but returns `501`.
The TODO is well-commented. This exercise has Claude implement it end-to-end.

**Prompt (in any running sandbox):**

```
Implement the issue search endpoint in backend/app/routers/issues.py.

Requirements:
- Accept a `q` query parameter (case-insensitive)
- Match issues where the title OR description contains `q`
- Return results ordered by updated_at descending
- Write or update tests in tests/test_issues.py to cover:
  - A search that returns one match
  - A search with no matches (should return empty list, not 404)
  - A search that matches on description (not just title)
- Run the full test suite when done and confirm everything passes
```

### What to expect

Claude should use SQLAlchemy's `ilike` for the case-insensitive match and the `or_`
combinator. A correct implementation looks roughly like:

```python
from sqlalchemy import or_

results = (
    db.query(models.Issue)
    .filter(
        models.Issue.project_id == project_id,
        or_(
            models.Issue.title.ilike(f"%{q}%"),
            models.Issue.description.ilike(f"%{q}%"),
        ),
    )
    .order_by(models.Issue.updated_at.desc())
    .all()
)
return results
```

Once implemented, the frontend search bar (in `frontend/src/app/projects/[id]/page.tsx`)
will work automatically — type a query and press Enter.

---

## 13. Network policies

Every sandbox routes outbound HTTP/HTTPS through a host-side proxy that enforces
access rules you define. There are three built-in postures:

| Policy      | Description                                                      |
|-------------|------------------------------------------------------------------|
| Open        | All traffic allowed — no restrictions                            |
| Balanced    | Default deny, with a broad allow-list covering AI APIs, npm, pip, GitHub, registries |
| Locked Down | Everything blocked; you explicitly allow what you need           |

> **Terminal note**: all `sbx policy` commands run on the **host**, not inside a
> sandbox session. Open a new terminal tab or detach first.

### Inspect current rules

```bash
sbx policy ls
```

### See what the sandbox is actually hitting

```bash
sbx policy log
```

Example output:
```
Allowed requests:
SANDBOX            TYPE     HOST                    PROXY        LAST SEEN   COUNT
devboard-compose   network  api.anthropic.com       forward      10:15:23    42
devboard-compose   network  registry.npmjs.org      transparent  10:15:20    18
devboard-compose   network  files.pythonhosted.org  transparent  10:15:18    7

Blocked requests:
SANDBOX            TYPE     HOST                    PROXY        LAST SEEN   COUNT
devboard-compose   network  smtp.mailgun.org        transparent  10:16:01    1
```

The `PROXY` column matters: `forward` means credentials were injected (only for AI API
calls); `transparent` means policy was enforced but no credential injection.

### Allow additional hosts

```bash
# Allow one host
sbx policy allow network smtp.mailgun.org

# Allow multiple at once
sbx policy allow network "smtp.mailgun.org,api.sendgrid.com"

# Allow all npm and PyPI (useful if Claude can't install packages)
sbx policy allow network "*.npmjs.org,*.pypi.org,files.pythonhosted.org"
```

### Block a host

```bash
sbx policy deny network ads.example.com
```

### Try "Locked Down" mode

Reset to a fresh policy selection (host terminal):

```bash
sbx policy reset
# Choose "Locked Down" (option 3)
```

Then start a sandbox. Claude won't be able to reach `api.anthropic.com` until you
explicitly allow it:

```bash
sbx policy allow network api.anthropic.com
```

This demonstrates the principle of least privilege — your agent can only talk to what
you've approved.

### Restore Balanced

```bash
sbx policy reset
# Choose "Balanced" (option 2)
```

---

## 14. Multiple workspaces

You can mount additional directories into a sandbox alongside the primary workspace.
Useful patterns:

- A shared `libs/` repo the agent can reference (read-only)
- The `docs/` repo alongside the main `app/` repo
- Frontend and backend as separate repos, both mounted

### Mount two directories

```bash
sbx run claude ~/sbx-quickstart/backend ~/sbx-quickstart/frontend:ro --name devboard-full
```

- `~/sbx-quickstart/backend` — primary workspace (read/write); agent starts here
- `~/sbx-quickstart/frontend:ro` — mounted read-only; agent can read but not write

Both appear inside the sandbox at their **exact host paths**, so relative paths in
error messages match what you see locally.

### Cross-repo coordination exercise

With both workspaces mounted:

```
The frontend's api.ts sends search requests to GET /issues/search, but the
backend currently returns 501 for that endpoint. (Assume you've already
implemented the backend fix in a previous session.)

Review the frontend search flow in the frontend/src directory and make sure the
error handling is user-friendly when the endpoint isn't available yet.
The frontend is read-only — propose the change but don't apply it.
```

This pattern is common in monorepo setups where you want Claude to understand
the full picture but only write to specific parts.

---

## 15. Debugging with `sbx exec`

`sbx exec` opens a shell (or runs a command) inside a running sandbox. It always
runs in a **separate terminal** — it's a host command, not something you type inside
the Claude session.

Use it to:
- Inspect the environment Claude is working in
- Check Docker container status
- Run a quick test or command manually
- Install a tool the agent doesn't know it needs

### Open an interactive shell

```bash
# In a new terminal tab (or after detaching from Claude)
sbx exec -it devboard-compose bash
```

You're now inside the sandbox VM. Try:

```bash
# What containers is Claude's Docker daemon running?
docker ps

# What packages are installed?
pip list | grep fastapi

# Is the API actually listening?
curl -s http://localhost:8000/health | python3 -m json.tool
```

Type `exit` to leave the shell. The Claude session keeps running.

### Run a one-off command without a shell

```bash
sbx exec -d devboard-compose bash -c "cd /path/to/backend && pytest tests/ -v --tb=short"
```

### Set a persistent environment variable

Variables set inside the sandbox don't survive a restart. Write them to
`/etc/sandbox-persistent.sh` to make them permanent for the sandbox's lifetime:

```bash
sbx exec -d devboard-compose bash -c \
  "echo 'export SMTP_HOST=smtp.mailgun.org' >> /etc/sandbox-persistent.sh"
```

The file is sourced on every login shell, so Claude (and you) will see the variable
in subsequent sessions.

---

## 16. Credentials deep-dive

### Supported services

The `sbx secret` command maps a service name to the environment variable(s) the proxy
checks and the API domain(s) it authenticates:

| Service    | Environment variable(s)                        | API domain(s)              |
|------------|------------------------------------------------|----------------------------|
| `anthropic`| `ANTHROPIC_API_KEY`                            | `api.anthropic.com`        |
| `openai`   | `OPENAI_API_KEY`                               | `api.openai.com`           |
| `github`   | `GH_TOKEN`, `GITHUB_TOKEN`                     | `api.github.com`, `github.com` |
| `google`   | `GEMINI_API_KEY`, `GOOGLE_API_KEY`             | `generativelanguage.googleapis.com` |
| `groq`     | `GROQ_API_KEY`                                 | `api.groq.com`             |
| `aws`      | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`   | AWS Bedrock endpoints      |

### Give Claude access to GitHub

Useful for agents that open PRs or interact with issues:

```bash
echo "$(gh auth token)" | sbx secret set -g github
```

Claude can then use the `gh` CLI inside the sandbox.

### Scope a secret to one sandbox

```bash
# Global — applies to all new sandboxes
sbx secret set -g anthropic

# Sandbox-scoped — takes effect immediately, even for a running sandbox
sbx secret set my-sandbox anthropic
```

A sandbox-scoped secret overrides the global one if both are set.

### Custom tokens (not in the supported service list)

For services not listed above (e.g., a `BRAVE_API_KEY`), write the value to
`/etc/sandbox-persistent.sh` inside the sandbox:

```bash
sbx exec -d my-sandbox bash -c \
  "echo 'export BRAVE_API_KEY=your_key' >> /etc/sandbox-persistent.sh"
```

Note: unlike `sbx secret`, this stores the value inside the VM where the agent can
read it directly. Only use this for tokens where proxy injection isn't needed.

---

## 17. Production patterns

### Always name your sandboxes

Names make it easy to reconnect and avoid creating duplicates:

```bash
sbx run claude --name devboard-main
# Later:
sbx run devboard-main   # reconnects to existing sandbox
```

Without `--name`, sbx auto-names based on the workspace path. Running the same path
again reconnects correctly, but explicit names are clearer.

### Use branch mode for any autonomous work

Before starting a long-running task:

```bash
sbx run claude --name feature-search --branch claude/issue-search
```

This gives you a clean diff to review, and a one-command rollback if the result isn't
what you wanted:

```bash
git branch -D claude/issue-search
sbx rm feature-search
```

### Create sandboxes without attaching

Useful for pre-warming or scripting:

```bash
sbx create claude . --name devboard-ci
# Later, attach when needed:
sbx run devboard-ci
```

### Run multiple agents in parallel on the same repo

```bash
sbx run claude . --name agent-search --branch claude/search
sbx run claude . --name agent-notifications --branch claude/notifications
# Each works on its own branch — no conflicts
```

### Non-interactive environments (CI)

Set the default policy before running any other command:

```bash
sbx policy set-default balanced
sbx run claude --name ci-review -- "Review the diff in HEAD and report any issues"
```

### Clean up idle sandboxes

```bash
sbx ls
sbx rm devboard-old
sbx rm devboard-scratch
```

Sandboxes accumulate Docker image layers and VM disk. Remove ones you're done with.

### Custom templates

If you need a pre-configured environment (e.g., a specific Node version, pre-installed
tools), build a custom image on top of the base:

```dockerfile
FROM docker/sandbox-templates:claude-code

RUN apt-get update && apt-get install -y postgresql-client redis-tools
RUN npm install -g tsx pnpm
```

Then pass `--template` when creating:

```bash
sbx run claude --template myorg/devboard-template:latest --name devboard-custom
```

---

## Appendix A: Prompt library

These prompts are designed to work well with Claude in a Docker Sandbox. Copy, adapt,
and combine them for your own workflows.

---

### Understand a new codebase

```
Explore this repository and produce a technical overview covering:
1. Architecture and tech stack (include the full dependency list)
2. How data flows through the system end to end
3. How to run the project and its test suite locally
4. Any patterns or conventions the team seems to follow
5. The top 3 areas you'd investigate first if you were debugging a production incident

Be specific — cite filenames and line numbers where relevant.
```

---

### Run tests and triage failures

```
Run the full test suite for the [backend/frontend] and produce a triage report:
- List every failing test with its full error output
- For each failure, identify whether it's a test bug, a code bug, or a missing feature
- Propose a fix for each code bug (don't implement yet — just describe the approach)
- Estimate the effort to fix each issue (small / medium / large)
```

---

### Fix a specific bug

```
Fix the bug exposed by [test name].

Constraints:
- Change only the minimal code needed to fix this specific bug
- Do not refactor unrelated code
- After each change, re-run [test name] to verify it passes
- When it passes, run the full suite to check for regressions
- Explain the root cause in a comment above the fix
```

---

### Implement a feature

```
Implement [feature description] in [file/module].

Requirements:
[paste the requirements or link to a spec]

Done criteria:
- Feature works end-to-end (manually demonstrate it with curl or a test)
- Tests cover the happy path and at least two edge cases
- No existing tests are broken
- Code follows the patterns already in the file
```

---

### Set up and run a service with Docker Compose

```
Start the full application stack with Docker Compose.

1. Run `docker compose up --build -d` and wait for all services to be healthy
2. Confirm each service is running with `docker compose ps`
3. Hit the health endpoint for each API service and report the response
4. If any service fails to start, show the full logs and diagnose the issue
5. Once everything is healthy, run a quick smoke test:
   - Create a user
   - Authenticate
   - Create a resource and retrieve it
   Report the responses as JSON.

Make sure any server you start binds to 0.0.0.0 (not 127.0.0.1) so I can
reach it via sbx ports forwarding.
```

---

### Code review

```
Review the changes in [branch or file] as if this were a pull request.

Focus on:
1. Correctness — are there any bugs, edge cases, or logic errors?
2. Security — are there any injection risks, missing auth checks, or exposed secrets?
3. Performance — any obvious N+1 queries, blocking I/O, or unnecessary work?
4. Test coverage — are the important paths tested?
5. Code quality — readability, naming, consistency with the surrounding code

For each issue, provide: severity (P0/P1/P2), location (file + line), description,
and a suggested fix.
```

---

### Document a module

```
Write docstrings and inline comments for all public functions and classes in [file].

Rules:
- Follow the existing docstring style in the codebase
- Explain *why*, not just *what* — especially for non-obvious logic
- Add type hints to any function that's missing them
- Do not change any logic — documentation only
```

---

## Appendix B: CLI quick reference

```bash
# ── Lifecycle ──────────────────────────────────────────────────────────────────
sbx run claude                          # start (or reconnect to) a sandbox
sbx run claude --name my-sb             # with an explicit name
sbx run claude --branch my-feature      # branch mode — agent works on own branch
sbx run claude --branch auto            # let sbx name the branch
sbx create claude .                     # create without attaching
sbx ls                                  # list sandboxes        [host terminal]
sbx stop my-sb                          # pause (preserves installed packages)
sbx rm my-sb                            # delete sandbox + VM + worktrees

# ── Attach, detach & shell ─────────────────────────────────────────────────────
sbx run my-sb                           # reattach to agent session
# Ctrl-C inside sbx run               → detach (agent keeps running)
sbx exec -it my-sb bash                 # shell inside sandbox  [host terminal]
sbx exec -d my-sb bash -c "pytest -v"  # one-off command        [host terminal]

# ── Port forwarding ────────────────────────────────────────────────────────────
# (all sbx ports commands run in a host terminal)
sbx ports my-sb --publish 8080:8000    # host:8080 → sandbox:8000
sbx ports my-sb --publish 3000         # OS picks host port
sbx ports my-sb                        # show active forwarding rules
sbx ports my-sb --unpublish 8080:8000  # stop forwarding

# ── Network policies ───────────────────────────────────────────────────────────
# (all sbx policy commands run in a host terminal)
sbx policy ls                           # list active rules
sbx policy log                          # show connection log (allowed + blocked)
sbx policy log my-sb                    # filter by sandbox
sbx policy allow network example.com    # allow a host
sbx policy allow network "*.npm.org,*.pypi.org"  # allow multiple
sbx policy deny network ads.example.com # block a host
sbx policy rm network --resource example.com     # remove a rule
sbx policy reset                        # wipe all rules, reprompt for default policy
sbx policy set-default balanced         # set default without interactive prompt (CI)

# ── Credentials ────────────────────────────────────────────────────────────────
sbx secret set -g anthropic             # store Anthropic key globally
sbx secret set my-sb openai            # scope to one sandbox
sbx secret ls                           # list stored secrets
sbx secret rm -g github                 # remove a secret

# ── Dashboard ──────────────────────────────────────────────────────────────────
sbx                                     # open interactive TUI  [host terminal]

# ── Reset ──────────────────────────────────────────────────────────────────────
sbx reset                               # stop all VMs, delete all sandbox data
```

---

## Appendix C: Troubleshooting

### Agent can't install packages or reach an API

The network policy is blocking the domain. In a host terminal, check what's blocked:

```bash
sbx policy log
```

Then allow the domains you need:

```bash
sbx policy allow network "*.npmjs.org,*.pypi.org,files.pythonhosted.org,github.com"
```

Or allow everything:

```bash
sbx policy allow network "**"
```

---

### `You are not authenticated to Docker`

Your login session expired. Re-authenticate:

```bash
sbx login
```

---

### API key errors / agent can't reach model provider

1. Check that the secret is stored: `sbx secret ls`
2. Check that `api.anthropic.com` is in the allow list: `sbx policy log`
3. If you're in Locked Down mode, explicitly allow the API:
   ```bash
   sbx policy allow network api.anthropic.com
   ```
4. If you stored a global secret while a sandbox was already running, recreate the
   sandbox — global secrets only take effect at creation time:
   ```bash
   sbx rm my-sb
   sbx run claude --name my-sb
   ```

---

### Port forwarding isn't working

- Confirm the service binds to `0.0.0.0`, not `127.0.0.1`
- Published ports don't survive a restart — re-run `sbx ports` after `sbx stop`/`sbx run`
- Check the sandbox is still running: `sbx ls`
- Make sure you're running `sbx ports` from a host terminal, not from inside the sandbox session

---

### Docker not available inside the sandbox (Windows)

Use the `-docker` template variant:

```bash
sbx run --template docker.io/docker/sandbox-templates:claude-code-docker claude
```

---

### `git worktree` is stale after `sbx rm`

```bash
git worktree remove .sbx/<sandbox-name>-worktrees/<branch-name>
git branch -D <branch-name>
```

---

### Clock drift after sleep/wake

The VM clock can fall behind after a laptop sleeps. Stop and restart the sandbox to
re-sync:

```bash
sbx stop my-sb
sbx run my-sb
```

---

### Nuclear option: wipe all sbx state

```bash
sbx reset   # stops all VMs, deletes all data

# If sbx reset doesn't help:
# macOS:
rm -rf ~/Library/Application\ Support/com.docker.sandboxes/
# Windows:
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\DockerSandboxes"
```

---

*For the latest docs, visit [docs.docker.com/ai/sandboxes](https://docs.docker.com/ai/sandboxes/).*
