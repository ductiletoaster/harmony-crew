---
name: memory-substrate
description: Entry point for Harmony's memory substrate — workstation auto-memory and the shared vault, accessed via the unified vault.* MCP surface.
category: domain
durability: durable
---

The Harmony substrate has two surfaces with one canonical MCP namespace (`vault.*`) reaching the shared one. Adopt the recall + persistence habits below as part of normal operation — they're how this project carries context between sessions and across agents.

## Surfaces

Two complementary tiers: a **shared** corpus every agent draws on, and each agent's **private, agent-local** memory. Different stores, different privacy scope — an agent conflating them looks in the wrong place.

| Tier | What it is | Scope |
|------|-----------|-------|
| **Shared vault (KB)** | Obsidian vault (markdown + frontmatter on NFS), via the `vault.*` MCP surface served by vault-mcp | Platform-wide — shared across every agent, session, and harness. The common corpus. |
| **Agent-local memory** | Each runtime's own private store — the harness supplies the mechanism: Claude Code **workstation auto-memory** (`~/.claude/projects/.../memory/`, auto-loaded at session start, written via the auto-memory protocol, not MCP); an OpenClaw agent's `memory_search`/`memory_get` index (a richer per-agent memory architecture, not just `MEMORY.md`); other harnesses their own. | **Private to one agent/runtime.** Not shared, not in the vault, not reachable via `vault_search` — and vault content is not reachable via the local search. |

**Boundary note:** the two tiers are complementary, not interchangeable — agent-local memory is an agent talking to itself; the vault is the shared corpus. Giving a surface access to the shared KB is a *separate* capability grant (an MCP access group on its VK — see `litellm-routing-model`). Each harness's local-memory specifics live in that harness's ops skill (e.g. `openclaw-platform-operations`).

The vault is the shared corpus. `source_agent` in frontmatter is recorded as provenance — who wrote a note — but it is not a partition. A pattern learned by `researcher` surfaces for `lead`, `aria`, and `claude-code` just by querying the vault without filtering on `source_agent`.

## Access surface

`vault.*` (served by vault-mcp) is the one MCP surface for the substrate. Reach for it for reads, writes, search, metadata, and lifecycle.

| Use for | Tool |
|---------|------|
| Read a note by path | `vault_readNote(path)` |
| Get note metadata + frontmatter | `vault_getNote(path)` |
| What references this note? | `vault_getBacklinks(path)` |
| Semantic / conceptual search | `vault_search(query, mode="semantic")` |
| Keyword / full-text search | `vault_search(query, mode="keyword")` |
| Find notes by tag | `vault_findByTag(tag)` |
| Find notes by GitHub issue | `vault_findByIssue(issue)` |
| Find orphans / expiring / stale | `vault_findOrphans()` / `vault_findExpiring()` / `vault_findStale()` |
| Write a structured note | `vault_writeNote(title, body, source_agent, tags, kind="…")` |
| Edit a note | `vault_editNote(path, content)` |
| Update / add frontmatter tags | `vault_updateFrontmatter(...)` / `vault_addTags(path, [tags])` |
| Mark a note superseded | `vault_invalidate(path, reason)` |
| Record retrieval signal | `vault_recordRetrieval(path)` |
| **Extract durable facts from a chat transcript** | `vault_extractFleetingFromTranscript(messages, source_agent)` |

See `vault-tools` for the full tool reference, kind/type schema, and per-kind templates.

## Write routing — which layer for what

| Material | Surface | Tool |
|----------|---------|------|
| "I learned the user prefers X" / "this approach failed last time" | vault `fleeting/` | `vault_writeNote(kind="fleeting", ...)` or capture-by-extraction below |
| Operator feedback / project state / coding behaviour rules | workstation auto-memory | Auto-memory protocol (workstation-only) |
| Durable extractions from a chat session | vault `fleeting/` | `vault_extractFleetingFromTranscript(messages, source_agent)` |
| Runbook, decision, architecture note, convention, research, credential doc | vault `notes/` | `vault_writeNote(kind="<runbook/decision/architecture/...>", ...)` |
| Capture I'm not sure about yet | vault `fleeting/` | `vault_writeNote(kind="fleeting", ...)` |
| Promote-intent signal (review later) | vault `fleeting/` + `promote_intent: true` | Set frontmatter on the write; the daily promote-runner picks it up |

When in doubt: **fleeting**. The promote-runner CronJob aggregates flagged candidates daily for operator triage.

## Read routing — pick the surface that fits the query

When starting any non-trivial task, sweep the substrate before reaching for external sources. Pick the tool that matches the query shape:

1. **Prior context across all writers** → `vault_search(query, mode="semantic")`. Spans the corpus regardless of `source_agent`.
2. **Specific note** → `vault_readNote(path)` or `vault_getNote(path)`.
3. **Metadata-shaped query** ("orphans", "by issue N", "stale") → `vault_findOrphans()` / `vault_findByIssue(...)` / `vault_findStale()`.
4. **What references this?** → `vault_getBacklinks(path)`.
5. **External** (web, GitHub, docs) only when the substrate is insufficient.

Call `vault_recordRetrieval(path)` on every note you actually read — it feeds the stale/orphan signal that keeps the corpus honest.

## Pre-Task Recall pattern

Before starting any non-trivial task:

```
vault_search(query=<task_description>, mode="semantic", limit=5)
```

If the search misses, try `mode="keyword"` for exact terms. Both are best-effort — continue if they return empty.

## Post-Session Persistence pattern

At the end of any research or task session, capture durable learnings:

```
vault_extractFleetingFromTranscript(messages=<session_messages>, source_agent="<your_role>")
```

The tool calls the local LLM, extracts 0–5 facts, and writes each as a `kind: fleeting` note via `vault_writeNote`. Best-effort — log and continue if it fails.

For curated knowledge worth keeping in the permanent corpus, write directly:

```
vault_writeNote(title=..., body=..., source_agent="<your_role>",
                tags=[...], kind="<runbook/decision/architecture/...>")
```

`vault-tools` skill owns the two-axis `kind` + `type` schema and per-kind templates.

## Agent IDs (provenance)

`source_agent` on every vault write is **provenance metadata** — it records who wrote a note. It is not a partition. Use your own identity so the substrate stays auditable; on recall, queries span all writers by default.

| source_agent | Identity |
|--------------|----------|
| `claude-code` | Claude Code operator sessions |
| `lead` | Lead role (planning / orchestration) |
| `researcher` | Researcher role |
| `implementer` | Implementer role |
| `reviewer` | Reviewer role |
| `investigator` | Investigator role |
| `librarian` | Librarian — vault curation |
| `triage` | Triage intake |
| `aria` | Aria — OpenClaw personal assistant |
| `vesper` | Vesper — OpenClaw companion |
| `pi-web` | pi-web (cluster-side remote web interface) |

## Auth

All `vault.*` calls route through LiteLLM MCP. Agent VKs hold `mcp_access_groups: [public]` (granted via team membership — see `harmony-public` team). The VK is for LLM routing and MCP access; do not invent separate MCP credentials.
