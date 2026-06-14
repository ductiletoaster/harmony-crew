---
name: argocd-ops
description: ArgoCD MCP tools for cluster operations — list/inspect applications, retrieve workload logs. Use for health checks, incident investigation, and deployment status.
category: ops
durability: durable
---

## When to Use

Use this skill when you need to observe cluster application state via MCP — not when writing manifests or configuring sync (see `argocd-deployment-patterns` and `k8s-kustomize-conventions`).

Primary consumers: Investigator (health sweeps, incident diagnosis), Lead (deployment verification).

## Available Tools

- `argocd-list_applications()` → list of all ArgoCD applications with health/sync status
- `argocd-get_application(name)` → full application detail — health, sync, resources, last sync time
- `argocd-get_application_workload_logs(name, container?, tail?)` → recent pod logs for an application's workloads

## Gated Operations

`sync_application` is not exposed via MCP — sync is a write operation and must use the CLI:

```
hmy deploy sync <app>
# or
argocd app sync <app>
```

This is intentional. Automated syncs go through ArgoCD's GitOps reconciler; manual syncs use the CLI with human intent.

## Common Patterns

Health sweep:
1. `argocd-list_applications()` → identify Degraded or OutOfSync apps
2. `argocd-get_application(name)` → drill into failing app for resource-level status
3. `argocd-get_application_workload_logs(name)` → check pod logs for error detail
4. Cross-reference with `kubectl` for node-level or persistent volume issues

## Auth

Routes through LiteLLM MCP. The gateway requires a LiteLLM virtual key as a Bearer token; the MCP client config supplies it (`Authorization: Bearer ${LITELLM_API_KEY}` in `.mcp.json` / pi `mcp.json`), so individual tool calls need no extra credentials.
