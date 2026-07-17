---
name: onboarding
description: Onboard a project to the harmony-crew foundation, or re-audit one that has drifted. Generates a new AGENTS.md, or refactors an existing AGENTS.md/CLAUDE.md, to the foundation's behavioral patterns — delegation to the shared agents, the platform↔local bridge, tripwires, fallback — and moves facts/conventions OUT of the entry files INTO local skills. Re-runnable as the project evolves to keep the entry files behavioral. Use when adopting the foundation, scaffolding a new repo, or when AGENTS.md/CLAUDE.md has accreted facts and conventions.
tier: concept
---

# Onboarding

harmony-crew is an **opinionated** foundation — like the Karpathy guidelines, it takes a stance on how agents should work, and this skill *shapes a project to match it*. It **generates** an `AGENTS.md` for a new project, **audits and refactors** an existing one, and is meant to be **re-run** as the project grows so the entry files don't drift back toward fact-stuffing.

## The stance (what "good" looks like)

1. **Entry files drive behavior; skills carry facts.** `AGENTS.md` / `CLAUDE.md` hold *behavior* — delegation, routing, posture, planning, memory, the platform↔local bridge, tripwires, fallback. Infrastructure facts, conventions, credentials, and command catalogs belong in **local skills** (`.claude/skills/`). A fact sitting in the entry file is a bug to fix.
2. **Delegate by default** to the foundation's roles — `lead`, `triage`, `investigator`, `researcher`, `implementer`, `reviewer`, `librarian`, `responder`. The entry file's routing table is what makes delegation automatic instead of an afterthought.
3. **Merge-don't-replace.** The foundation supplies the behavioral spine; the project fills only its specifics (ask-list, tripwires, local-skills map, verification commands, repo). The canonical shape is [`templates/AGENTS.md`](../../templates/AGENTS.md).
4. **Trigger vs detail.** A silent landmine's *trigger* lives always-on (a Tripwire line + an imperative skill `description`); its *detail* lives in the skill, loaded on demand. Never duplicate the detail into the entry file.
5. **Platform is an enhancement, not a prerequisite.** Agents degrade gracefully when the corpus / gateway / cluster is unreachable (the Fallback section). Onboarding must not assume the platform is wired before value is delivered.

## Procedure

### 1. Assess
- Is the foundation installed? (`.claude/settings.json` plugin entry / `.pi/settings.json` package referencing `harmony-crew`.) If not, point the operator at the README *Install* steps first.
- Inventory the entry files: is there an `AGENTS.md`? a `CLAUDE.md`? Read what's in them.
- Note what the foundation offers that the project isn't using yet — the 8 shared roles, the platform skills.

### 2a. New project (no AGENTS.md) → generate
- Start from `templates/AGENTS.md`.
- Fill what you can **infer** from the repo: verification commands (`package.json` / `pyproject.toml` / `Makefile`), the remote URL (`git remote`), the stack. Leave the judgment slots (ask-list, tripwires, local-skills map) marked for the operator **with concrete suggestions**, not blanks.
- Add a one-line `CLAUDE.md` (`@AGENTS.md`) if this is a Claude Code project.

### 2b. Existing entry files → audit + refactor
Walk every section of `AGENTS.md` (and `CLAUDE.md`) and classify it:
- **Behavior** (delegation, posture, planning, memory, the bridge, tripwires, fallback) → keep; add any of these that are missing, from the scaffold.
- **Facts / conventions** (infra tables, IPs, domains, credential paths, command catalogs, service/app inventories, named conventions) → **propose moving each into a local skill** — a new `.claude/skills/<name>.md`, or an existing one — leaving only a behavioral *pointer* in the entry file.
- **Accretion** (changelogs, "recent changes", duplicated conventions) → propose removal; git history is the record.
- **Landmines** → for every convention that fails *silently* when violated, ensure (a) a Tripwire line in `AGENTS.md`, and (b) the owning skill's `description` names the trap + its consequence imperatively, so the skill loads reliably.

### 3. Recommend, then apply
Present a short plan first — *what moves to skills, what's added, what's removed* — then apply it. Moving content into skills is a real edit; confirm destructive removals with the operator. The entry file should come out **shorter** than it went in.

### 4. Re-run as the project evolves
This skill is idempotent. Run it again whenever the entry files have grown — a convention crept in, a new landmine appeared, a new local skill is warranted. Each pass nudges the project back to the rule: *behavior in the entry file, facts in skills*.

## Done when (measure the outcome; don't gate it)

- `AGENTS.md` is short and behavioral; the facts are in skills.
- Delegation routes to the foundation's roles.
- Every silent landmine has a Tripwire + an imperative skill `description`.
- Re-running the skill surfaces fewer and fewer changes over time.

**Worked example:** [Harmony's filled `AGENTS.md`](https://github.com/ductiletoaster/harmony/blob/main/AGENTS.md) — the foundation's first consumer.
