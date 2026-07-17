# harmony-crew

A cross-project **agent foundation** for the projects I own — dual-published for two runtimes:

- **pi.dev** autonomous workers (a pi package)
- **Claude Code** (a plugin, via this repo's marketplace)

The same skill tree (`skills/<name>/SKILL.md`) feeds both runtimes; agents have a per-runtime variant.

> **Status — generalizing backward.** The initial seed was a **verbatim 1:1 migration** of Harmony's agents + skills, so much content is still Harmony-specific. The goal is a reusable foundation; generic-vs-project-specific is being sorted out incrementally — extracting generic patterns into these skills and leaving project-specific values in each consumer's local skills. Platform-capability skills (e.g. `openclaw-platform-operations`) are now authored generically here directly, not migrated.

## What's in the box (migrated verbatim from Harmony)

**8 role agents** (`agents/*.md`, Claude format): `lead`, `triage`, `investigator`, `researcher`, `responder`, `librarian`, `reviewer`, `implementer`.

**39 skills** (`skills/<name>/SKILL.md`) — Harmony's migrated skill set plus generic platform-capability skills authored directly into the foundation.

**Skill tiers.** Every `SKILL.md` carries a `tier:` frontmatter field placing it in the layering:

- **`tier: concept`** — platform-generic patterns and methodology; subject- and harness-agnostic; the generic base other skills build on (e.g. planning, the seam registry, the memory-substrate model, LiteLLM federation, orchestration patterns).
- **`tier: subject`** — about a specific tool/product/technology; project-agnostic; typically builds on a concept skill (e.g. operating ArgoCD or ComfyUI, Terraform/Python/K8s conventions).

There is deliberately no `project` tier: skills hardcoded to one deployment (node IPs, one cluster's topology, one org's conventions) belong in that consumer's **local** repo, not the foundation. The two wholly-project-specific skills (`homelab-topology`, `harmony-platform-conventions`) have been extracted to the first consumer's local repo. In-skill residue (a stray service URL or team name inside an otherwise-generic skill) is still being generalized backward incrementally.

**pi side:** `pi-agents/role-*.md` carries the **same 8** roles in pi-subagents format. A role is harness-agnostic — only the manifest frontmatter differs (Claude: `name`/`description`; pi: `tools`/`model`/`thinking`/`max_turns`).

`role-researcher` + `role-librarian` were brought in **verbatim** from Harmony's `.pi/` overlay; `responder` is authored in Harmony's agent conventions and bound to the same substrate as the others (`memory-substrate` Read Routing, `vault.*`, QMD, `source_agent` provenance) — so every agent keeps the concrete skill/tool bindings that let it actually load skills and act. The bodies are still Harmony-flavored; **de-Harmonizing them into project-agnostic form (and rebinding each reference to a consumer's actual skills) is the deliberate backward-refinement pass** — not done here, to keep the 1:1 baseline faithful.

## Install

### pi.dev

In a project's `.pi/settings.json` — pin the tag for reproducible builds:

```json
{
  "packages": [
    "npm:@tintinweb/pi-subagents",
    "git:github.com/ductiletoaster/harmony-crew@v0.4.0"
  ]
}
```

The project adds its own `.pi/skills/<name>/SKILL.md` and `.pi/agents/<name>.md` overlay for project-specifics; pi walks the overlay from cwd to git root before the package.

### Claude Code

Enable the plugin in `.claude/settings.json` (project-level), or in `~/.claude/settings.json` to enable it across **all** your projects:

```json
{
  "extraKnownMarketplaces": {
    "harmony-crew": {
      "source": { "source": "github", "repo": "ductiletoaster/harmony-crew" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "harmony-crew@harmony-crew": true }
}
```

No `ref` ⇒ it tracks the latest release on `main`; `autoUpdate` pulls it on startup — you never edit a pin. (Add `"ref": "v0.4.0"` to the `source` if you'd rather pin a fixed version.) Interactively: `/plugin marketplace add ductiletoaster/harmony-crew` then `/plugin install harmony-crew@harmony-crew`. The project keeps its own `.claude/skills/` + `.claude/agents/` overlay, which shadows the plugin's foundation entries when names collide.

## Versioning

One semver line drives both runtimes. Claude Code only re-fetches a plugin when `plugin.json`'s `version` changes — commits alone don't ship — so **every change merged to `main` moves the version**: a CI workflow ([`.github/workflows/release.yml`](.github/workflows/release.yml)) auto-bumps the patch and tags it, or a PR may set a minor/major explicitly. `plugin.json` == `package.json` == the git tag `vX.Y.Z`. Claude consumers track `main` (always latest); pi consumers and in-cluster image bakes pin the tag (reproducible).

## Onboarding — the `onboarding` skill

Installing the package/plugin gives a project the **agents + skills**, but not an entry file — agent *behavior* (delegation, routing, posture, the platform↔local bridge, fallback) is driven by a repo-local `AGENTS.md` that must be instantiated per project. The foundation is **opinionated** (like the Karpathy guidelines), and the [`onboarding`](skills/onboarding/SKILL.md) skill applies that opinion to a project — just ask an agent to *onboard this project to harmony-crew* (or re-audit it):

- **New project** → generates an `AGENTS.md` from the [`templates/AGENTS.md`](templates/AGENTS.md) scaffold, inferring what it can (test commands, repo) and suggesting the rest.
- **Existing project** → audits `AGENTS.md`/`CLAUDE.md` against the patterns: routes delegation to the foundation's agents, adds the behavioral spine where missing, and **moves facts/conventions out of the entry files into local skills**.
- **Re-runnable** → run it again as the project grows to keep the entry files behavioral and the facts in skills.

This is **merge-don't-replace**: the foundation supplies the behavioral spine; the project fills its specifics. Prefer the skill; the template is the canonical shape if you'd rather hand-copy. Conventions and facts live in skills, never in `AGENTS.md`. Worked example: [Harmony's filled `AGENTS.md`](https://github.com/ductiletoaster/harmony/blob/main/AGENTS.md).

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
