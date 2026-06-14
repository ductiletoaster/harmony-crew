---
name: agent-platform-design
description: Designing agent capabilities and surfaces — the operator-layer vs autonomous-runtime distinction, the MCP-vs-CLI interface decision, the off-the-shelf-over-custom default, the skill-vs-agent tradeoff, and the MCP provenance contract. Load when designing a new agent capability or evaluating a platform option.
category: architecture
durability: durable
---

Generic agent-platform design framework. **This skill owns the design *decisions*** — which
surface a capability lives on, whether it's a skill or an agent, whether to build or vendor. It
is project-agnostic by construction; the only project-specific scalars (the task CLI name, the
seam registry, the runtime block) come from the recipe. Decide against these frames rather than
re-deriving them per project.

## Two surfaces — keep them distinct

| Surface | Primary caller | What lives here |
|---|---|---|
| **Operator layer** | The operator working ON the project, interactively | Agents, skills, dispatch patterns the operator drives by hand |
| **Autonomous runtime** | The in-cluster orchestrator running unattended | The `runtime:` execution platform — workflow engine, runner image, webhook dispatch |

Requirements diverge between the two. A decision made for the interactive operator layer does
not automatically transfer to the autonomous runtime, and vice versa. Name the surface a
capability targets before designing it, so a discussion never conflates "what the operator
runs" with "what the runtime dispatches". The autonomous runtime's concrete platform values
(orchestrator, namespace, runner image, workflow template) come from the recipe `runtime:`
block — see `agent-orchestration-patterns`.

## Interface boundary: MCP vs CLI

For any new capability, decide the primary caller first; the surface follows:

| Primary caller | Pattern |
|---|---|
| LLM mid-task (agents) | MCP tool first; optional CLI shim for human debug |
| Human at a terminal / cron / CI | CLI command only; no MCP unless agents also need it |
| Both | MCP is canonical; the CLI is a thin wrapper — no parallel implementation |

The MCP tool owns validation, schema, and side effects. The CLI (the project's task CLI, named
in `identity.cli`) forwards structured args and translates exit codes. Drift between the two
surfaces is a bug, not a feature.

### Off-the-shelf > custom — the strong default

Before designing a custom MCP server or wrapping a vendor in your own code, check two things:

1. Does a maintained off-the-shelf option exist? (package registries, MCP server registries,
   the vendor's own client SDK)
2. Is the vendor's own CLI / REST already shipping production-grade for this surface?

**The cost of a custom wrapper:** every upstream release can break your translation layer, every
SDK change can break your lifecycle hooks, and the wrapper's tool surface is always a subset of
what the upstream supports. **The cost of skill + CLI:** maintain one skill file that drives the
upstream's own CLI through `bash`.

**Use a custom MCP server only when:** (a) no upstream CLI/SDK exists, (b) agents need structured
tool params that `bash` can't carry safely, or (c) the operation is high-volume enough that the
proxy + JSON-RPC overhead is a measurable bottleneck. Default to **no**.

## MCP server provenance contract

If a tool appears in the `tools/list` response, an agent will eventually call it. A stub that
returns "not yet implemented" lands at the model layer as a tool failure, which the LLM may treat
as transient and retry — burning context window and operator trust.

Two rules for any MCP server you ship or vendor:

1. **No stub tools.** If an operation isn't implemented end-to-end, remove it from `tools/list`
   (or prefix the description with `[UNAVAILABLE]` so the model routes around it). Failing fast
   on the boundary beats a mid-task surprise.
2. **Capabilities advertised in `initialize` must work.** If the server advertises `resources`,
   then `resources/list` must return a well-shaped (possibly empty) array per the MCP spec — not
   "Method not found", not `{}` instead of `{"resources": []}`. The peer calls every advertised
   capability and pays a per-call timeout on each broken one.

A capability that is *not* advertised in `initialize` is permitted to be absent. The contract is:
don't advertise what you can't deliver.

## Skill vs agent tradeoff

**Behavioural specialization → skill. Operational specialization → agent.**

- Add a **skill** when you need *how to do something* but the role and tool scope don't change.
- Add an **agent** when the role genuinely requires a different operational stance OR different
  tool access (e.g. a triage role with no cluster access; a reviewer with no write access to code).

Most specialization resolves into a skill. **Agents stay small; skills grow.** A new agent
requires justification — the privilege gradient and the role's operational shape, not just a new
behaviour. (Task decomposition, result contracts, and the privilege gradient itself live in
`autonomous-agent-design`.)

## Delegation-packet semantics

When one agent hands work to another, the handoff is a self-contained packet, not a shared
transcript. Include: what was produced (artifacts, PR links, notes), what the next agent needs
that isn't obvious from the artifacts, and the acceptance criteria for the next phase. The
receiving agent should not have to read the full conversation history to act. (The trust gradient
that governs *which* agent may receive *which* packet is the privilege gradient in
`autonomous-agent-design`; the orchestration shapes are in `orchestration-patterns`.)

## Skill design guidelines

- One tight sentence in the description — this is how agents find the skill.
- Category: `domain`, `stack`, `process`, `architecture`, `planning`, or `boundary`.
- Durability: `durable` / `transitional` / `cross-cutting`.
- Content: operational and prescriptive, not aspirational.
- No `agents` field in frontmatter — agents load skills by explicit reference in their prompts.

## Capability rollout sequence

1. Design the capability (this skill — option analysis, interface decision, skill/agent tradeoff).
2. Write the skill(s) encoding the pattern.
3. Write or update the agent(s) that load the skill.
4. **Shadow** — run and observe; take no action.
5. **Draft** — produce artifacts; a human approves before publish.
6. **Autonomous** — run and publish; a human reviews asynchronously.

Never skip the shadow and draft stages for a capability that produces side effects. (The full
shadow→draft→autonomous maturity model is in `autonomous-agent-design`.)

## Capabilities that cross a protected seam

A capability that touches a boundary in the project's seam registry (recipe `seams`) needs human
sign-off before it ships autonomously, regardless of where it sits in the rollout sequence. Flag
the crossing at design time, not after implementation. The seam list is per-project and comes
from the recipe — never assume a fixed set.

## Project values come from the recipe

| Need | Source |
|---|---|
| Project task-CLI name (the CLI surface a capability forwards to) | `identity.cli` |
| The autonomous-runtime platform (orchestrator, namespace, runner, …) | recipe `runtime:` block |
| The protected-seam list a capability is checked against | recipe `seams` |
| Active tool modules a capability composes with | recipe `tools.*` |

This skill owns the design *decisions*; the recipe supplies only the project's CLI name, seam
registry, runtime block, and active tools. The frames hold across every project; the scalars vary.
