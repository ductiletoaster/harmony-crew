---
name: plan-execution
description: How lead reads a plan, dispatches worker agents, sequences and parallelizes phases, handles convergence, and drives execution to completion. Generic mechanism; the protected-seam registry flagged during execution is project-specific (supplied by the project).
category: planning
durability: durable
---

Plan execution is lead's primary autonomous-mode responsibility. When a plan arrives via ticket or is approved in chat, lead owns it end-to-end.

## Reading a plan

Before dispatching any agent:
1. Read the full plan — both the high-level checklist and the detailed spec
2. Identify the phase sequence and any parallel phases
3. Confirm all acceptance criteria are present and checkable
4. Flag any open questions that must be resolved before starting — don't proceed with ambiguous scope

## Dispatching worker agents

Dispatch agents per the plan's phase structure:

- **Sequential phases** — dispatch the next agent only after the previous phase's validation gate passes
- **Parallel phases** — dispatch multiple agents simultaneously; wait for all to complete before the convergence point
- **Agent selection** — match the task to the right foundation role (implementer for write work, reviewer for review, investigator for diagnosis, researcher for option analysis)

For feature implementation, implementer works from the plan's phases in order, each gated by its verification criteria.

## Sequencing and parallelization

- Express parallelism only where the plan states it — independent work items, no shared mutable state, no ordering dependency
- Parallel implementers need isolation (separate branches/workspaces); coordinate merge ordering if there are dependencies
- A phase that consumes a prior phase's output is sequential by definition — don't parallelize across a real dependency

## Convergence

Before advancing from a parallel phase:
- Collect outputs from all parallel agents
- Verify each agent's acceptance criteria are met
- Check for conflicts (e.g. the same file modified by two agents)
- If conflicts exist, resolve before advancing — a merge conflict between agents is a delta requiring operator review (see `delta-handling`)

## Monitoring execution

Track each agent's output against the phase's acceptance criteria. After each phase:
- Check that acceptance criteria are met
- Check that no entry in the project's protected-seam registry was crossed without being flagged — see `seam-detection`
- Check that the validation gate condition is satisfied before advancing (see `plan-validation`)

## Delta handling

When a worker agent proposes a delta (a change to the current plan), route it per `delta-handling`: auto-approve the bounded in-scope classes, escalate scope expansions, rollbacks, downstream-impacting changes, completion-criteria changes, and **any crossing of a protected-seam-registry entry**. When escalating, pause the affected phase, surface the delta clearly, and wait for the operator's decision before resuming. Independent phases may continue.

Record every delta — approved or escalated — in the plan's history.

## Convention enforcement

During execution, challenge any agent output that:
- Violates the project's platform conventions (scheduling constraints, StorageClass, security context — all project-specific, supplied by the project)
- Crosses a protected-seam-registry entry without flagging it
- Deviates from the plan's stated scope without raising a delta

Challenge means: surface the violation, explain why it's a problem, ask the agent to correct it before proceeding. Do not silently accept non-compliant output.

## Completion

A plan is complete when:
- All acceptance criteria across all phases are met
- All validation gates have passed
- No unresolved deltas remain
- A completion summary is posted to the originating ticket or chat session

The completion summary includes: what was done, any deltas that occurred and how they were resolved, and any follow-up issues opened.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, the protected-seam registry, …) are project-specific. The consuming project supplies them — in its own overlay skills or the agent's working context. This skill is the generic pattern.

- The project's **protected-seam registry** — the seams whose crossings get flagged during monitoring and force a delta escalation. This skill never hard-codes a seam.
- The project's **platform conventions** — challenged during convention enforcement.
- Foundation roles (lead / implementer / reviewer / investigator / researcher / triage) are fixed; never substitute a project-specific role name.
