---
name: agent-platform-design
description: Designing agent capabilities and surfaces for Harmony — interface boundary decisions, skill vs agent tradeoffs, surface naming, and the Scope 1 vs Scope 2 distinction. Load when designing new agent capabilities or evaluating platform options.
tier: concept
requires: []
audience: [crew]
---

## Two surfaces — keep them distinct

| Surface | Primary caller | Scope |
|---|---|---|
| **Scope 1 — Claude Code operator layer** | Operators (Brian) working ON Harmony | Agents, skills, dispatch patterns in `.claude/` |
| **Scope 2 — `hmy agent` autonomous runtime** | In-cluster orchestrator running AGAINST external projects (FireRisk, etc.) | Argo Workflows, Pydantic AI orchestrator, webhook dispatch |

Requirements diverge between surfaces. Design decisions made for Scope 1 don't automatically apply to Scope 2. Before the Scope 2 planning session, establish clear surface naming conventions so discussions don't conflate the two.

## Interface boundary: MCP vs CLI

For any new capability, decide the primary caller:

| Primary caller | Pattern |
|---|---|
| LLM mid-task (agents) | MCP tool first; optional CLI shim for human debug |
| Human at terminal / cron / CI | CLI command only; no MCP unless agents also need it |
| Both | MCP is canonical; CLI is a thin wrapper — no parallel implementation |

The MCP tool owns validation, schema, and side effects. The CLI forwards structured args and translates exit codes. Drift between surfaces is a bug.

### Off-the-shelf > custom — the strong default

Before designing a custom MCP server or wrapping a vendor in our own code, check two things:

1. Does a maintained off-the-shelf option exist? (npm `pi-package` keyword, MCP server registries, vendor's own client SDK)
2. Is the vendor's own CLI / REST already shipping production-grade for this surface?

Case studies tonight (2026-06-04):
- **`@0xkobold/pi-mcp` over our `pi-mcp-adapter` fork** — the upstream maintainer's design (auto-connect at extension load, no `session_start` hook) worked under pi-web's session runtime where `pi-mcp-adapter` didn't. Swapping to the off-the-shelf adapter deleted hundreds of lines we were going to have to maintain.
- **Bundled `coder` CLI over our in-house `coder-mcp`** — Coder Inc. ships a tested, versioned CLI that already implements every workspace operation (start / stop / list / show / ssh-exec / logs / templates). Our coder-mcp shipped 5 tools, one of which (`run_in_workspace`) was a stub. We retired the entire wrapper (`-600 lines`) by bundling the CLI and writing a skill that uses `bash`.

**The cost of custom MCP wrappers**: every Coder release potentially breaks our Python translation, every Pi Coding Agent SDK change can break our lifecycle hooks, and the wrapper's tool surface is always a subset of what the upstream supports. The cost of skill + CLI: maintain one skill file.

**Use custom MCP only when**: (a) no upstream CLI/SDK exists, (b) agents need structured tool params that bash can't carry safely, or (c) the operation is so high-volume that the proxy + JSON-RPC overhead is a measurable bottleneck. Default no.

## MCP server provenance contract

If a tool is in the `tools/list` response, an agent will eventually try to call it. Stubs that return "not yet implemented" land at the model layer as a tool failure, which the LLM may treat as a transient error and retry — burning context window and operator trust.

Two rules for any MCP server we ship or vendor:

1. **No stub tools.** If the operation isn't implemented end-to-end, remove it from `tools/list` (or prefix the description with `[UNAVAILABLE]` so the model can route around it). Failing fast on the boundary is better than mid-task surprise.
2. **Capabilities advertised in `initialize` must work.** If the server's `initialize` response advertises `resources`, then `resources/list` must return a well-shaped (possibly empty) array per the MCP spec — not "Method not found", not `{}` instead of `{"resources": []}`. The peer (LiteLLM, @0xkobold/pi-mcp, etc.) will call every advertised capability and pay a 30s timeout per broken one.

A capability that's *not* advertised in `initialize` is permitted to be absent. The contract is: don't advertise what you can't deliver.

## Skill vs agent tradeoff

Add a skill when: behavioral specialization is needed (how to do something) but the role and tool scope don't change.

Add an agent when: the role genuinely requires a different operational stance OR different tool access (e.g., Triage has no cluster access; Reviewer has no write access to code).

Most specialization resolves into a skill. New agents require justification.

## Skill design guidelines

- Description carries trigger language and the load cue — for skills no agent always-loads, the description is the only load path, so name the tasks and phrases that should trigger it
- `tier`: `concept` (generic pattern) vs `subject` (about a specific tool/product)
- `requires`: the runtime capability the skill's guidance operates — `[]` (portable), `mcp:<group>`, `cluster`, or `external:github|web`; onboarding profiles and doctor checks filter on this
- `audience`: `[crew]` or `[crew, persona]` — `persona` membership derives the OpenClaw consumption slice (`slices/openclaw.txt` is generated from it)
- Content: operational and prescriptive, not aspirational
- No `agents` field in frontmatter — agents load skills by explicit reference in their system prompts

## Platform tenets (durable bets)

Design new capabilities against these durable bets:
- Kubernetes as the delivery strategy
- Talos Linux / Sidero Omni on Proxmox as the substrate
- Agent-oriented platform direction (implementations reshape; direction holds)
- Python as the primary implementation language
- Open source first, permissive license preferred

Capabilities tied to transitional services (human-facing apps, specific AI frameworks) get lighter investment.

## Capability rollout sequence

1. Design the capability (this skill — option analysis, interface decision, skill/agent tradeoff)
2. Write the skill(s) encoding the pattern
3. Write or update the agent(s) that load the skill
4. Shadow mode: run and observe, no action taken
5. Draft mode: produce artifacts, human approves before publish
6. Autonomous: run and publish, human reviews asynchronously

Never skip the shadow and draft stages for capabilities that produce side effects.

## Knowledge corpus integration

Every significant capability should be documented in the vault:
- Design decisions → `kind: research` note
- Operational procedures → `kind: runbook` note
- Agent execution records → `kind: agent-run` note (automatic from orchestrator)

The vault is the institutional memory. Skills encode the how; vault notes encode the why and what happened.
