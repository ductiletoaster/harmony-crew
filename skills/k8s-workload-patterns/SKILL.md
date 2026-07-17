---
name: k8s-workload-patterns
description: Kubernetes workload design patterns for Harmony — Deployment, StatefulSet, DaemonSet selection, resource limits, health checks, and service exposure. Load when designing or reviewing workload manifests.
category: domain
durability: durable
tier: subject
---

## Workload type selection

| Type | Use when |
|---|---|
| `Deployment` | Stateless services, multiple replicas, rolling updates |
| `StatefulSet` | Stateful services needing stable network identity or ordered pod management (databases, Valkey) |
| `DaemonSet` | Per-node services (Node Exporter, DCGM Exporter, Traefik in hostNetwork mode) |
| `CronJob` | Scheduled one-off tasks |

For most platform services: `Deployment`. For databases backing platform services: `StatefulSet`.

## Runtime selection

Most workloads use the cluster's default container runtime (no `runtimeClassName` field). One opt-in alternative exists for specific cases — see `harmony-platform-conventions` for the full decision table:

- `runtimeClassName: kata` → workloads running LLM-directed code OR needing real-kernel features (agent surfaces, Docker compose stacks)
- _omit_ → everything else (apps, observability, vault, ARC runners)

## Required fields for all workloads

```yaml
spec:
  template:
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      securityContext:
        fsGroup: 3000
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: <app>
          securityContext:
            capabilities:
              drop: [ALL]
```

See `harmony-platform-conventions` for the canonical versions of these fields.

## Resource limits

Always set both `requests` and `limits`. Requests affect scheduling; limits prevent noisy-neighbor OOM:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "1000m"
    memory: "512Mi"
```

GPU workloads additionally set `nvidia.com/gpu: 1` in limits (overlay only).

## Health checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

Use `readinessProbe` to control traffic routing. Use `livenessProbe` to restart genuinely broken containers. Don't share the same endpoint for both unless the semantics align.

## Service exposure

In-cluster services use `ClusterIP`. External access via Traefik IngressRoute (not plain Ingress):

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: <app>
  namespace: <app>
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`<app>.lab.pixeloven.com`)
      kind: Rule
      services:
        - name: <app>
          port: 8080
```

Lab services use `*.lab.pixeloven.com`. Management services use `*.manage.pixeloven.com` (Omni VM Traefik, separate ingress).

## PersistentVolumeClaims

Always use PVCs, never hostPath (except for DaemonSet node-exporter patterns). StorageClass selection:
- `harmony-runtime` — databases, model weights, ephemeral workspaces (NVMe, Delete reclaim)
- `harmony-storage` — user data, media, long-lived shared content (HDD, Retain reclaim)

Never swap these without reviewing the reclaim consequence.
