---
name: tool-coder
description: Dispatching and operating Coder workspaces from inside an agent session via the coder CLI — run a project's real app stack (Docker, full boot, browser-reachable UI) that can't run in the agent sandbox. Active only when the project recipe declares a tools.* entry whose module = coder; reads endpoint/auth from that entry.
---

Generic Coder workspace-dispatch pattern. **Activation:** load this only when the recipe has a
`tools.*` entry whose `module` is `coder` (the recipe author chooses the role key — it's commonly
`exec`, but read the module value, not the key). Take the Coder URL and session token from **that
coder entry's** `.endpoint` and `.auth` — never hard-code them.

## When to use

The agent surface runs under syscall-isolated runtimes that don't host a Docker daemon. When a
project actually needs to **run** — `docker compose up`, full stack boot, a browser-reachable UI —
dispatch to a Coder workspace and exec inside it. Use it when the operator wants to demonstrate
work in a browser, or a task needs the project's real app stack and a stable URL to hand back.

Don't use it for pure code editing, unit tests/linting, or git operations — those stay in the
agent surface.

## Surfaces

Workspace lifecycle runs entirely through the **`coder` CLI** (create / ping / ssh / list / stop /
delete). Auth is by two env vars derived from the recipe entry — no interactive `coder login`:

```bash
export CODER_URL=<the coder entry's .endpoint>
export CODER_SESSION_TOKEN=$(<resolve the coder entry's .auth>)   # e.g. op read op://…/api_token
```

Every subcommand picks those up automatically; just call `bash` with the command.

## Common command set

### Start (or claim) a workspace — pass EVERY parameter

```bash
coder create --yes \
  --template <template> \
  --parameter git_url=<repo-url> \
  --parameter git_ref=<branch> \
  --parameter cpu_cores=2 \
  --parameter memory_gb=4 \
  <workspace-name>
```

**Pass every template parameter explicitly.** `coder create --yes` confirms creation but does NOT
auto-default unset parameters — it prompts interactively for each one. From inside an agent session
(no stdin) the prompt reads **EOF** and terraform dies with `prepare build: EOF`. Enumerate the
template's parameters once (`coder templates list` / the template's `main.tf`) and pass all of them
every time.

Idempotent in practice: if a workspace of that name is already `running`, this is a no-op that
prints its info. If it's stopped, use `coder start` instead.

### Wait for the workspace agent to come online

```bash
coder ping <workspace-name> --wait
```

The workspace pod can be `Running` before the in-workspace Coder agent has registered.
`coder ping --wait` blocks until the agent is reachable through the tailnet mesh. This — not
retrying `coder create` — is the right tool for cold-start latency.

### Run a command inside the workspace

```bash
coder ssh <workspace-name> -- bash -lc "cd /workspaces/<repo> && docker compose up --build -d"
```

The `-- bash -lc '<cmd>'` shape gives a real **login** shell with the devcontainer's PATH; without
`-l`, things like `docker compose` may not resolve. Use `-d` for long-running services so the SSH
exec returns immediately.

### List / stop / delete

```bash
coder list --output json | jq '.[] | {name, status, latest_build_status, owner}'
coder stop   <workspace-name> --yes      # stop without deleting
coder delete <workspace-name> --yes      # permanent
```

### Get the browser URL

```bash
coder show <workspace-name> --output json | jq -r '.workspace.access_url // empty'
```

For wildcard-DNS per-workspace app URLs, the pattern is `<workspace>--<owner>.<wildcard-domain>`
(the wildcard domain comes from `facts.domains` / the coder entry's `.notes`).

### Inspect a failed build

```bash
coder show <workspace-name> --output json | jq '.latest_build.job.error'
coder logs <workspace-name>
```

## Pattern: demonstrate a code change

1. Edit code in the agent surface.
2. Commit + push to a feature branch.
3. `coder create --yes --template <t> --parameter git_url=<repo> --parameter git_ref=<branch> --parameter cpu_cores=2 --parameter memory_gb=4 <ws>` — pass every parameter.
4. `coder ping <ws> --wait` (image-building templates cold-start in minutes).
5. `coder ssh <ws> -- bash -lc "<run-command>"`.
6. Hand the URL to the operator: `<ws>--<owner>.<wildcard-domain>`.
7. After validation, `coder stop` or `coder delete` to free resources.

## Gotchas (project-agnostic)

- **Template must exist first.** `coder create` only instantiates existing templates; pushing a new
  template is a separate build step before this module applies.
- **Image-building templates cold-start slowly.** First-time creation runs an image build —
  minutes is normal. Wait with `coder ping --wait`, don't retry `coder create`.
- **Repo clone can silently fall back.** If `coder ssh <ws> -- ls /workspaces/<repo>` is empty, the
  builder fell back to a base image because the git clone failed (common cause: a username set
  without a matching credential, forcing rejected auth on a public repo). The workspace boots but
  has no devcontainer features.

## Everything project-specific comes from the recipe

| Need | Source |
|------|--------|
| Coder URL (`CODER_URL`) | the coder entry's `.endpoint` |
| Session token (`CODER_SESSION_TOKEN`) | the coder entry's `.auth` |
| Repo to clone, template name, owner, wildcard domain | the coder entry's `.notes` + `facts.domains` |

This module is the entire Coder-specific surface. To make Coder dispatch work for a new project,
that project adds a `tools.*` entry with `module: coder` to its recipe — it writes no exec skill of
its own.
