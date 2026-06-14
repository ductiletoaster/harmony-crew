---
name: k8s-kustomize-conventions
description: Generic Kustomize base+overlay structure, overlay patch patterns, and manifest validation. Applies the project's manifest paths and toleration/runtime values (project-specific values). Load when writing or modifying Kubernetes manifests.
category: stack
durability: durable
---

Generic Kustomize convention pattern. The base+overlay *structure* and patch *discipline* are
fixed; the concrete directory paths, taint keys, StorageClasses, and node selectors are
project-specific (from the project's own manifest tree) — never hard-code them.

## Directory structure

Manifests follow a base + overlay layout. Bases are reusable and env-agnostic; overlays carry the
environment-specific patches (tolerations, node affinity, resources, replicas):

```
<k8s-root>/
├── base/<component>/         # reusable base resources — no env-specific config
└── overlays/<env>/<app>/     # per-app, per-env patches
    ├── kustomization.yaml
    └── <patch-files>.yaml
```

The GitOps reconciler syncs each `overlays/<env>/<app>/` directory. Base resources are **shared**
— a change to a base manifest propagates to every overlay that references it. Treat base changes
as high blast-radius; push environment-specific concerns into overlay patches.

The `<k8s-root>` and the `<env>` overlay name are the project's own — they are project-specific
(from the project tree); this skill never assumes a specific environment name.

## Required overlay content — the scheduling patch

Every overlay must patch in the cluster's scheduling toleration so pods can land on the project's
nodes. The **canonical toleration block shape is owned by `k8s-workload-patterns`**; this overlay
patch fills it with the project's scheduling taint key:

```yaml
# overlays/<env>/<app>/toleration-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app>
spec:
  template:
    spec:
      tolerations:
        - key: <taint-key>                 # project-specific
          operator: Exists
          effect: NoSchedule
```

Without the matching toleration, pods will not schedule. See `k8s-workload-patterns` for the
full required-fields skeleton (security context, runtime class).

## kustomization.yaml structure

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base/<component>

patches:
  - path: toleration-patch.yaml
    target:
      kind: Deployment
      name: <app>
```

## Specialized overlays (GPU, etc.)

Hardware-specific requirements — node affinity, accelerator resource limits — go in **overlay
patches, never in base**:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: <gpu-node>   # project-specific
      containers:
        - name: <app>
          resources:
            limits:
              nvidia.com/gpu: 1                 # accelerator key per the project's hardware
```

The node names and accelerator keys are project facts; the base/overlay *placement* is the pattern.

## Static / cross-namespace volumes

If the project shares a static volume across namespaces (e.g. a read-only model library backed by
NFS), the consumer PVCs use `storageClassName: ""` to bypass dynamic provisioning and bind the
static PV. **Keep the empty string** — it is intentional, not a missing value. The backing path
and mount points are project facts.

## Manifest validation

Before opening a PR, confirm the overlay resolves:

```bash
kubectl kustomize build <k8s-root>/overlays/<env>/<app>
```

This validates the kustomization without applying anything to the cluster.

## Kustomize image transforms — known limit

Kustomize `images:` transforms reach standard workload kinds but **do not** reach CRDs such as
WorkflowTemplate. If pinning an image inside a CRD, set the tag directly in that resource's YAML;
don't rely on `images:` in `kustomization.yaml` to propagate there.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, …) are project-specific. The
consuming project supplies them — in its own overlay skills or the agent's working context. This
skill is the generic pattern.

| Need | Source |
|---|---|
| Manifest root + overlay env name | project-specific (the project tree) |
| Scheduling taint key (fills the toleration block) | project-specific |
| StorageClasses for PVCs | project-specific (fast / bulk tiers — see `k8s-workload-patterns`) |
| GPU node selectors / accelerator keys | project-specific (the project's hardware) |
| Canonical toleration / securityContext block shapes | owned by `k8s-workload-patterns` |
| GitOps wiring that syncs the overlay | project-specific (the project's gitops module) |

This skill owns the base+overlay discipline; the project supplies the paths and scalars.
