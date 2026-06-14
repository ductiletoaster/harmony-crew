---
name: k8s-service-onboarding
description: Generic step-by-step pattern for adding a new service to a Kubernetes platform — namespace, base manifests, overlay, secrets, ingress, GitOps registration, verification. Applies the project's paths/domains (project-specific values); defers GitOps + secret wiring to the project's tool modules. Load when deploying a new application.
category: architecture
durability: durable
---

Generic new-service onboarding pattern. The *steps* below are fixed; every path, domain, store
name, and reconciler is project-specific (supplied by the project) — never hard-code them. GitOps
registration and secret wiring are **deferred to the project's tool modules** (its gitops and
secrets modules); this skill sequences them, it doesn't reimplement them.

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

Every workload resource carries the scheduling toleration (project-specific taint key)
and the standard security context — use the canonical skeletons from `k8s-workload-patterns`,
filled with the project's values.

### 3. Overlay

Create the per-env overlay (`<k8s-root>/overlays/<env>/<app>/`):
- `kustomization.yaml` — references the base, lists patches
- `toleration-patch.yaml` — scheduling toleration (project-specific taint key)
- accelerator/affinity patch if the workload needs hardware (node selector + accelerator limit)

See `k8s-kustomize-conventions` for the base/overlay discipline and the `<k8s-root>` / `<env>`
sources.

### 4. Secrets — via the secrets tool module

If the service needs secrets, follow the project's **secrets tool module** (e.g. an
external-secrets or sealed-secrets module). The decision rule (paraphrased there):

- A **pod/Deployment/CronJob** that mounts a Kubernetes Secret → create the reconciled secret
  manifest (e.g. an `ExternalSecret`) **and** its consuming workload in the **same PR**.
- A **CLI / CI / agent subprocess** that can read the backing store directly at runtime → read
  the store directly, **no** in-cluster secret object.

Never create a speculative secret object ahead of a consumer. Store name and reference prefix are
project-specific (from the project's secrets configuration) — not from this skill.

### 5. Ingress

If the service needs external access, add an ingress object for the project's ingress controller,
matched on a host under the project's domain:

```yaml
# ingress kind/apiVersion per the project's ingress stack
spec:
  routes:
    - match: Host(`<app>.<domain>`)   # domain is project-specific
      services:
        - name: <app>
          port: 8080
```

Add the matching DNS record for `<app>.<domain>` wherever the project manages DNS (often a
Terraform stage — see `terraform-conventions`).

### 6. Register with the GitOps reconciler

Wire the overlay into continuous delivery through the project's **GitOps tool module**
(e.g. `tool-argocd`, `tool-flux`). That module owns the reconciler resource
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

(For ArgoCD/Flux app-state reads, use the gitops module's read path.)

### 8. Post-deploy checklist

If the project drives post-deploy verification from per-app checklist files, add one for the new
service (falling back to the project's default checklist when absent).

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, …) are project-specific. The
consuming project supplies them — in its own overlay skills or the agent's working context. This
skill is the generic pattern.

| Need | Source |
|---|---|
| Manifest root + overlay env name | project-specific (the project tree) |
| Toleration / securityContext skeletons | `k8s-workload-patterns` (project-specific scalars) |
| StorageClasses | project-specific (fast / bulk tiers) |
| External domain for the ingress host | project-specific |
| Secret store + reference prefix + secret-object kind | the project's secrets module |
| Reconciler manifest shape + read/sync surface | the project's gitops module |
| DNS management | the project's IaC |

This skill sequences the steps; the project's values and tool modules supply the paths, stores,
and reconcilers.
