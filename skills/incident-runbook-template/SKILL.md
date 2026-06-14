---
name: incident-runbook-template
description: Standard structure for incident reports and ops-sweep findings — symptom → diagnosis → fix → verification. Generic mechanism; the read-path diagnostic tools are project-specific (the project's active tools). Load when investigator is producing a finding, writing a runbook, or filing a work item for a degradation.
category: process
durability: cross-cutting
---

## Incident report structure

Every finding from investigator or an ops sweep uses this structure:

```
## Incident: <short title>

**Severity:** Low / Medium / High / Critical
**Status:** Active / Monitoring / Resolved
**Detected:** <timestamp>

### Symptom
Observable behaviour. What is the system doing (or not doing)?

### Where
Component, namespace, node, or service. Be specific.

### Diagnosis
Root cause or most likely cause. If unknown, state the leading hypothesis and what would confirm it.

### Blast radius
What else is affected or at risk? Downstream dependencies, user-facing impact.

### Fix / recommended action
What should happen next. Not implementation instructions — the action to take.

### Verification
How you confirm the fix worked — the specific checkable signal that the symptom is gone and the component is healthy.

### Timeline
- <timestamp>: symptom first observed
- <timestamp>: investigation started
- <timestamp>: root cause identified
- <timestamp>: remediation applied / escalated
```

## Work-item conventions for findings

When filing a work item for a persistent degradation:

- **Title:** `[ops] <component>: <symptom>`
- **Label:** the project's ops domain label
- **Body:** use the incident report structure above
- **Deduplicate:** search open items before filing. If one already exists, add a comment with updated observations rather than opening a duplicate.

## Ops-sweep output format

For scheduled health sweeps (even clean ones):

```
## Ops Sweep — <date>

**Result:** Clean / <N> issues found

### <subsystem, per active project tool>
- <resource>: Healthy ✓
- <resource>: Degraded — <reason>

### Issues filed
- #<ref>: <title>
```

A clean sweep with no issues still produces output. Silence is not confirmation. The set of subsystems swept is determined by which tools the project uses (gitops, secrets, exec, …) — sweep each active surface.

## Diagnostic read paths

Use the **read-path tools provided by the project's active tools** — don't assume any specific tool is present.

- The project's gateway tool federates the read-path tools for the other tools; reach a tool's diagnostics through it where configured.
- The project's gitops tool (its `tool-<module>` skill) provides application/sync status read tools.
- The project's secrets tool provides sync-status checks for its secret resources.
- The exec / compute substrate provides node and workload state.
- Fall back to the platform's native CLI only when the tool's read surface is unavailable.

Each `tool-<module>` skill documents its own read surface and the exact tool/command names — consult the active tool, not a fixed list.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, the protected-seam registry, …)
are project-specific. The consuming project supplies them — in its own overlay skills or the
agent's working context. This skill is the generic pattern.

- The project's configured tools (gitops/secrets/memory/gateway as applicable) — which subsystems exist, and the read-path tool/command names used for diagnosis. The report *template* is fixed; the *tools* that populate it are the project's active tools.
- The ops domain label and the work-item tracker come from the project.
- Foundation role names (investigator) are fixed; never substitute a project-specific role.
