---
name: plan-execution
description: How Lead reads an approved plan, dispatches worker agents per its phase structure, monitors acceptance criteria and validation gates, handles deltas, and drives execution to completion. Load when executing a persisted plan in autonomous mode.
tier: concept
requires: []
audience: [crew]
---

Plan execution is Lead's primary autonomous-mode responsibility. When a plan arrives via ticket or is approved in chat, Lead owns it end-to-end.

## Reading a Plan

Before dispatching any agent:
1. Read the full plan — both the high-level checklist and the detailed spec
2. Identify the phase sequence and any parallel phases
3. Confirm all acceptance criteria are present and checkable
4. Flag any open questions that must be resolved before starting — don't proceed with ambiguous scope

## Dispatching Worker Agents

Dispatch agents per the plan's phase structure:

- **Sequential phases**: dispatch the next agent only after the previous phase's validation gate passes
- **Parallel phases**: dispatch multiple agents simultaneously; wait for all to complete before the convergence point
- **Agent selection**: match the task to the right agent role (Implementer for write work, Reviewer for review, Investigator for diagnosis, Researcher for option analysis)

For feature implementation tasks, Implementer works from the spec's plan.md:
phases execute in order, each gated by its verification criteria.

## Monitoring Execution

Track each agent's output against the phase's acceptance criteria. After each phase:
- Check that acceptance criteria are met
- Check that no protected seams were crossed without flagging (see `harmony-protected-seams`)
- Check that the validation gate condition is satisfied before advancing

## Delta Handling

When a worker agent proposes a delta (a change to the current plan):

**Auto-approve without human review:**
- Retries on transient failures — same task, no scope change
- Minor task reordering — swapping independent tasks with no dependency between them
- Approach substitution within scope — different tool to achieve the same outcome
- Acceptance criteria clarification — adding specificity without raising or lowering the bar

**Always escalate to human:**
- Scope expansion — tasks not in the original plan
- Rollback decisions — reverting work already completed
- Any seam crossing — the four protected patterns
- Changes that affect another agent's downstream task
- Exit/completion criteria changes

When escalating: pause execution, surface the delta clearly (what changed, why, what the risk is), wait for human decision before resuming.

Record all deltas — approved or escalated — in the plan's history.

## Convention Enforcement

During execution, challenge any agent output that:
- Violates Harmony platform conventions (tolerations, StorageClass, security context)
- Crosses a protected seam without flagging it
- Deviates from the plan's stated scope without raising a delta

Challenge means: surface the violation, explain why it's a problem, ask the agent to correct before proceeding. Do not silently accept non-compliant output.

## Completion

A plan is complete when:
- All acceptance criteria across all phases are met
- All validation gates have passed
- No unresolved deltas remain
- A completion summary is posted to the originating ticket or chat session

The completion summary should include: what was done, any deltas that occurred and how they were resolved, and any follow-up issues opened.
