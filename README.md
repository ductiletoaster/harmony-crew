# harmony-crew

A generic **agent foundation** — 6 role agents + project-agnostic skills — dual-published for two runtimes:

- **pi.dev** autonomous workers (a pi package)
- **Claude Code** (a plugin, via this repo's marketplace)

The same skill tree (`skills/<name>/SKILL.md` + frontmatter) feeds both runtimes; agents have a per-runtime variant because their frontmatter differs.

> Despite the name, this package is **foundation-only**: no project context is baked in. Project-specific skills/roles live in each consuming project's overlay (`.pi/` for pi, `.claude/` for Claude Code), which shadows these entries when names collide. "harmony-" is just the org brand.

## What's in the box

**6 role agents** — operational shapes, not behavioural knowledge. Capability is added as a skill, not a new agent.

| Agent | Role |
|-------|------|
| `lead` | Orchestrator/planner. Writes plans, dispatches workers. Does not mutate code. |
| `triage` | Intake + label routing. No code/config writes. |
| `investigator` | Read-only diagnosis. Produces briefs. |
| `responder` | Drafts answers/replies from the corpus. Drafts only — a human sends. |
| `reviewer` | Adversarial review, hard-coded skeptical posture. Comment-only. |
| `implementer` | Privileged write path. Branch + PR only. Strict scope discipline. |

`agents/pi/role-*.md` — pi-subagents frontmatter (`tools`, `model: litellm:*`, `thinking`, `max_turns`).
`agents/claude/*.md` — Claude subagent frontmatter (`tools`, `model: opus|sonnet|haiku`). Model/tool assignments are tunable.

**7 project-agnostic skills** (`skills/<name>/SKILL.md`): `autonomous-agent-design`, `github-actions-conventions`, `github-repo-workflow`, `mcp-server-design`, `orchestration-patterns`, `plan-generation`, `plan-validation`.

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
├── agents/
│   ├── pi/role-*.md                # pi-subagents frontmatter
│   └── claude/*.md                 # Claude subagent frontmatter
├── package.json                    # pi package manifest
└── .claude-plugin/
    ├── plugin.json                 # Claude plugin manifest (agents → ./agents/claude)
    └── marketplace.json            # this repo doubles as its own marketplace
```

## First consumer

`ductiletoaster/harmony` consumes this foundation and layers its homelab-specific skills/roles on top — the reference example of the overlay model.
