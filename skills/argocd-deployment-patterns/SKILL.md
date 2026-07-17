---
name: argocd-deployment-patterns
description: ArgoCD app-of-apps structure, sync waves, health check semantics, and deployment patterns for Harmony. Load when deploying, syncing, or debugging ArgoCD-managed workloads.
category: domain
durability: durable
tier: subject
---

All Harmony workloads are managed by ArgoCD. The root application is at `argocd/root.yaml` using an app-of-apps pattern with 12 child Applications.

## App-of-apps structure

```
argocd/root.yaml          # Root Application — watches argocd/ directory
argocd/apps/              # Child Application manifests
infrastructure/kubernetes/
├── base/<component>/     # Base resources
└── overlays/prod/<app>/  # Production patches
```

ArgoCD syncs `overlays/prod/<app>` for each child Application. Changes to base manifests propagate to all overlays — treat base changes as high blast-radius.

## Sync operations

**Agent read paths** route through LiteLLM MCP — no auth required:
```
argocd-list_applications    # List all apps
argocd-get_application      # Get a specific app
```

**Write operations** (sync, rollback) always use the CLI:
```bash
export ARGOCD_SERVER=argocd.lab.pixeloven.com
export ARGOCD_AUTH_TOKEN=$(op read "op://Harmony/ArgoCD/agent_token")

argocd app sync <app-name>
argocd app wait <app-name> --health --timeout 300
```

**Fallback** (when both CLI and LiteLLM unavailable):
```bash
kubectl get applications.argoproj.io -n argocd
```

**Never** apply manifests directly with `kubectl apply` in production — let ArgoCD sync.

## Sync waves

ArgoCD sync waves control resource creation order. Lower wave numbers deploy first.

Key platform waves:
- Wave `"1"` — namespace-level resources (namespaces, RBAC, shared volumes)
- Wave `"2"` — dependencies (databases, caches)
- Wave `"3"` — application workloads

The `shared-models` namespace (PVs for ComfyUI and InvokeAI) deploys at wave `"1"`.

Set sync wave via annotation:
```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"
```

## Health check semantics

ArgoCD evaluates app health from Kubernetes resource health. Common states:
- **Healthy** — all resources in expected state
- **Progressing** — resources being updated (pods starting, rollout in progress)
- **Degraded** — one or more resources failed or are in error state
- **Missing** — expected resource not found in cluster
- **Suspended** — resource is paused (e.g., CronJob suspended)

An app shows **OutOfSync** when the live cluster state diverges from the git source. This is expected during a deploy and resolves once sync completes.

## Debugging a degraded app

```bash
argocd app get <app-name>               # Overview: sync + health status
argocd app get <app-name> -o json       # Full detail including resource conditions
kubectl get pods -n <namespace>         # Pod state
kubectl describe pod -n <namespace> <pod>  # Events and conditions
kubectl logs -n <namespace> <pod>       # Container logs
```

For ExternalSecret issues specifically — see `secret-management-patterns`.

## Adding a new app

1. Create base manifests under `infrastructure/kubernetes/base/<app>/`
2. Create overlay under `infrastructure/kubernetes/overlays/prod/<app>/` with toleration patch
3. Add a child Application manifest to `argocd/apps/<app>.yaml`
4. ArgoCD root app picks it up on next sync

GPU workloads additionally need a node selector or affinity overlay patch — see `harmony-platform-conventions`.
