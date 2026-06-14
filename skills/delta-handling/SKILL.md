---
name: delta-handling
description: How to propose, evaluate, and record plan deltas during autonomous execution. Defines the two delta classes — auto-approvable vs operator-escalated — and the recording format. Generic mechanism; seam crossings escalate against the project's protected-seam registry.
category: planning
durability: durable
---

A delta is any proposed change to a plan in progress — a task approach, scope, ordering, or acceptance criterion. Worker agents propose deltas; lead evaluates them.

## Delta lifecycle

1. Worker agent identifies an issue during task execution
2. Agent drafts the delta: what to change, why, what the risk is
3. Lead evaluates the delta against the two classes below
4. Lead auto-approves or escalates
5. Plan is updated to reflect the delta (approved or escalated)
6. All deltas recorded in the plan history — approved or not

## Auto-approvable (lead judges, no operator needed)

| Class | Description |
|---|---|
| Transient retry | Same task, same approach, no scope change. Retrying after a rate limit, network error, or flaky tool. |
| Minor task reordering | Swapping two independent tasks with no dependency between them. The outcome is identical. |
| Approach substitution within scope | Different tool or implementation technique to achieve the same stated outcome. Scope unchanged. |
| Acceptance criteria clarification | Making an acceptance criterion more specific without raising or lowering the bar. No new requirements added. |

Lead may auto-approve without pausing execution. Record the decision.

## Always escalate to the operator

| Class | Description |
|---|---|
| Scope expansion | Tasks or deliverables not in the original plan. Even if beneficial, the operator decides. |
| Rollback | Reverting work already completed. High risk of data loss or state divergence. |
| Seam crossing | Any entry in the project's protected-seam registry touched without prior flagging. See `seam-detection` and `seam-alert-routing`. |
| Downstream impact | Changes that affect another agent's assigned task or expected input. |
| Exit/completion criteria change | The definition of "done" for the plan or a phase is being altered. |

For escalations: pause execution, surface the delta clearly (what changed, why, what the risk is), wait for the operator's decision before resuming.

## Delta record format

Append to the plan's history section after every delta:

```
## Delta log

### Delta <N> — <date>
**Proposed by:** <agent>
**Type:** <auto-approvable class | escalation class>
**Decision:** Auto-approved by lead / Approved by operator / Rejected
**What changed:** one sentence describing the modification
**Why:** one sentence explaining the trigger
**Risk:** one sentence on what could go wrong
```

## Examples

**Auto-approved — transient retry:**
> Delta 1 — Worker hit an API rate limit on PR creation. Retrying same task after a backoff. Auto-approved.

**Escalated — scope expansion:**
> Delta 2 — Worker proposes adding integration tests to the PR. Integration tests were not in the original plan. Pausing — operator: expand scope or defer to a follow-up issue?

**Escalated — seam crossing:**
> Delta 3 — Worker changed a setting that touches a protected-seam-registry entry to simplify debugging. Reverting. Operator: please advise.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, the protected-seam registry, …)
are project-specific. The consuming project supplies them — in its own overlay skills or the
agent's working context. This skill is the generic pattern.

- The project's protected-seam registry. A delta that touches any entry escalates regardless of how minor it looks. This skill never enumerates the seams; they're project-specific.
- Foundation roles are fixed; the "Decision" line names lead (the evaluator) and the operator (the human owner), not a project-specific person or role.
