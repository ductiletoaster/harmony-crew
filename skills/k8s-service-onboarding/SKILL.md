---
name: k8s-service-onboarding
description: Generic step-by-step pattern for adding a new service to a Kubernetes platform — namespace, base manifests, overlay, secrets, ingress, GitOps registration, verification. Applies the project's paths/domains from the recipe's facts; defers GitOps + secret wiring to the active tool modules. Load when deploying a new application.
category: architecture
durability: durable
---

Generic new-service onboarding pattern. The *steps* below are fixed; every path, domain, store
name, and reconciler comes from the recipe's `facts` and the active `tools.*` modules — never
hard-code them. GitOps registration and secret wiring are **deferred to the project's tool
modules** (`tools.gitops`, `tools.secrets`); this skill sequences them, it doesn't reimplement them.

## Onboarding checklist

### 1. Namespace and PodSecurity

Each service gets its own namespace with PodSecurity admission labels — default to `baseline`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <app>
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: baseline
```

Use `privileged` **only** if the workload genuinely needs `hostNetwork`, `hostPID`, or `hostPath`
(e.g. node exporters). Otherwise stay on `baseline`.

### 2. Base manifests

Create the base under the project's manifest root (`<k8s-root>/base/<app>/`):
- `deployment.yaml` (or `StatefulSet`)
- `service.yaml`
- `configmap.yaml` (if needed)
- `kustomization.yaml`

Every workload resource carries the scheduling toleration (taint key from `facts.tolerations`)
and the standard security context — use the canonical skeletons from `k8s-workload-patterns`,
filled with `facts`.

### 3. Overlay

Create the per-env overlay (`<k8s-root>/overlays/<env>/<app>/`):
- `kustomization.yaml` — references the base, lists patches
- `toleration-patch.yaml` — scheduling toleration (taint key from `facts.tolerations`)
- accelerator/affinity patch if the workload needs hardware (node selector + accelerator limit)

See `k8s-kustomize-conventions` for the base/overlay discipline and the `<k8s-root>` / `<env>`
sources.

### 4. Secrets — via the secrets tool module

If the service needs secrets, follow the project's **secrets tool module** (`tools.secrets`,
e.g. `tool-external-secrets` / `tool-sealed-secrets`). The decision rule (paraphrased there):

- A **pod/Deployment/CronJob** that mounts a Kubernetes Secret → create the reconciled secret
  manifest (e.g. an `ExternalSecret`) **and** its consuming workload in the **same PR**.
- A **CLI / CI / agent subprocess** that can read the backing store directly at runtime → read
  the store directly, **no** in-cluster secret object.

Never create a speculative secret object ahead of a consumer. Store name and reference prefix come
from the secrets-role `tools.*` entry — not from this skill.

### 5. Ingress

If the service needs external access, add an ingress object for the project's ingress controller,
matched on a host under `facts.domains`:

```yaml
# ingress kind/apiVersion per the project's ingress stack
spec:
  routes:
    - match: Host(`<app>.<facts.domains>`)
      services:
        - name: <app>
          port: 8080
```

Add the matching DNS record for `<app>.<facts.domains>` wherever the project manages DNS (often a
Terraform stage — see `terraform-conventions`).

### 6. Register with the GitOps reconciler

Wire the overlay into continuous delivery through the project's **GitOps tool module**
(`tools.gitops` — e.g. `tool-argocd`, `tool-flux`). That module owns the reconciler resource
shape (an ArgoCD `Application`, a Flux `Kustomization`, …) pointing at
`<k8s-root>/overlays/<env>/<app>`, with prune + self-heal enabled per the project's convention.
**Do not invent the reconciler manifest here** — defer to the gitops module so a Flux project and
an ArgoCD project each get the right shape.

### 7. Validation

Confirm the overlay resolves before committing — this applies nothing to the cluster:

```bash
kubectl kustomize build <k8s-root>/overlays/<env>/<app>
```

After merge and a reconciler sync, verify via the gitops module's read surface and `kubectl`:

```bash
kubectl get pods -n <app>
kubectl get <secret-object-kind> -n <app>   # if the service uses secrets
```

(For ArgoCD/Flux app-state reads, use the gitops module's read path — see `tools.gitops`.)

### 8. Post-deploy checklist

If the project drives post-deploy verification from per-app checklist files, add one for the new
service (falling back to the project's default checklist when absent).

## Project values come from the recipe

| Need | Source |
|---|---|
| Manifest root + overlay env name | `facts` / the project tree |
| Toleration / securityContext skeletons | `k8s-workload-patterns` (scalars from `facts`) |
| StorageClasses | `facts.storage_fast` / `facts.storage_bulk` |
| External domain for the ingress host | `facts.domains` |
| Secret store + reference prefix + secret-object kind | the `tools.secrets` module |
| Reconciler manifest shape + read/sync surface | the `tools.gitops` module |
| DNS management | the project's IaC (`stack.iac`) |

This skill sequences the steps; the recipe's facts and tool modules supply the paths, stores, and
reconcilers.
