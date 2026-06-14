---
name: seam-alert-routing
description: How to route a detected seam crossing — who decides, the flag-don't-block posture, and routing by detection context. Generic mechanism; the seams in scope come from the project recipe (recipe.seams). Load when a seam crossing is detected and needs to be surfaced.
category: boundary
durability: durable
---

## Who owns seam decisions

**The operator** is the primary owner and holds the final decision on every seam crossing. **Lead** co-enforces: it flags crossings in diffs and during agent execution but does not unilaterally approve them.

Neither reviewer nor implementer has authority to approve a seam crossing. They detect and flag; the operator decides.

## Response posture: flag, don't block

The posture is lighter-touch. A detected crossing of a `recipe.seams` entry:
- Is flagged immediately and clearly
- Does not automatically block execution or PR merge
- Routes to the operator for a decision

This keeps work moving while ensuring crossings don't go unnoticed.

## Routing by detection context

### Detected in a PR diff (reviewer)

1. Post a PR comment with the seam finding (format in `seam-detection`)
2. Mark the finding as **Required**
3. Surface it to the operator (mention / assignment per the project's tracker)
4. Do not approve the PR until the operator signs off

### Detected during autonomous execution (lead)

1. Log the crossing in the plan's delta record (see `delta-handling`)
2. Surface it to the operator on the triggering work item
3. Pause the affected phase — do not advance until the operator responds
4. Other independent phases may continue

### Detected in a scheduled sweep (investigator)

1. File a work item under the project's ops domain label
2. Title: `[seam] <seam-name>: <description of crossing>`
3. Body: what was detected, where, what the risk is
4. Do not auto-remediate — seam crossings are operator decisions

## Escalation format

```
**Seam crossing — requires operator review**

Seam: <seam name from recipe.seams>
Detected by: <reviewer / lead / investigator>
Location: <PR / issue / file path>
What crossed: <one sentence>
Risk: <one sentence on potential impact>

Operator — please advise before proceeding.
```

## After the operator's decision

- **Approved:** record the approval in the plan delta log or PR thread; execution continues
- **Rejected:** revert the crossing; raise a delta if the original task can't be completed without it
- **Deferred:** note the deferral; create a follow-up item for the seam discussion

All decisions are recorded. Don't let seam crossings resolve silently.

## Project values come from the recipe

- `recipe.seams` — the registry that defines which alerts count as seam crossings and therefore escalate to the operator rather than being handled autonomously. This skill routes; it does not enumerate seams.
- The operator is the fixed sign-off authority; never hard-code a project-specific name or handle. Use the project's tracker for mentions/assignment.
- Foundation roles (lead / reviewer / implementer / investigator) are fixed; never substitute a project-specific role name.
