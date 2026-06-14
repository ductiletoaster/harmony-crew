---
name: harmony-platform-conventions
description: Core Kubernetes workload conventions all agents must follow when writing or reviewing manifests.
category: domain
durability: durable
---

All Kubernetes workloads deployed to Harmony must follow these conventions. Apply them when writing, reviewing, or modifying any manifest.

## Scheduling

Every workload must tolerate the control-plane taint — all three Talos nodes are control-plane and carry `node-role.kubernetes.io/control-plane:NoSchedule`:

```yaml
tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

Without this toleration, pods will not schedule anywhere in the cluster.

## Storage

Two StorageClasses — choose based on data type and retention need:

| StorageClass | Backing | Reclaim | Use for |
|---|---|---|---|
| `harmony-runtime` | NVMe | `Delete` | Databases, model weights, ephemeral workspaces |
| `harmony-storage` | HDD | `Retain` | User data, media, long-lived shared content |

Never swap these without understanding the reclaim consequence. `Delete` means the PV is destroyed when the PVC is deleted. `Retain` means the PV persists and must be manually cleaned up.

## Pod Security Context

Standard security context for all workloads:

```yaml
securityContext:
  fsGroup: 3000
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault
```

Container-level: drop `ALL` capabilities unless a specific capability is explicitly required and justified.

## Runtime Substrate (RuntimeClass)

Two runtimes are available on the cluster. Pick by **workload threat model**, not convenience:

| `runtimeClassName` | Use for | Why |
|---|---|---|
| `kata` | LLM-directed code AND Docker / nested namespaces (pi-worker execute, pi-web, coder-mcp, homelab-audit, Coder workspace pods) | Real Linux kernel in a microVM. Full syscall surface — handles NFS-CSI writes the same way runc does. Cold start ~150-300ms, ~50-200MB memory per pod. |
| (unset → runc default) | Everything else — observability, vault, app services, ARC runners | No isolation tax for workloads that don't run untrusted code. ARC runners explicitly stay on runc + privileged DinD for GitHub Actions parity. |

The principle: **agent surfaces and Docker workloads use Kata; everything else uses the default.**

Earlier the cluster also offered gVisor, but it was retired — its gofer/9P shim blocks all writes to NFS-backed PVCs (the cluster's only persistent storage substrate), making it unusable for any workload that writes state. Kata replaces it across the board.

The `kata` RuntimeClass lives at `infrastructure/kubernetes/apps/homelab-agents/base/runtimeclass-kata.yaml` and requires the `siderolabs/kata-containers` Talos system extension on every node (see `scripts/talos-kata-rolling-upgrade.sh`).

## Secret Management

Secrets come from 1Password via External Secrets Operator. Never hardcode secrets in manifests.

- ExternalSecret `refreshInterval` must be `"0"` (sync on creation only)
- ExternalSecret `deletionPolicy` must be `Retain`
- Force-sync: delete the ExternalSecret and let ArgoCD recreate it
- Reference the `onepassword` ClusterSecretStore

## Namespace and PodSecurity

Each service gets its own namespace. PodSecurity admission is enforced — default is `baseline`. The `monitoring` namespace uses `privileged` (required for hostNetwork/hostPID workloads like node exporters).

## Kustomize Structure

Manifests follow base + overlay pattern:

```
infrastructure/kubernetes/
├── base/<component>/       # Reusable base resources
└── overlays/prod/<app>/    # Production-specific patches (tolerations, GPU, resources)
```

Changes to base manifests propagate to all overlays — treat base changes as high blast-radius. Prefer overlay patches for environment-specific concerns.

## GPU Workloads

GPU workloads (ComfyUI, InvokeAI) require:
- Node selector or affinity for GPU nodes (`workstation-01`, `workstation-02`)
- NVIDIA resource limit: `nvidia.com/gpu: 1`
- Applied via overlay patch, not in base

## ArgoCD

All workloads are managed by ArgoCD app-of-apps rooted at `argocd/root.yaml`. Do not apply manifests directly with `kubectl apply` in production — let ArgoCD sync. For forced resync, use `argocd app sync <app-name>`.
