---
name: tool-argocd
description: Operating ArgoCD as an agent — read application state, sync, rollback, diagnose. Active only when the project recipe declares tools.gitops.module = argocd; reads endpoint/auth/mcp from that block.
---

Generic ArgoCD operating pattern. **Activation:** load this only when the recipe's
`tools.gitops.module` is `argocd`. Take the server endpoint, auth ref, and MCP prefix
from `tools.gitops` — never hard-code them. (A project on Flux loads `tool-flux` instead.)

## Read path — via the gateway MCP

Use the `<tools.gitops.mcp>-*` tools (e.g. `argocd-list_applications`, `argocd-get_application`,
`argocd-get_application_resource_tree`) for all read and diagnosis work. No CLI needed for reads.

## Write path — CLI only

Sync, rollback, and other mutations go through the `argocd` CLI — never the MCP, and never
`kubectl apply` in a GitOps-managed cluster:

```bash
export ARGOCD_SERVER=<tools.gitops.endpoint>
export ARGOCD_AUTH_TOKEN=$(<resolve tools.gitops.auth>)   # e.g. op read op://…/agent_token
argocd app sync <app>
argocd app rollback <app> <revision>
```

## Conventions (project-agnostic)

- Never `kubectl apply` to mutate a GitOps-managed app — let ArgoCD reconcile, or `argocd app sync`.
- Read state before acting; a degraded app may be mid-sync.
- Honour `tools.gitops.notes` for project quirks (e.g. known false-drift / ignore-difference patterns).

## Everything project-specific comes from the recipe

| Need | Source |
|------|--------|
| Server endpoint | `tools.gitops.endpoint` |
| Auth | `tools.gitops.auth` |
| Read-path MCP prefix | `tools.gitops.mcp` |
| App / overlay layout, drift quirks | `tools.gitops.notes` + `facts` |

This module is the entire ArgoCD-specific surface. To make ArgoCD work for a new project,
that project adds a `tools.gitops` block to its recipe — it writes no ArgoCD skill of its own.
