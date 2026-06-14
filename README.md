# harmony-crew

A cross-project **agent foundation** for the projects I own — dual-published for two runtimes:

- **pi.dev** autonomous workers (a pi package)
- **Claude Code** (a plugin, via this repo's marketplace)

The same skill tree (`skills/<name>/SKILL.md`) feeds both runtimes; agents have a per-runtime variant.

> **Status — migration in progress.** Step 1 is a **verbatim 1:1 migration** of Harmony's agents + skills into this repo, in the plugin structure — so the content here is currently Harmony-specific. The goal is a reusable foundation; generic-vs-project-specific gets sorted out incrementally *backward* from this faithful baseline. (Classification: ~33 of Harmony's 39 skills are generic engineering; ~3 are truly Harmony-only.)

## What's in the box (migrated verbatim from Harmony)

**7 role agents** (`agents/*.md`, Claude format): `lead`, `triage`, `investigator`, `researcher`, `librarian`, `reviewer`, `implementer`.

**39 skills** (`skills/<name>/SKILL.md`) — Harmony's complete skill set, verbatim.

**pi side:** `pi-agents/role-*.md` currently holds Harmony's 6 generic pi-side agents (`implementer`/`investigator`/`lead`/`responder`/`reviewer`/`triage`); reconciling that roster with the 7 Claude agents is part of the backward refinement.

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
