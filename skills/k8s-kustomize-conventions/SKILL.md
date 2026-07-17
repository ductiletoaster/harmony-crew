---
name: k8s-kustomize-conventions
description: Kustomize base+overlay structure, overlay patch patterns, manifest validation, and ArgoCD sync conventions for Harmony. Load when writing or modifying Kubernetes manifests.
category: stack
durability: durable
tier: subject
---

## Directory structure

```
infrastructure/kubernetes/
├── base/<component>/       # Reusable base resources (no env-specific config)
└── overlays/prod/<app>/    # Production patches (tolerations, GPU, resources, replicas)
    ├── kustomization.yaml
    └── <patch-files>.yaml
```

ArgoCD syncs each `overlays/prod/<app>/` directory. Base resources are shared — **changes to base manifests propagate to all overlays**. Treat base changes as high blast-radius; prefer overlay patches for environment-specific concerns.

## Required overlay content

Every overlay must include a toleration patch for the control-plane taint:

```yaml
# overlays/prod/<app>/toleration-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app>
spec:
  template:
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
```

Without this, pods will not schedule anywhere in the cluster.

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

## GPU workloads

GPU overlays additionally require node affinity and resource limits — applied via overlay patch, never in base:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: workstation-01   # or workstation-02
      containers:
        - name: <app>
          resources:
            limits:
              nvidia.com/gpu: 1
```

## Manifest validation

Before opening a PR:
```bash
kubectl kustomize build infrastructure/kubernetes/overlays/prod/<app>
```

This validates the kustomization resolves without error. It does not apply anything to the cluster.

## Shared model library (ComfyUI + InvokeAI)

A cross-namespace static NFS volume provides a read-only model library. The `shared-models` namespace contains two static PVs pointing at NFS `192.168.8.200:/mnt/Data/Storage/shared-models/library`. Each consumer namespace has a matching RWX PVC with `storageClassName: ""` to bypass dynamic provisioning.

- ComfyUI mounts at `/app/ComfyUI/shared_models` (wired via `extra_model_paths.yaml` ConfigMap)
- InvokeAI mounts at `/workspace/shared-models` (init container creates symlinks under `/workspace/models/.shared/<type>`)

Do not change `storageClassName` on these PVCs — the empty string is intentional to bind to the static PV.

## Kustomize image transforms

Kustomize image transforms do **not** reach WorkflowTemplate CRDs. If pinning an image in a WorkflowTemplate, set the tag directly in the workflow YAML — do not rely on `images:` in `kustomization.yaml` to propagate there.
