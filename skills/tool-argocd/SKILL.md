---
name: tool-argocd
description: Operating ArgoCD as an agent — read application state, sync, rollback, diagnose. Load this when the project uses ArgoCD.
---

Generic ArgoCD operating pattern. Load this when the project uses ArgoCD. The project
provides the server endpoint, auth ref, and MCP prefix (env vars, mounted secrets, or its
overlay) — never hard-code them.

## Surfaces

- **Read path** = the gateway's ArgoCD MCP tools (`argocd-*` — e.g. `argocd-list_applications`,
  `argocd-get_application`, `argocd-get_application_resource_tree`).
- **Write path** (sync / rollback) = the `argocd` CLI.

ArgoCD mutations are gated to the CLI/PR because ArgoCD is a reconciler that must stay the
source of truth — this is the reconciler-gated-mutation rule, not a blanket
read-MCP/write-CLI law.

## Read path — via the gateway MCP

Use the gateway's `argocd-*` MCP tools (e.g. `argocd-list_applications`, `argocd-get_application`,
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
- Honour the project's notes for quirks (e.g. known false-drift / ignore-difference patterns).

## Everything project-specific is supplied by the project

| Need | Source |
|------|--------|
| Server endpoint | project-specific (env var, mounted secret, or overlay) |
| Auth | project-specific (env var, mounted secret, or overlay) |
| Read-path MCP prefix | project-specific (the project's gateway config) |
| App / overlay layout, drift quirks | project-specific (the project's overlay/notes) |

This module is the entire ArgoCD-specific surface. To make ArgoCD work for a new project,
that project supplies the endpoint, auth, and MCP prefix in its own overlay or context — it
writes no ArgoCD skill of its own.
