---
name: coder-workspace-dispatch
description: Dispatch and operate Coder dev workspaces (sandboxes) from an agent session — via the federated `coder` MCP tools (any client whose VK holds the `coder` access group) or the bundled `coder` CLI (pi). Use when a task needs to run a project's real app stack (Docker compose, full boot, browser-reachable UI) that can't run inside the agent's local sandbox, or to demonstrate work in a browser.
tier: subject
requires: [mcp:coder]
audience: [crew]
---

## When to use

Agent surfaces run under syscall-isolated runtimes that don't host a Docker daemon. When a task needs to actually **run** — `docker compose up`, full stack boot, a browser-reachable UI — dispatch a **Coder workspace** and drive it.

Use this skill when:
- A task requires running the project's full app, not just editing code or unit tests
- The operator asks to demonstrate work in a browser
- You need a stable URL to hand back for poking around

Don't use it for pure code editing, unit tests / linting, or git — those stay in the agent surface.

## Two ways to reach Coder

Coder exposes its **own** MCP server (Coder-maintained; no custom wrapper). Reach it whichever way your harness is wired:

| Path | Who | How |
|------|-----|-----|
| **MCP tools** (default) | **any client** whose VK holds the `coder` access group (Claude Code, pi, OpenClaw agents) | The platform federates Coder's remote MCP through the LLM gateway. Tools surface as `coder_*` (via the gateway, prefixed — e.g. `coder-coder_create_workspace`, plus your harness's own MCP prefix). No CLI, no token handling — the gateway injects auth. |
| **`coder` CLI** | **pi** (CLI bundled in the pi-web / pi-worker images) | `CODER_URL` + `CODER_SESSION_TOKEN` are pre-set (admin token via ExternalSecret from `op://<vault>/Coder/api_token`); every subcommand uses them, no `coder login`. Call via `bash`. |

If the `coder_*` tools aren't visible to you, your VK lacks the `coder` group (see your platform's access-map skill) — fall back to the CLI only if your harness bundles it, else say so.

## Core operations (MCP tool ↔ CLI)

| Operation | MCP tool | CLI |
|-----------|----------|-----|
| List your workspaces | `coder_list_workspaces` | `coder list --output json` |
| Inspect one | `coder_get_workspace` | `coder show <ws> --output json` |
| **Create / claim** | `coder_create_workspace` (pass every template parameter) | `coder create --yes --template <t> --parameter …` |
| Start / **stop / delete** | `coder_create_workspace_build` (`transition: start\|stop\|delete`) | `coder start` / `coder stop --yes` / `coder delete --yes` |
| **Run a command (exec)** | `coder_workspace_bash` | `coder ssh <ws> -- bash -lc "<cmd>"` |
| List / read / write / edit files | `coder_workspace_ls` / `coder_workspace_read_file` / `coder_workspace_write_file` / `coder_workspace_edit_file(s)` | `coder ssh <ws> -- …` |
| App URLs / port-forward | `coder_workspace_list_apps` / `coder_workspace_port_forward` | `coder show`… / `coder port-forward` |
| Build / agent logs | `coder_get_workspace_build_logs` / `coder_get_workspace_agent_logs` | `coder logs <ws>` |
| Templates (read-only) | `coder_list_templates` / `coder_get_template` / `coder_template_version_parameters` | `coder templates list` |

**Scope note (MCP):** the federated `coder` server is deliberately scoped — workspace lifecycle + exec + file ops + logs + **read-only** templates. Template *creation/mutation* and Task tools are intentionally excluded from the MCP surface; if you truly need them, that's a CLI/operator step, not this tool path.

**Pass every template parameter explicitly.** Coder does not auto-default unset parameters — via the CLI it prompts interactively (and dies `prepare build: EOF` with no stdin); via MCP an omitted required parameter fails the build. Use `coder_template_version_parameters` / `coder templates` to learn the parameter set first (e.g. an `envbuilder` template typically declares `git_url`, `git_ref`, `cpu_cores`, `memory_gb`).

## Pattern: demonstrate a code change

1. Edit + commit + push to a feature branch (agent surface).
2. **Create** a workspace from the branch — `coder_create_workspace` with `git_ref=<branch>` + all params.
3. **Wait for the agent** — the workspace pod can be `Running` before the in-workspace Coder agent registers. Poll `coder_get_workspace` until the agent is ready (CLI: `coder ping <ws> --wait`). `envbuilder` cold start (kaniko devcontainer build) is 1–3 min — normal; don't retry create.
4. **Run** the stack — `coder_workspace_bash` `cd /workspaces/<repo> && docker compose up --build -d` (use `-d` so the call returns).
5. **Hand back the URL** — `coder_workspace_list_apps`, or the wildcard pattern `<ws>--<owner>.<coder-host>` (owner for the in-cluster admin token is `admin`).
6. After validation, **stop or delete** to free resources — `coder_create_workspace_build` `transition: stop` (or `delete`).

## Gotchas (apply to both paths)

- **Template must exist first.** Create only instantiates existing templates; new ones are pushed via the template-sync workflow when `infrastructure/coder/templates/<name>/main.tf` changes. Unknown template → build step first, not this skill.
- **Workspace URL = wildcard subdomain.** With `*.<coder-host>` configured, every workspace is reachable at `<ws>--<owner>.<coder-host>`.
- **Repo clone silently failed → fallback image.** If the workspace has no `/workspaces/<repo>`, envbuilder fell back to `codercom/enterprise-base:ubuntu` (git clone failed — often a template setting `GIT_USERNAME` without `GIT_PASSWORD`, rejected for public repos). The workspace boots but has no devcontainer features (no docker-in-docker, node, etc.). Check `coder_get_workspace_build_logs` / `kubectl logs -n coder coder-admin-<ws>`.
- **PodSecurity must allow privileged.** The `coder` namespace runs `enforce: privileged` so envbuilder's kaniko step can go `privileged: true` inside kata isolation. `forbidden: violates PodSecurity` on build → the namespace label was reverted.

## Related

- your platform's access-map skill — which VKs hold the `coder` group + the gateway/host values
- your platform's conventions skill — cluster operating rules (tolerations, fsGroup, PodSecurity)
