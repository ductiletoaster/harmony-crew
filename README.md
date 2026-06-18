# harmony-crew

A cross-project **agent foundation** for the projects I own — dual-published for two runtimes:

- **pi.dev** autonomous workers (a pi package)
- **Claude Code** (a plugin, via this repo's marketplace)

The same skill tree (`skills/<name>/SKILL.md`) feeds both runtimes; agents have a per-runtime variant.

> **Status — migration in progress.** Step 1 is a **verbatim 1:1 migration** of Harmony's agents + skills into this repo, in the plugin structure — so the content here is currently Harmony-specific. The goal is a reusable foundation; generic-vs-project-specific gets sorted out incrementally *backward* from this faithful baseline. (Classification: ~33 of Harmony's 39 skills are generic engineering; ~3 are truly Harmony-only.)

## What's in the box (migrated verbatim from Harmony)

**8 role agents** (`agents/*.md`, Claude format): `lead`, `triage`, `investigator`, `researcher`, `responder`, `librarian`, `reviewer`, `implementer`.

**39 skills** (`skills/<name>/SKILL.md`) — Harmony's complete skill set, verbatim.

**pi side:** `pi-agents/role-*.md` carries the **same 8** roles in pi-subagents format. A role is harness-agnostic — only the manifest frontmatter differs (Claude: `name`/`description`; pi: `tools`/`model`/`thinking`/`max_turns`).

`role-researcher` + `role-librarian` were brought in **verbatim** from Harmony's `.pi/` overlay; `responder` is authored in Harmony's agent conventions and bound to the same substrate as the others (`memory-substrate` Read Routing, `vault.*`, QMD, `source_agent` provenance) — so every agent keeps the concrete skill/tool bindings that let it actually load skills and act. The bodies are still Harmony-flavored; **de-Harmonizing them into project-agnostic form (and rebinding each reference to a consumer's actual skills) is the deliberate backward-refinement pass** — not done here, to keep the 1:1 baseline faithful.

## Install

### pi.dev

In a project's `.pi/settings.json`:

```json
{
  "packages": [
    "npm:@tintinweb/pi-subagents",
    "git:github.com/ductiletoaster/harmony-crew@v0.3.0"
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

## Onboarding — the behavioral scaffold

Installing the package/plugin gives a project the **agents + skills**. It does *not* give it an entry file — agent *behavior* (delegation, routing, posture, the platform↔local bridge, fallback) is driven by an `AGENTS.md` at the repo root, which is repo-local and must be instantiated per project.

[`templates/AGENTS.md`](templates/AGENTS.md) is that scaffold — the **portable behavioral contract**, with the project-specific spots marked `▸ Fill for your project`. To onboard:

1. Copy `templates/AGENTS.md` to your repo root as `AGENTS.md`.
2. (Claude Code) add a one-line `CLAUDE.md` containing `@AGENTS.md`.
3. Fill **only** the `▸ Fill` blocks — your ask-list, tripwires, local-skills table, verification commands, repo. Keep the rest of the spine as-is.
4. Author your project's **local skills** (`.claude/skills/`) for the specifics those blocks point at.

This is **merge-don't-replace**: the foundation supplies the behavioral spine; you append your specifics. Conventions and facts live in skills, never in `AGENTS.md`. Worked example: [Harmony's filled `AGENTS.md`](https://github.com/ductiletoaster/harmony/blob/main/AGENTS.md).

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
