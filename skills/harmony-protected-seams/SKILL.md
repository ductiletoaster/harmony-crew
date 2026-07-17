---
name: harmony-protected-seams
description: Registry of four load-bearing platform patterns that require human review before change.
category: boundary
durability: durable
---

Harmony has four protected seams — patterns that are load-bearing for platform correctness or security. These are semantic patterns, not path-bound. When any of these patterns are touched in a diff, flag it for human review. Do not block; flag.

## The Four Seams

### 1. Secret Management Contract
The 1Password → ESO → Kubernetes secret flow.

Protected patterns:
- `refreshInterval` on any ExternalSecret (must remain `"0"`)
- `deletionPolicy` on any ExternalSecret (must remain `Retain`)
- ClusterSecretStore configuration changes
- Force-sync procedure: delete the ExternalSecret and let ArgoCD recreate it — never use annotations or `refreshInterval` changes to trigger re-sync

Risk: changing these causes 1Password API rate limit cascades or silent secret loss.

### 2. Workload Scheduling Contract
The control-plane toleration and StorageClass selection model.

Protected patterns:
- Removing or modifying the `node-role.kubernetes.io/control-plane:NoSchedule` toleration from any workload
- StorageClass selection: `harmony-runtime` (NVMe, `Delete` reclaim) vs `harmony-storage` (HDD, `Retain` reclaim)

Risk: pods fail to schedule anywhere, or data lands in the wrong storage tier (wrong performance or wrong retention behaviour).

### 3. LiteLLM MCP Access Boundary
The access-group intersection that decides which MCP tools a consumer can reach.

A single bearer virtual key (VK) now carries **both** LLM routing and MCP tool scope — the old "VKs are LLM-only, MCP uses global/no-auth" split no longer holds. Tool visibility for any consumer is the intersection **server `access_groups` ∩ team allowlist (a hard ceiling) ∩ VK groups**. That intersection is the load-bearing boundary; the values live in the consumer's local skill.

Protected patterns:
- A VK's `mcp_access_groups` — the set of capability groups a consumer opts into (widens or narrows its tool surface)
- A team's allowlist (`object_permission.mcp_access_groups`) — the hard ceiling every member VK is capped by
- A server's `access_groups` in the LiteLLM proxy config `mcp_servers` block — which groups can see a given upstream
- Per-server `allowed_tools` allowlists — the only reliable way to restrict which tools a server exposes

Risk: broadening any of the three sets silently over-grants a surface (e.g. a pod gains cluster-ops or host-path tools it shouldn't). A group that matches **zero** servers is treated as UNRESTRICTED, and a VK with **no** groups inherits the team's full allowlist — both fail *open*, not closed. See `litellm-routing-model` for the mechanism and `secret-management-patterns` for the VK's credential path.

### 4. Agent Runtime Contract
Exit codes, result format, and retry behaviour in the Pydantic AI / Argo orchestration path.

Protected patterns:
- Exit codes: `0` = success, `75` = transient (retry), `1` = structural (no retry)
- Result format: structured `AgentResult` written to `/tmp/agent-result.json`
- Retry logic in `execute-claude` Argo step — tied to exit code semantics

Risk: changing exit codes or result format breaks autonomous agent reliability and Argo Workflow retry logic silently.

## Response Policy

**Flag, don't block.** When a diff touches one of these patterns, surface a comment: which seam was crossed, what the risk is, and what human review should check. Do not halt execution.

## Registry Ownership

Brian (primary). Lead agent (enforcement co-owner — flags crossings during review).

New entries require a PR with Brian's approval. Seams are named, narrow, and machine-detectable — if a proposed seam can't be described in terms of a detectable pattern, it doesn't belong in this registry.
