---
name: tool-vault-substrate
description: Operating the agent memory substrate — a markdown vault with frontmatter, read AND written through the vault_* MCP surface. Load this when the project uses the vault memory substrate.
---

Generic memory-substrate operating pattern — this is the owner's durable memory tool. A vault of
markdown notes (frontmatter + body) reached entirely through an MCP surface. Load this when the
project uses the vault memory substrate. The project provides the MCP prefix (env vars, mounted
secrets, or its overlay) — never hard-code it.

> The federated MCP surface depends on `tool-litellm` (the gateway). Load that module first; the
> `vault_*` calls below route through the gateway's `/mcp` endpoint.

## Surfaces

Both reads **and** writes go through the MCP surface — there is no CLI. The vault is a plain store
(not a reconciler), so writing is a direct tool call, not a gated mutation.

- **Read** — `vault_search`, `vault_readNote`, `vault_getNote`, `vault_getBacklinks`,
  `vault_findByTag`, `vault_findByIssue`, …
- **Write** — `vault_writeNote` (emit + auto-index), `vault_editNote`, `vault_updateFrontmatter`,
  `vault_addTags`, `vault_invalidate`, `vault_extractFleetingFromTranscript`, …

## Habits — recall before, persist after

These are the substrate's reason to exist; adopt them as normal operation.

**Pre-Task Recall** — before any non-trivial task, sweep the substrate before reaching for
external sources:

```
vault_search(query=<task_description>, mode="semantic", limit=5)
```

If semantic misses, retry `mode="keyword"` for exact terms. Both are best-effort — continue if
empty. Call `vault_recordRetrieval(path)` on every note you actually read, to keep the
stale/orphan corpus-health signal honest.

**Post-Session Persistence** — at the end of a session, capture durable learnings:

```
vault_extractFleetingFromTranscript(messages=<session_messages>, source_agent="<your_role>")
```

It asks a model for 0–5 durable facts and writes each as a `kind: fleeting` note. Best-effort —
log and continue on failure. For curated knowledge worth keeping permanently, write directly with
`vault_writeNote(kind="<runbook/decision/architecture/...>", ...)`.

## Write pattern

```
vault_writeNote(
  kind="research",        # REQUIRED — see Kinds
  type="person",          # optional structural shape — see Types
  title="<descriptive title>",
  body="<structured content>",   # if None, the vault auto-fills a per-kind template
  tags=["domain:infrastructure", "project:<x>"],
  recommendation="...",   # REQUIRED when kind=research
  source_agent="<your_role>",
  issue=42,
  valid_until="2026-12-31",
)
→ {note_path, filename, id, index_status, lint_warnings, ...}
```

Required fields: `kind`, `title`, `source_agent`, `tags` (≥1). `recommendation` is required only
when `kind=research`. `vault_writeNote` **auto-indexes** on emit — no separate index call in
normal flow. Notes auto-route by kind (`fleeting` → `fleeting/`, others → `notes/`).

## Two-axis schema — `kind` + `type`

| Axis | Required? | Drives | Values |
|------|-----------|--------|--------|
| `kind` | yes | directory routing, body template, lifecycle role | 10-value enum below |
| `type` | optional | projections / structural-shape filtering | 5-value enum below |

### Kinds (10-value enum)

| Kind | Purpose | Body template (auto when body=None) |
|------|---------|-------------------------------------|
| `note` | Evergreen general knowledge | Free-form (body required) |
| `fleeting` | Unprocessed capture / inbox | Free-form (body required) |
| `research` | Option analysis, evaluations | Context → Options → Recommendation → Open questions |
| `runbook` | Operational procedure | Symptoms → Diagnosis → Fix → Verification |
| `decision` | Explicit ADR | Context → Decision → Alternatives → Consequences |
| `architecture` | System design | Problem → Architecture → Trade-offs → Out of scope |
| `convention` | Coding / platform standard | Scope → Rules → Examples → Exceptions |
| `review` | PR / spec / vault review | Scope → Findings → Recommendation → Action items |
| `credential` | Service credential doc | Service → How to obtain → Where used → Rotation |
| `agent-run` | Agent execution record | Goal → Actions → Outcome → Follow-ups |

`note` and `fleeting` are **free-form** — they reject `body=None`. The other 8 auto-inline a
per-kind template.

### Types (5-value enum, optional)

| Type | Purpose |
|------|---------|
| `concept` | Evergreen claim, one idea per note |
| `moc` | Map of Content — curated index into a topic cluster |
| `person` | Persona / individual / contact |
| `reference` | External citation, runbook reference |
| `log` | Event / observation / dated entry |

### What writeNote rejects at emit (raises)

- Empty title or empty tags list
- Unknown `kind`, `type`, or `source_agent`
- `kind=research` without `recommendation`
- `body=None` on a free-form kind (`note`, `fleeting`)
- **Tag artefacts** — numeric-only tags (issue refs) and 6-char hex (colour codes) are scanner
  false-positives and are rejected.

## Tool surface — everything under the `vault_*` namespace

The MCP prefix is project-specific (supplied by the project's gateway config); it parameterises the
namespace; the tool *names* below are the stable API.

**Read:** `vault_readNote(path)`, `vault_readNotes(paths)`, `vault_getNote(path)`,
`vault_getBacklinks(path)`, `vault_getLinks(path)`, `vault_listVault(directory?)`,
`vault_listHeadings(path, level?)`.

**Search:** `vault_search(query, mode="semantic"|"keyword", limit=10)`, `vault_findByTag(tag)`,
`vault_findByIssue(issue)`, `vault_findBrokenLinks(directory?)`.

**Write:** `vault_writeNote(...)`, `vault_editNote(path, content)`,
`vault_appendToSection(path, heading, content)`, `vault_deleteNote(path, confirm)`,
`vault_indexNote(path)`.

**Metadata:** `vault_getFrontmatter(path)`, `vault_updateFrontmatter(path, updates)`,
`vault_addTags(path, tags)`, `vault_removeTags(path, tags)`.

**Lifecycle + corpus health:** `vault_recordRetrieval(note_id)`, `vault_findOrphans(status?)`,
`vault_findStale(...)`, `vault_findExpiring(days?)`, `vault_invalidate(note_id, reason)`,
`vault_recordReviewDecision(path, decision, notes?)`, `vault_getConsolidationCandidates()`,
`vault_findSkipped()`.

**Transcript extraction:** `vault_extractFleetingFromTranscript(messages, source_agent, promote_intent=False)`.

## Conventions (project-agnostic)

- **Sweep the substrate before the web.** Prior context likely already exists; recall first.
- **`source_agent` is provenance, not a partition.** Use your own role identity; recall spans all
  writers by default.
- **When in doubt, write `fleeting`.** Cheap to capture; promotion to a permanent kind is a later,
  deliberate step.

## Everything project-specific is supplied by the project

| Need | Source |
|------|--------|
| MCP tool prefix (the `vault_*` namespace) | project-specific (the project's gateway config) |
| Backing-store / infra specifics (search engine, embedding model, promote/lint cadence) | project-specific (the project's overlay/notes) |
| `source_agent` value to attribute writes | your own role identity |

This module is the entire substrate-tool surface. To make the substrate work for a new project,
that project supplies the MCP prefix in its own overlay or context — it writes no memory skill of
its own. (Higher-level curation/librarian behaviour is a project overlay concern, not part of this
tool module.)
