---
name: seam-detection
description: How to identify protected seam crossings in diffs and proposed changes. Defines what to look for in each seam and how to report a finding. Load when Reviewer is scanning a diff or Lead is monitoring agent output for seam violations.
category: boundary
durability: durable
---

A seam crossing is any change that touches one of the four protected patterns without the crossing having been explicitly flagged by the author. The four seams are defined in `harmony-protected-seams`. This skill defines how to detect them in practice.

## Detection patterns

### Seam 1 — Secret management contract

**Scan for in diffs:**
- Any `refreshInterval` value other than `"0"` on an ExternalSecret
- `deletionPolicy` changed from `Retain`
- Hardcoded secrets, tokens, passwords, or API keys (any string matching key/token/password patterns)
- ExternalSecret created without a same-PR consumer workload
- `ClusterSecretStore` reference to anything other than `onepassword`

**Shell grep (run against changed files):**
```bash
git diff HEAD~1 | grep -E '(refreshInterval|deletionPolicy|password|token|apiKey|secret)' | grep -v '#'
gitleaks detect --source . --no-git
```

### Seam 2 — Workload scheduling contract

**Scan for in diffs:**
- Deployment, StatefulSet, DaemonSet, or Job with no `tolerations` block
- `tolerations` block missing `node-role.kubernetes.io/control-plane`
- `storageClassName` changed between `harmony-runtime` and `harmony-storage` (or to a third class)
- `storageClassName: ""` used outside the shared-models static PV binding pattern

**Shell grep:**
```bash
git diff HEAD~1 -- '*.yaml' | grep -E '(storageClassName|tolerations)' 
# Then verify control-plane toleration is present in every workload
```

### Seam 3 — LiteLLM MCP access boundary

The load-bearing boundary is the **server `access_groups` ∩ team allowlist ∩ VK groups** intersection (see `harmony-protected-seams` Seam 3), not a VK-vs-MCP credential split.

**Scan for in diffs:**
- A VK's `mcp_access_groups` (or `object_permission`) changed — a consumer's opted-in capability groups widened or narrowed
- A team's allowlist (`object_permission.mcp_access_groups`) changed — the hard ceiling every member VK is capped by
- A server's `access_groups` changed in the LiteLLM proxy config `mcp_servers` block, or a new MCP server added
- A per-server `allowed_tools` allowlist removed or widened
- A group left matching zero servers, or a VK left with no groups (both fail *open* — treated as unrestricted / full-allowlist inheritance)

**Shell grep:**
```bash
git diff HEAD~1 | grep -E '(mcp_access_groups|access_groups|allowed_tools|mcp_servers|object_permission)'
```

### Seam 4 — Agent runtime contract

**Scan for in diffs:**
- Exit code values changed in orchestrator or WorkflowTemplate (any value other than 0, 75, 1)
- `AgentResult` schema fields added, renamed, or removed
- `maxDuration` cap re-added to `execute-claude` retry
- WorkflowTemplate runner image version changed without a corresponding orchestrator compatibility check
- `retryStrategy` expression changed from `exitCode == 75`

**Shell grep:**
```bash
git diff HEAD~1 -- 'orchestrator.py' '*WorkflowTemplate*' | grep -E '(exit|retry|AgentResult|maxDuration)'
```

## Reporting a seam finding

In a PR comment or review finding:

```
**Seam crossing detected — <seam name>**

File: <path>
Line: <number>
Change: <what changed>
Risk: <why this matters>
Action required: Human sign-off before merge. Tag @ductiletoaster.
```

Mark as **Required** in the review. Do not approve or suggest merge until the author acknowledges the crossing and Brian provides sign-off.

## False positives

Not every touch of a seam-related file is a crossing. Context matters:

- An ExternalSecret file modified to add a label (not touching `refreshInterval` or `deletionPolicy`) is not a crossing
- A comment change in `orchestrator.py` is not a crossing
- A new test that imports from `AgentResult` but doesn't change its schema is not a crossing

When in doubt, flag it. A false positive costs a brief discussion. A missed crossing can break production.
