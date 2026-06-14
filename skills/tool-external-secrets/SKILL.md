---
name: tool-external-secrets
description: Operating External Secrets Operator (ESO) as an agent — syncing secrets from a backing store into Kubernetes via ExternalSecrets. Active only when the project recipe declares a tools.* entry whose module = external-secrets; reads store/prefix from that entry.
---

Generic External Secrets Operator (ESO) operating pattern. **Activation:** load this only when
the recipe has a `tools.*` entry whose `module` is `external-secrets` (the recipe author chooses
the role key — it's commonly `secrets`, but read the module value, not the key). Take the
ClusterSecretStore name and the secret-reference prefix from **that external-secrets entry** —
never hard-code them. (A project on Sealed Secrets loads `tool-sealed-secrets` instead.)

## Surfaces

Secret sync is **reconciler-gated**: you do not write Kubernetes Secrets directly. You declare an
`ExternalSecret` manifest; ESO is the reconciler that reads the backing store and materialises the
Kubernetes Secret. Changes flow **store → ExternalSecret manifest → ESO → Secret**, never a direct
`kubectl create secret`. This is the reconciler-gated-mutation rule applied to secrets: the
manifest (via PR/GitOps) is the source of truth, ESO owns the live Secret.

- **Read path** — inspect ExternalSecret status and the resulting Secret via `kubectl` /
  the gateway MCP cluster tools.
- **Write path** — author/modify the `ExternalSecret` manifest (PR); force-sync via the
  delete-and-recreate procedure below. Never hand-edit the materialised Secret.

## ExternalSecret conventions (project-agnostic)

Every ExternalSecret should carry:

```yaml
spec:
  refreshInterval: "0"       # sync on creation only — never poll
  deletionPolicy: Retain     # the materialised Secret persists if the ExternalSecret is deleted
```

- **`refreshInterval: "0"` (sync-on-create, never poll).** Polling drives backing-store API
  rate-limit cascades across every ESO-managed secret. Treat it as a platform constraint, not a
  preference.
- **`deletionPolicy: Retain`.** Deleting the ExternalSecret leaves the live Secret in place — so
  delete-and-recreate is a safe force-sync, not a data-loss event.
- **Reference the project's registered ClusterSecretStore by name** — take it from the recipe
  entry's `.store`; don't assume a store name.

## When to create an ExternalSecret — the decision rule

An ExternalSecret only earns its keep when a workload consumes the resulting Secret. It is a
bridge from the backing store into Kubernetes; with no consumer it's dead weight that reports
false-positive Degraded status.

| Caller | Pattern |
|--------|---------|
| CLI, CI, agent subprocess — anything that can read the store directly at runtime | Read the store directly (e.g. `op read`, the store's own CLI/SDK) — **no ExternalSecret** |
| Pod / Deployment / CronJob that mounts or references a Kubernetes Secret | ExternalSecret — land the ExternalSecret **and its consuming workload in the same PR** |

**Never create a speculative ExternalSecret ahead of a consumer.**

## Force-sync procedure

Because `refreshInterval: "0"` means the standard force-sync annotation does nothing, re-sync by
delete-and-recreate (safe under `deletionPolicy: Retain`):

```bash
# 1. Drop finalizers so deletion completes
kubectl patch externalsecret <name> -n <ns> --type=merge \
  -p '{"metadata":{"finalizers":[]}}'

# 2. Delete — the GitOps reconciler recreates it from the manifest, re-pulling from the store
kubectl delete externalsecret <name> -n <ns>
```

If the ClusterSecretStore reports a rate-limit error, scale ESO to zero, wait for the backing
store's rate-limit window to clear, then scale it back to one — this stops the polling cascade.

## Everything project-specific comes from the recipe

| Need | Source |
|------|--------|
| ClusterSecretStore name | the external-secrets entry's `.store` |
| Secret-reference prefix (where store paths live) | the external-secrets entry's `.prefix` |
| Pod-identity / filesystem ownership (e.g. `fsGroup`) | `facts` |
| Store-specific quirks (paths, rotation) | the external-secrets entry's `.notes` + `facts` |

This module is the entire ESO-specific surface. To make ESO work for a new project, that project
adds a `tools.*` entry with `module: external-secrets` to its recipe — it writes no secrets skill
of its own.
