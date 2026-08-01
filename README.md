# harmony-crew

A cross-project **agent foundation** for the projects I own — one shared skill tree, consumed by **three harnesses**:

| Harness | What it runs | Consumes | How |
|---------|-------------|----------|-----|
| **Claude Code** | operator/dev sessions + subagents | the **full** foundation (8 role agents + all skills) | plugin (this repo's marketplace) |
| **pi.dev** | autonomous workers | the **full** foundation (8 role agents + all skills) | pi package |
| **OpenClaw** | assistant/companion agents (personas) | a **consumption slice** of skills (no roles) | skills installed into the gateway |

The same `skills/<name>/SKILL.md` tree feeds all three. Claude Code and pi.dev also run the **8 crew roles** (`lead`, `implementer`, …) with a per-runtime agent variant; **OpenClaw does not** — its agents are project personas (Aria, Vesper, …), so it consumes only the skill *slice* that lets an agent *use the platform* (web search, image gen, knowledge base), not the operator/dev catalog.

> **Status — generalizing backward.** The initial seed was a **verbatim 1:1 migration** of Harmony's agents + skills. The goal is a reusable foundation; generic-vs-project-specific is sorted out incrementally — extracting generic patterns into these skills and leaving project-specific values in each consumer's local skills. Platform-capability skills are now authored generically here directly.

## Supported harnesses & the consumption model

**Three frontmatter fields decide where a skill goes and who gets it** (browsable inventory: [`docs/CATALOG.md`](docs/CATALOG.md)):

- **`tier`** — `concept` (platform-generic patterns) vs `subject` (about a specific tool/product). Project-specific values never live here — they go in the consumer's **local** overlay.
- **`requires`** — the runtime capability the skill's guidance operates: `[]` (portable — works on a bare repo), `mcp:<group>` (a federated MCP capability granted via the consumer's virtual key), `cluster` (live cluster/platform access), or `external:github|web` (public platforms). This is the axis onboarding profiles and doctor checks filter on.
- **`audience`** — `[crew]` (the Claude Code / pi.dev role harnesses) or `[crew, persona]`. Skills with `persona` form the **OpenClaw consumption slice**, generated into [`slices/openclaw.txt`](slices/openclaw.txt); the gateway install consumes that file, so the slice cannot drift from frontmatter.

**Operator vs consumption — the key OpenClaw distinction.** Some skills are *about* OpenClaw but are for whoever **builds/tunes** a gateway (a Claude Code or pi.dev dev): `openclaw-platform-operations` (config model, Tool Search, rollout), `openclaw-agent-tuning` (identity layers). These are **operator skills** — they are **not** installed into OpenClaw agents. The **consumption slice** (below) is the opposite: skills an OpenClaw agent loads to *use* the platform.

## Platform capabilities — what these skills enable, per harness

| Capability | Skill(s) | Claude Code | pi.dev | OpenClaw agents |
|-----------|----------|:---:|:---:|:---:|
| **Shared knowledge base** (search / read / contribute) | `knowledge-base-access`, `memory-substrate`, `vault-tools` | ✓ | ✓ | ✓ *(slice: `knowledge-base-access`)* |
| **Agent-local memory** (private recall) | `knowledge-base-access`, `memory-substrate` | ✓ | ✓ | ✓ *(slice: `knowledge-base-access`)* |
| **Web search** | `searxng-search` | ✓ | ✓ | ✓ *(slice)* |
| **Image generation** | `comfyui` | ✓ | ✓ | ✓ *(slice)* |
| **Browser** (rendered pages, screenshots, interaction) | `browser` | ✓ | ✓ | — |
| **Code intelligence** (SAST, AST/structural, LSP) | `codeintel` | ✓ | ✓ | — |
| **Cluster ops** (ArgoCD reads + GitOps patterns) | `argocd-deployment-patterns` | ✓ | ✓ | — |
| **Secrets / credentials** | `secret-management-patterns` | ✓ | ✓ | — |
| **LiteLLM / MCP federation** | `litellm-routing-model` | ✓ | ✓ | — |
| **Voice** (STT/TTS wiring — channel-level, not an agent tool) | `voice` | ✓ | ✓ | — |
| **Planning · review · orchestration** | `plan-*`, `pr-review-checklist`, `orchestration-patterns`, seam skills | ✓ | ✓ | — |
| **Build / tune OpenClaw** (operator) | `openclaw-platform-operations`, `openclaw-agent-tuning` | ✓ | ✓ | — |

*✓ (slice)* = part of the OpenClaw **consumption slice**. The machine-readable slice is [`slices/openclaw.txt`](slices/openclaw.txt), generated from `audience` frontmatter (currently `searxng-search`, `comfyui`, `knowledge-base-access`); `memory-substrate` and `vault-tools` are crew-side references, not slice members. Actual availability of a capability at runtime also depends on the consumer's LiteLLM VK access groups (see `litellm-routing-model`) — the skill is the guidance; the VK grants the tools.

## What's in the box

**8 role agents**, single-sourced in `roles/<role>/` (shared `body.md` + per-runtime frontmatter + optional runtime-context appendix) and rendered by `scripts/render_roles.py` into `agents/*.md` (Claude format) and `pi-agents/role-*.md` (pi format): `lead`, `triage`, `investigator`, `researcher`, `responder`, `librarian`, `reviewer`, `implementer`. (Not used by OpenClaw.) Edit `roles/`, never the rendered trees — CI fails on drift.

**40 skills** (`skills/<name>/SKILL.md`), each carrying schema-v2 frontmatter — `tier`, `requires`, `audience` — with the full inventory generated into [`docs/CATALOG.md`](docs/CATALOG.md). There is deliberately no `project` tier — deployment-specific skills (node IPs, one cluster's topology) belong in the consumer's **local** repo. In-skill residue is still being generalized backward incrementally.

## Install

### Claude Code

Enable the plugin in `.claude/settings.json` (or `~/.claude/settings.json` for all your projects):

```json
{
  "extraKnownMarketplaces": {
    "harmony-crew": { "source": { "source": "github", "repo": "ductiletoaster/harmony-crew" }, "autoUpdate": true }
  },
  "enabledPlugins": { "harmony-crew@harmony-crew": true }
}
```

No `ref` ⇒ tracks the latest release on `main` (`autoUpdate` pulls it on startup). The project keeps its own `.claude/skills/` + `.claude/agents/` overlay, which shadows foundation entries when names collide.

### pi.dev

In `.pi/settings.json` — pin the tag for reproducible builds:

```json
{ "packages": ["npm:pi-subagents@0.28.0", "git:github.com/ductiletoaster/harmony-crew@v0.7.0"] }
```

The project adds its own `.pi/skills/` + `.pi/agents/` overlay; pi walks it from cwd to git root before the package.

### OpenClaw

OpenClaw agents run a different runtime (ClawHub skills + persona workspace files), so they don't load the plugin/package — instead the **consumption slice** is installed into the gateway's managed skills dir. The gateway's `init-skills` step clones harmony-crew (pinned tag) and installs the slice via OpenClaw's native installer:

```sh
# init container (a GH token is needed only for a PRIVATE foundation repo; mount it init-only)
git clone --depth 1 -b v0.7.0 https://<token>@github.com/ductiletoaster/harmony-crew /tmp/hc
while read -r s; do
  openclaw skills install /tmp/hc/skills/$s --global --as $s      # → ~/.openclaw/skills (auto-loaded)
done < /tmp/hc/slices/openclaw.txt
```

Then per-agent visibility is set with the gateway's `agents.list[].skills` allowlist. harmony-crew's `SKILL.md` frontmatter (`tier`/`category`) is ignored by OpenClaw — the file installs and loads as-is. Worked example: `ductiletoaster/harmony`'s `openclaw-{agents,companions}.yaml`.

## Versioning

One semver line drives all consumers. Claude Code re-fetches only when `plugin.json`'s `version` changes, so **every PR that touches `skills/`, `agents/`, `pi-agents/`, or `templates/` bumps the version in the PR itself** (usually the patch; set minor/major explicitly when warranted) — enforced by the `version-bump` check in [`.github/workflows/ci.yml`](.github/workflows/ci.yml). On merge, [`.github/workflows/release.yml`](.github/workflows/release.yml) tags the merged version — tag-only; it pushes nothing to `main`. Keep `plugin.json` == `package.json` == git tag `vX.Y.Z`. **Claude Code** tracks `main` (always latest); **pi.dev** and **OpenClaw** pin the tag (reproducible) — bump the pin to update.

## Onboarding — the `onboarding` skill

Installing the foundation gives a project the agents + skills, but not an entry file — agent *behavior* is driven by a repo-local `AGENTS.md` per project. The [`onboarding`](skills/onboarding/SKILL.md) skill applies the foundation's opinion to a project — ask an agent to *onboard this project to harmony-crew*:

- **New project** → generates `AGENTS.md` from [`templates/AGENTS.md`](templates/AGENTS.md), inferring what it can.
- **Existing project** → audits `AGENTS.md`/`CLAUDE.md`, routes delegation to the foundation's agents, and **moves facts/conventions out of the entry file into local skills**.
- **Re-runnable** as the project grows. If the project runs **OpenClaw**, onboarding also flags wiring the gateway's consumption-slice install (see the OpenClaw install above).

**Merge-don't-replace**: the foundation supplies the behavioral spine; the project fills its specifics. Worked example: [Harmony's filled `AGENTS.md`](https://github.com/ductiletoaster/harmony/blob/main/AGENTS.md).

## Catalog scope — foundation vs overlay

The dividing test is **"no project context baked in"** — not width. A single-language convention skill is fine in foundation if any project benefits; a skill that binds to a specific project's vault, gateway, cluster, secret paths, or domains is **not** — it belongs in that project's overlay.

## Layout

```
harmony-crew/
├── roles/<role>/                   # SINGLE SOURCE for the 8 role agents (body + per-runtime frontmatter)
│   └── expected-local-skills.txt   # local-skill slots a consumer supplies in its overlay
├── skills/<name>/SKILL.md          # one tree → all three harnesses read it (schema-v2 frontmatter)
├── agents/*.md                     # RENDERED Claude subagent files (do not edit; not used by OpenClaw)
├── pi-agents/role-*.md             # RENDERED pi-subagents files (do not edit)
├── slices/openclaw.txt             # GENERATED OpenClaw consumption slice (audience: persona)
├── docs/CATALOG.md                 # GENERATED skill inventory
├── scripts/render_roles.py         # role renderer; --check is the CI drift gate
├── scripts/gen_catalog.py          # slice + catalog generator; --check in CI
├── scripts/check_skills.py         # schema-v2 frontmatter validator
├── scripts/check_skill_refs.py     # every skill ref in agent bodies must resolve
├── package.json                    # pi package manifest
└── .claude-plugin/
    ├── plugin.json                 # Claude plugin manifest
    └── marketplace.json            # this repo doubles as its own marketplace
```

## First consumer

`ductiletoaster/harmony` consumes this foundation across **all three harnesses** — Claude Code + pi.dev run the crew roles; its OpenClaw gateways install the consumption slice — and layers its homelab-specific skills/roles on top. The reference example of the overlay model.
