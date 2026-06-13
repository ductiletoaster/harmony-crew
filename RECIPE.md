# Project Recipe — the contract between harmony-crew and a consuming project

harmony-crew is a **personal multi-project agent foundation**: the role agents, the
generic patterns, the agent→tool routing, and a library of **tool modules** for the
tools you run across your own projects (LiteLLM, ArgoCD, External Secrets, the vault
substrate, Coder, ComfyUI, …).

A consuming project supplies one **recipe** declaring its deltas — overwhelmingly,
*which tools it uses and where they live*, plus a handful of platform facts. The recipe
is the project's single source of truth; foundation skills and agents read it instead
of hard-coding anything.

> Not an OSS package — a toolkit for the projects you own. The foundation bakes in *your*
> stack and how your crew uses it; a new project (Harmony, FireRisk, …) is a new recipe.

## Location

- **pi runtime:** `.pi/project.yaml`
- **Claude Code:** `.claude/project-profile.md` (same fields)

## Schema

```yaml
identity:
  name: <project>            # short name — prompts + note attribution
  cli:  <cmd>                # the project's task CLI, if any (e.g. hmy)
  repo: <owner>/<name>

tools:                       # THE project-specific core: which modules are active + where
  <role>:                    # role = gateway | gitops | secrets | memory | media | exec | search | …
    module:   <module-name>  # names a foundation tool module: skills/tool-<module>/
    endpoint: <host/url>     # connection target the module uses
    auth:     <ref>          # how to authenticate (op:// ref, env var, token path)
    mcp:      <prefix>       # MCP tool prefix when the tool is reached via the gateway
    notes:    <free text>    # project quirks the module must respect

facts:                       # concrete platform values the pattern skills reference
  storage_fast: <class>
  storage_bulk: <class>
  fsGroup: <gid>
  tolerations: [ <taint-key> ]
  runtimes: { default: <runc|…>, sandboxed: <kata|…> }
  domains: <wildcard or list>

seams:                       # this project's protected-seams registry (name + one-line why)
  - <seam>: <why it needs human sign-off>

stack:                       # language / IaC toolchain the convention patterns apply to
  python: { pkg: uv, lint: ruff, test: pytest, layout: src }
  iac:    { tool: terraform, stages: [ … ] }
```

## How it's consumed

1. Every agent loads the recipe **first** (it's small). See `agent-routing`.
2. The agent assembles its loadout: **role base skills** (fixed, foundation) **+ a tool
   module for every active `tools.*` entry**.
3. Pattern skills (`<stack>-conventions`, `k8s-*`, `pr-review-checklist`, …) take concrete
   values from `facts` / `stack` — never hard-coded.
4. Tool modules read their own `tools.<role>` block for endpoint / auth / mcp.

**A new project = write a recipe.** No new skills unless it runs a tool no module covers yet.
