# harmony-crew

A **personal multi-project agent foundation** — 7 role agents + a library of generic skills (conventions, tool modules, recipe-driven routing) — dual-published for two runtimes:

- **pi.dev** autonomous workers (a pi package)
- **Claude Code** (a plugin, via this repo's marketplace)

The same skill tree (`skills/<name>/SKILL.md` + frontmatter) feeds both runtimes; agents have a per-runtime variant because their frontmatter differs.

> A **personal toolkit**, not an OSS package: the foundation carries the patterns, the **tool modules** for the stack you run across your projects, and the agent→tool routing. Each consuming project supplies a single **recipe** (`.pi/project.yaml`) with its deltas — which tools, where, plus a few facts. No one project's *values* are baked in (those come from the recipe); the overlay (`.pi/`, `.claude/`) still shadows the foundation when names collide. See `RECIPE.md`.

## What's in the box

**7 role agents** — operational shapes, not behavioural knowledge. Each reads the project recipe first; capability is added as a skill, not a new agent.

| Agent | Role |
|-------|------|
| `lead` | Orchestrator/planner. Writes plans, dispatches workers. Does not mutate code. |
| `triage` | Intake + label routing. No code/config writes. |
| `investigator` | Read-only diagnosis. Produces briefs. |
| `responder` | Drafts answers/replies from the corpus. Drafts only — a human sends. |
| `researcher` | Option analysis → a structured note (via the recipe's memory module). |
| `reviewer` | Adversarial review, hard-coded skeptical posture. Comment-only. |
| `implementer` | Privileged write path. Branch + PR only. Strict scope discipline. |

`pi-agents/role-*.md` — pi-subagents frontmatter (`tools`, `model: litellm:*`, `thinking`, `max_turns`); `pi.agents` points here.
`agents/*.md` — Claude subagent frontmatter (`tools`, `model: opus|sonnet|haiku`); the plugin's default agents location. Model/tool assignments are tunable.

**Skills** (`skills/<name>/SKILL.md`) come in three kinds: generic **pattern** skills (stack conventions — python/terraform/ansible/k8s; process — pr-review/intake/plan/seam-detection); **tool modules** (`tool-<x>/`, opt-in per recipe — argocd, litellm, external-secrets, vault-substrate, comfyui, coder, searxng); and the **routing contract** (`agent-routing` + `RECIPE.md`). A consuming project activates tool modules and supplies values through its recipe.

## Install

### pi.dev

In a project's `.pi/settings.json`:

```json
{
  "packages": [
    "npm:@tintinweb/pi-subagents",
    "git:github.com/ductiletoaster/harmony-crew@v0.1.0"
  ]
}
```

The project adds its own `.pi/skills/<name>/SKILL.md` and `.pi/agents/<name>.md` overlay for project-specifics; pi walks the overlay from cwd to git root before the package.

### Claude Code

Add the marketplace and enable the plugin — per-project via a checked-in `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "harmony-crew": { "source": { "source": "github", "repo": "ductiletoaster/harmony-crew" } }
  },
  "enabledPlugins": { "harmony-crew@harmony-crew": true }
}
```

…or interactively: `/plugin marketplace add ductiletoaster/harmony-crew` then `/plugin install harmony-crew@harmony-crew`. The project keeps its own `.claude/skills/` + `.claude/agents/` overlay, which shadows the plugin's foundation entries when names collide.

## Catalog scope — foundation vs overlay

The dividing test is **"no project context baked in"** — not width. A single-language convention skill is fine in foundation if any project benefits; a skill that binds to a specific project's vault, gateway, cluster, secret paths, or domains is **not** — it belongs in that project's overlay.

## Layout

```
harmony-crew/
├── skills/<name>/SKILL.md          # one tree → pi + Claude both read it
├── agents/*.md                     # Claude subagent frontmatter (plugin default location)
├── pi-agents/role-*.md             # pi-subagents frontmatter (pi.agents → ./pi-agents)
├── package.json                    # pi package manifest
└── .claude-plugin/
    ├── plugin.json                 # Claude plugin manifest (agents from default ./agents)
    └── marketplace.json            # this repo doubles as its own marketplace
```

## First consumer

`ductiletoaster/harmony` consumes this foundation and layers its homelab-specific skills/roles on top — the reference example of the overlay model.
