---
name: service-deprecation-playbook
description: Pattern for cleanly sunsetting a service — dependents, data disposition, ingress off, scale down, remove from gitops, manifest cleanup, namespace, secrets, DNS, docs. Generic sequence; the tool and path specifics come from the recipe's active modules and facts. Load when removing a service from the platform.
category: process
durability: durable
---

The deprecation *sequence* below is reusable. Every concrete tool and path — how the service deploys, how secrets and DNS are managed, where manifests live — comes from the project's recipe and its active modules, not from this skill.

## Before removing a service

1. **Identify dependents.** Does any other service call this one? Is its data referenced elsewhere? Is there a volume with user data?
2. **Data disposition.** Decide: migrate, archive, or delete. User-facing data (photos, files, content) must be migrated or archived — never silently deleted.
3. **Grace period.** For user-facing services, communicate the sunset date before removal. For platform-internal services, coordinate with affected consumers.

## Removal sequence

### 1. Disable ingress

Remove or disable the route so traffic stops reaching the service while it keeps running. Confirm no live requests in the access logs before proceeding. Use the routing mechanism the project's gateway/ingress setup defines.

### 2. Scale down

Set the workload's replicas to 0 (or delete the workload directly if the service is being removed entirely).

### 3. Remove from the gitops reconciler

Through the recipe's gitops module (`recipe.tools.gitops` → its `tool-<module>`):

1. Remove the service's application/source entry from the gitops configuration
2. Let the reconciler detect the removed resource on the next sync
3. If prune is enabled, the reconciler deletes the in-cluster resources automatically
4. Verify the reconciler no longer lists the service

Never delete in-cluster resources out-of-band when a reconciler manages them — remove the source and let it prune (see the gitops module's deployment patterns).

### 4. Remove manifests

Delete the service's overlay, then its base — only if no other overlay still references the base. The manifest layout (base/overlay paths) is the project's; take the locations from the project, not from this skill.

### 5. Clean up the namespace

Once all workload resources are gone, delete the namespace. Volumes with a `Retain` reclaim policy leave orphan persistent volumes behind — verify and delete those manually only **after confirming the data is migrated or archived**. The reclaim-policy behaviour maps to the StorageClass in `recipe.facts` (`storage_fast` is typically Delete, `storage_bulk` typically Retain — confirm against the recipe).

### 6. Remove secrets

Through the recipe's secrets module (`recipe.tools.secrets`):

1. Delete the synced secret resource (the reconciler may have already pruned it)
2. Delete the materialized cluster Secret if it persists
3. Archive or delete the upstream secret-store item if nothing else references it

### 7. Remove DNS

Remove the service's DNS record using the project's DNS-management mechanism (often an IaC stage from `recipe.stack.iac`). Preview the change, then apply.

### 8. Archive documentation

Archive related knowledge in the project's memory substrate (the recipe's `memory` module): tag service-specific notes as archived and record the deprecation date. Git history is the record for removed code — don't leave tombstone files behind.

## Post-removal checklist

- [ ] No route / ingress for the service's domain
- [ ] No pods running in the namespace
- [ ] Namespace deleted
- [ ] No orphan persistent volumes
- [ ] Synced secret and materialized Secret deleted
- [ ] Upstream secret-store item archived or deleted
- [ ] DNS record removed
- [ ] Gitops reconciler no longer shows the service
- [ ] Documentation archived in the memory substrate

## Project values come from the recipe

- `recipe.tools.gitops` (and its `tool-<module>`) — how the service deploys and is pruned; never assume a specific reconciler.
- `recipe.tools.secrets` — the secret resource type and upstream store for secret cleanup.
- `recipe.tools.memory` — where deprecation notes are archived.
- `recipe.facts.storage_*` — StorageClass reclaim behaviour that decides whether orphan volumes survive namespace deletion.
- `recipe.stack.iac` — the DNS-management mechanism and its preview/apply commands.
- Manifest base/overlay paths come from the project; this skill names the *steps*, not the *paths*.
