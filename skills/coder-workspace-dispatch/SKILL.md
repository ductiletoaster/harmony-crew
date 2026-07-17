---
name: coder-workspace-dispatch
description: Dispatch and operate Coder workspaces from inside an agent session via the bundled `coder` CLI. Use when the operator wants to demonstrate work in a browser, or when a task needs to run a project's real app stack (Docker compose, full boot, browser-reachable UI) that can't run inside the agent's local sandbox.
category: process
durability: durable
tier: subject
---

## When to use

The agent surface (this pi session) runs under syscall-isolated runtimes that don't host Docker daemons. When a project needs to actually run — `docker compose up`, full stack boot, browser-reachable UI — dispatch to a Coder workspace and exec inside it.

Use this skill when:
- The operator asks to demonstrate work in a browser
- A task requires running the project's full app, not just editing code or running unit tests
- You need a stable URL to hand back to the operator for poking around

Don't use this skill for:
- Pure code editing (stays in the agent surface)
- Unit tests / linting (local sandbox is enough)
- Git operations (agent surface)

## How auth + invocation works

The `coder` CLI binary is bundled into both pi-web and pi-worker images. Two env vars are pre-set:

- `CODER_URL=https://coder.lab.pixeloven.com`
- `CODER_SESSION_TOKEN` — Coder admin API token mounted from `op://Harmony/Coder/api_token` via ExternalSecret

You don't need to `coder login` — every subcommand uses those env vars automatically. Just call `bash` with the command.

## Common command set

### Start (or claim) a workspace
```bash
coder create --yes \
  --template envbuilder \
  --parameter git_url=https://github.com/ductiletoaster/harmony \
  --parameter git_ref=main \
  --parameter cpu_cores=2 \
  --parameter memory_gb=4 \
  harmony-demo
```
**Pass every template parameter explicitly.** `coder create --yes` confirms the workspace creation but does NOT auto-default unset parameters — it prompts interactively for each one. From inside a Pi session (no stdin) the prompt reads EOF and terraform dies with `prepare build: EOF`. The envbuilder template declares 4 parameters: `git_url`, `git_ref`, `cpu_cores`, `memory_gb`. Pass all four every time.

Idempotent in practice: if a workspace named `harmony-demo` already exists in `running` state, this becomes a no-op + prints the existing workspace info. If it's stopped, use `coder start` instead.

### Wait for the workspace agent to come online
```bash
coder ping harmony-demo --wait
```
The workspace pod can be `Running` in K8s before the in-workspace Coder agent has finished booting and registered. `coder ping --wait` blocks until the agent is reachable through the tailnet mesh.

### Run a command inside the workspace
```bash
coder ssh harmony-demo -- bash -lc "cd /workspaces/harmony && docker compose up --build -d"
```
The `-- bash -lc '<cmd>'` shape gives you a real login shell with the devcontainer's PATH; without `-l`, things like `docker compose` may not resolve depending on how the devcontainer feature installs them. Use `-d` for long-running services so the SSH exec returns immediately.

### List workspaces (yours)
```bash
coder list --output json | jq '.[] | {name, status, latest_build_status, owner}'
```

### Stop without deleting
```bash
coder stop harmony-demo --yes
```

### Delete (permanent)
```bash
coder delete harmony-demo --yes
```

### Get the browser URL
```bash
coder show harmony-demo --output json | jq -r '.workspace.access_url // empty'
```
For the wildcard-DNS app URLs (e.g., `harmony-demo--admin.coder.lab.pixeloven.com`), the pattern is `<workspace>--<owner>.coder.lab.pixeloven.com`.

### Read the workspace build log when something failed
```bash
coder show harmony-demo --output json | jq '.latest_build.job.error'
coder logs harmony-demo
```

## Pattern: demonstrate a code change

1. Edit code in the agent surface (this pi session).
2. Commit + push to a feature branch.
3. `coder create --yes --template envbuilder --parameter git_url=<repo-url> --parameter git_ref=<branch> --parameter cpu_cores=2 --parameter memory_gb=4 <ws-name>` — pass every template parameter (see Start workspace above)
4. `coder ping <ws-name> --wait` (envbuilder cold-start can take 1–3 minutes for image pull + devcontainer build)
5. `coder ssh <ws-name> -- bash -lc "<run-command>"`
6. Hand the workspace URL to the operator: `<ws-name>--<owner>.coder.lab.pixeloven.com`
7. After they validate, `coder stop` or `coder delete` to free resources.

## Gotchas

- **Workspace template must exist first.** `coder create` only instantiates from existing templates; new templates are pushed via the `sync-coder-templates.yaml` workflow when `infrastructure/coder/templates/<name>/main.tf` changes. If the operator asks for a template you don't see in `coder templates list`, that's a build step before this skill applies.
- **`envbuilder` cold start.** First-time workspace creation runs kaniko to build the devcontainer image — 1–3 minutes is normal. `coder ping --wait` is the right tool, not retrying `coder create`.
- **Workspace URL = wildcard subdomain pattern.** With `*.coder.lab.pixeloven.com` configured as the workspace wildcard, every workspace is reachable at `<ws-name>--<owner-username>.coder.lab.pixeloven.com`. Owner for the in-cluster admin token is `admin`.
- **Build failures.** If `coder create` returns "build failed", inspect via `coder show <ws> --output json | jq .latest_build.job` then `coder logs <ws>` for the terraform/kaniko trail.
- **Repo clone silently failed → fallback image.** If `coder ssh <ws> -- ls /workspaces/<repo>` returns empty, envbuilder fell back to `codercom/enterprise-base:ubuntu` because the git clone failed. Check `kubectl logs -n coder coder-admin-<ws>` for `Failed to clone repository`. Common cause: template sets `GIT_USERNAME` without `GIT_PASSWORD`, forcing GitHub auth that's rejected for public repos. The workspace boots but has no devcontainer features applied (no docker-in-docker, no node, etc.).
- **PodSecurity must allow privileged.** The `coder` namespace in this cluster runs `enforce: privileged` so envbuilder's kaniko build step can `privileged: true` inside kata isolation. If you ever see the build die with `forbidden: violates PodSecurity baseline:latest: privileged`, the namespace label was reverted.

## Related

- `harmony-platform-conventions` — broader cluster operating rules (tolerations, fsGroup 3000 NFS, etc.)
