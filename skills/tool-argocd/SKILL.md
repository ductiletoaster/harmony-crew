---
name: tool-argocd
description: Operating ArgoCD as an agent — read application state, sync, rollback, diagnose. Active only when the project recipe declares a tools.* entry whose module = argocd; reads endpoint/auth/mcp from that entry.
---

Generic ArgoCD operating pattern. **Activation:** load this only when the recipe has a
`tools.*` entry whose `module` is `argocd` (the recipe author chooses the role key — it's
commonly `gitops`, but read the module value, not the key). Take the server endpoint, auth
ref, and MCP prefix from **that argocd entry** — never hard-code them. (A project on Flux
loads `tool-flux` instead.)

## Surfaces

- **Read path** = the gateway MCP `<entry>.mcp-*` tools (e.g. `argocd-list_applications`,
  `argocd-get_application`, `argocd-get_application_resource_tree`).
- **Write path** (sync / rollback) = the `argocd` CLI.

ArgoCD mutations are gated to the CLI/PR because ArgoCD is a reconciler that must stay the
source of truth — this is the reconciler-gated-mutation rule, not a blanket
read-MCP/write-CLI law.

## Read path — via the gateway MCP

Use the `<entry>.mcp-*` tools (e.g. `argocd-list_applications`, `argocd-get_application`,
`argocd-get_application_resource_tree`) for all read and diagnosis work. No CLI needed for reads.

## Write path — CLI only

Sync, rollback, and other mutations go through the `argocd` CLI — never the MCP, and never
`kubectl apply` in a GitOps-managed cluster:

```bash
export ARGOCD_SERVER=<the argocd entry's .endpoint>
export ARGOCD_AUTH_TOKEN=$(<resolve the argocd entry's .auth>)   # e.g. op read op://…/agent_token
argocd app sync <app>
argocd app rollback <app> <revision>
```

## Conventions (project-agnostic)

- Never `kubectl apply` to mutate a GitOps-managed app — let ArgoCD reconcile, or `argocd app sync`.
- Read state before acting; a degraded app may be mid-sync.
- Honour the argocd entry's `.notes` for project quirks (e.g. known false-drift / ignore-difference patterns).

## Everything project-specific comes from the recipe

| Need | Source |
|------|--------|
| Server endpoint | the argocd entry's `.endpoint` |
| Auth | the argocd entry's `.auth` |
| Read-path MCP prefix | the argocd entry's `.mcp` |
| App / overlay layout, drift quirks | the argocd entry's `.notes` + `facts` |

This module is the entire ArgoCD-specific surface. To make ArgoCD work for a new project,
that project adds a `tools.*` entry with `module: argocd` to its recipe — it writes no ArgoCD
skill of its own.
