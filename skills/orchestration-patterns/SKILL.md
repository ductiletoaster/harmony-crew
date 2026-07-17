---
name: orchestration-patterns
description: Parallel and sequential workflow composition, convergence handling, and multi-agent coordination for Lead. Load when Lead is designing or executing a multi-agent plan.
category: planning
durability: durable
tier: concept
---

## Workflow shapes

### Sequential

Each phase depends on the previous phase's output. No parallelism.

```
Triage → Researcher → Lead (plan) → Implementer → Reviewer → Ship
```

Use sequential when:
- Later phases need results from earlier phases
- Resource contention makes parallelism impractical
- The risk of divergent outputs is high

### Parallel

Multiple agents work independently. Convergence waits for all to complete.

```
          ┌─→ Implementer (component A) ─┐
Lead ─────┤                              ├─→ Reviewer → Ship
          └─→ Implementer (component B) ─┘
```

Use parallel when:
- Work items are genuinely independent (no shared state, no ordering dependency)
- The plan explicitly expresses parallelism
- Sandboxing is confirmed (git worktrees, separate namespaces)

### Mixed

Sequential phases with parallel implementation inside, then sequential reconvergence:

```
Phase 1 (sequential) → Phase 2 (parallel Implementers) → Phase 3 (sequential Reviewer)
```

Most non-trivial plans are mixed.

## Expressing parallelism in plans

Plans must express parallelism and convergence explicitly:

```markdown
## Phase 2: Implementation (parallel)
Phases 2A and 2B can run concurrently.

### Phase 2A — Python changes
- Agent: Implementer
- Acceptance criteria: `uv run pytest` passes

### Phase 2B — K8s manifest changes
- Agent: Implementer
- Acceptance criteria: `kubectl kustomize build` passes

## Phase 3: Review (begins only when 2A and 2B are both complete)
- Agent: Reviewer
```

Never imply parallelism — state it. Never imply convergence — state the condition.

## Convergence handling

Before advancing from a parallel phase:
- Collect outputs from all parallel agents
- Verify each agent's acceptance criteria are met
- Check for conflicts (same file modified by two agents)
- If conflicts exist: resolve before advancing — this is a delta requiring human review

## Sandboxing parallel Implementers

Multiple Implementers writing code simultaneously need isolation:
- Each Implementer works on a separate git branch
- No shared mutable state in the workspace
- PRs are independent — they can be reviewed and merged separately
- Lead coordinates merge ordering if there are dependencies

## Inter-agent handoff

When handing off between agents (sequential), include in the handoff:
1. What was produced (artifacts, PR links, vault notes)
2. What the next agent needs to know (context that isn't obvious from the artifacts)
3. What the acceptance criteria are for the next phase

Don't assume the next agent will read the full conversation history. Be explicit.

## Stall detection

If a worker agent hasn't produced output within the expected window:
1. Check for a transient failure (exit 75) — retry if so
2. Check for a structural failure (exit 1) — escalate to human
3. Check for a missing dependency (the agent is waiting on input that hasn't arrived)

Do not let a stalled agent block a plan indefinitely without surfacing it.
