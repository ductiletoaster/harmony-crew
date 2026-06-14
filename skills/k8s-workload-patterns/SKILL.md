---
name: k8s-workload-patterns
description: Generic Kubernetes workload design — workload-type selection, the canonical toleration + securityContext block shapes, runtime-class selection logic, resource limits, probes, and service exposure. This skill OWNS the block skeletons; the recipe's facts supply only the variable scalars. Load when designing or reviewing workload manifests.
category: domain
durability: durable
---

Generic workload-design pattern. **This skill owns the canonical block shapes** — the toleration
block, the security-context skeleton, and the runtime-class *selection logic*. The recipe's
`facts` supply only the variable scalars that fill those blocks (`fsGroup`, the StorageClass
names, the toleration key, the runtime-class names). Authoring a manifest against these skeletons
is correct-by-construction; never hand-roll a different shape.

## Workload type selection

| Type | Use when |
|---|---|
| `Deployment` | Stateless services, multiple replicas, rolling updates |
| `StatefulSet` | Stateful services needing stable network identity or ordered pod management (databases, caches) |
| `DaemonSet` | Per-node services (node exporters, hostNetwork ingress) |
| `CronJob` | Scheduled one-off tasks |

Default to `Deployment`; use `StatefulSet` for the databases backing those services.

## Required fields for all workloads — canonical skeleton

Every pod spec carries the scheduling toleration and the standard security context. This is the
owned shape; fill the scalars from `facts`, leave the structure intact:

```yaml
spec:
  template:
    spec:
      tolerations:
        - key: <facts.tolerations[*]>      # taint key — the only variable part
          operator: Exists
          effect: NoSchedule
      securityContext:
        fsGroup: <facts.fsGroup>           # pod-identity GID for shared-storage writes
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: <app>
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: [ALL]                  # add a capability back only with explicit justification
```

- `operator: Exists` + `effect: NoSchedule` are fixed — only the toleration **key** varies, and it
  comes from `facts.tolerations`. Without the matching toleration, pods won't schedule.
- `fsGroup` is the **only** variable in the security context; everything else
  (`runAsNonRoot`, `seccompProfile: RuntimeDefault`, dropped capabilities) is constant.

## Runtime selection logic

A project may declare two runtimes in `facts.runtimes`: a `default` and a `sandboxed` one. Select
the runtime class by **workload threat model**, not convenience:

| `runtimeClassName` | Use for | Rule |
|---|---|---|
| `<facts.runtimes.sandboxed>` | Workloads that run LLM-directed / untrusted code, or need real-kernel / nested-namespace features (agent execution surfaces, Docker / compose stacks) | Stronger isolation for code you don't fully control |
| _(unset → `<facts.runtimes.default>`)_ | Everything else — app services, observability, stores, CI runners | No isolation tax for workloads that don't run untrusted code |

The selection **principle is fixed**: *agent surfaces and Docker workloads get the sandboxed
runtime; everything else uses the default.* Only the two runtime-class **names** vary, and they
come from `facts.runtimes.{sandboxed,default}`. Omitting `runtimeClassName` selects the cluster
default — that's the intended path for ordinary workloads.

## Resource limits

Always set both `requests` and `limits`. Requests drive scheduling; limits prevent noisy-neighbor
OOM:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "1000m"
    memory: "512Mi"
```

Accelerator workloads additionally set the accelerator key (e.g. `nvidia.com/gpu: 1`) in
`limits`, and only in the overlay — see `k8s-kustomize-conventions`.

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

Readiness controls traffic routing; liveness restarts genuinely broken containers. Don't share an
endpoint for both unless the semantics align.

## Service exposure

In-cluster services use `ClusterIP`. External access goes through the project's ingress controller
(an IngressRoute / Ingress per the project's ingress stack), matched on a host under the project's
domain:

```yaml
# ingress shape depends on the project's controller; the host comes from facts.domains
spec:
  routes:
    - match: Host(`<app>.<facts.domains>`)
      services:
        - name: <app>
          port: 8080
```

The ingress kind/apiVersion and the domain are project facts; the ClusterIP-internal /
ingress-external split is the pattern.

## PersistentVolumeClaims

Always use PVCs, never `hostPath` (except established DaemonSet node-exporter patterns). Pick the
StorageClass by data type and retention need from `facts`:

| Recipe key | Tier | Use for |
|---|---|---|
| `facts.storage_fast` | fast (e.g. NVMe), typically `Delete` reclaim | Databases, model weights, ephemeral workspaces |
| `facts.storage_bulk` | bulk (e.g. HDD), typically `Retain` reclaim | User data, media, long-lived shared content |

Never swap these without reviewing the reclaim consequence: `Delete` destroys the PV with the PVC;
`Retain` keeps the PV until it's manually cleaned up.

## Project values come from the recipe

| Need | Source |
|---|---|
| Toleration taint key (fills the fixed toleration block) | `facts.tolerations` |
| `fsGroup` (the only variable in the security-context skeleton) | `facts.fsGroup` |
| Sandboxed + default runtime-class names | `facts.runtimes.sandboxed` / `facts.runtimes.default` |
| StorageClass names | `facts.storage_fast` / `facts.storage_bulk` |
| External domain for ingress hosts | `facts.domains` |
| Ingress controller kind / accelerator keys | the project's ingress + hardware facts |

This skill owns every block *shape*; the recipe supplies only the scalars that fill them. A small
model authoring against these skeletons cannot produce a malformed toleration or security context
— it only fills in the recipe's values.
