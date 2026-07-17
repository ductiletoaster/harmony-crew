---
name: k8s-service-onboarding
description: Step-by-step pattern for adding a new service to the Harmony platform — namespace, manifests, ArgoCD app, secrets, and verification. Load when deploying a new application to the cluster.
category: architecture
durability: durable
tier: subject
---

## Onboarding checklist

### 1. Namespace and PodSecurity

Create a namespace with PodSecurity labels:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <app>
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: baseline
```

Use `privileged` only if the workload requires hostNetwork, hostPID, or hostPath (like node exporters). Default is `baseline`.

### 2. Base manifests

Create `infrastructure/kubernetes/base/<app>/`:
- `deployment.yaml` (or StatefulSet)
- `service.yaml`
- `configmap.yaml` (if needed)
- `kustomization.yaml`

All workload resources must include the control-plane toleration and standard security context — see your platform's conventions skill.

### 3. Overlay

Create `infrastructure/kubernetes/overlays/prod/<app>/`:
- `kustomization.yaml` — references base, includes patches
- `toleration-patch.yaml` — control-plane toleration on the workload
- GPU patch if needed (node selector + `nvidia.com/gpu: 1`)

### 4. Secrets

If the service needs secrets from 1Password:
1. Add the 1Password item to the Harmony vault
2. Create an ExternalSecret in the app namespace — only if a pod consumer exists in the same PR
3. Reference `onepassword` ClusterSecretStore
4. Set `refreshInterval: "0"` and `deletionPolicy: Retain`

See `secret-management-patterns` for the full ESO pattern.

### 5. Ingress

Add a Traefik IngressRoute if the service needs external access:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: <app>
  namespace: <app>
spec:
  entryPoints: [websecure]
  routes:
    - match: Host(`<app>.<service-domain>`)
      kind: Rule
      services:
        - name: <app>
          port: 8080
```

Add a DNS A record (via the platform's DNS/Terraform stage) pointing `<app>.<service-domain>` to the cluster node IPs. The concrete service domain, DNS stage, and node IPs live in the consumer's topology skill.

### 6. ArgoCD child Application

Create `infrastructure/kubernetes/argocd/apps/<app>.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app>
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/ductiletoaster/harmony.git
    targetRevision: HEAD
    path: infrastructure/kubernetes/overlays/prod/<app>
  destination:
    server: https://kubernetes.default.svc
    namespace: <app>
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 7. Validation

```bash
kubectl kustomize build infrastructure/kubernetes/overlays/prod/<app>
# Review output for correctness before committing
```

After merge and ArgoCD sync:
```bash
argocd app get <app>
kubectl get pods -n <app>
kubectl get externalsecret -n <app>   # if secrets exist
```

### 8. Post-deploy checklist

Create `.claude/checklists/<app>.yaml` for the `harmony.checklist` command. Falls back to `_default.yaml` if absent.
