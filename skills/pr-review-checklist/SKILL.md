---
name: pr-review-checklist
description: Structured checklist the reviewer runs against PRs across all surface types — application code, infrastructure manifests, IaC. Generic mechanism; concrete values and the seam set are project-specific. Load for every pre-merge review.
category: process
durability: cross-cutting
---

Every review opens with a one-sentence summary judgment (Pass / Pass with required changes / Block), then lists findings by category: Required, Recommended, Note.

The checklist below is the **reusable cross-surface review mechanism**. It names *categories* of checks, not project constants — every concrete value (StorageClass, fsGroup, secret-store name, lint/test commands) is project-specific, and the protected-seam set being checked is the project's, not a fixed list.

## Universal checks (all PRs)

- [ ] PR scope matches stated purpose — no unrelated changes bundled
- [ ] No secrets hardcoded in any changed file (tokens, passwords, API keys)
- [ ] Every entry in the project's seam registry (the protected-seam-registry) checked — see `seam-detection`. State which seams were touched and whether the author flagged each crossing
- [ ] Commit message follows the project's commit format

## Application code (the project's stack language)

Run the project's lint, format, and test commands (project-specific — e.g. lint, format, test):

- [ ] Lint passes
- [ ] Format check passes (formatting is often a separate gate from lint)
- [ ] Tests pass
- [ ] New public functions/methods have a short docstring (one line, purpose only — no wall-of-text)
- [ ] No raw `print()` to stdout where the project uses a console/logging convention
- [ ] CLI commands declare their arguments/options with help strings
- [ ] MCP tools have precise descriptions (agents select tools by description)
- [ ] No parallel implementation of a capability that already exists on another surface — thin wrappers, not duplicate logic (see the project's interface-boundary rules)

## Infrastructure manifests (when the project uses a gitops / k8s module)

Take concrete values from the project's config; take the deploy/reconcile rules from the active tool module (e.g. an argocd or flux module).

- [ ] Required scheduling constraint present on every workload — project-specific toleration / node-selector keys
- [ ] StorageClass matches data type: the fast tier for databases/ephemeral, the bulk tier for user data/media (tiers project-specific)
- [ ] Pod security context matches platform conventions: project-specific `fsGroup`, non-root, hardened seccomp profile
- [ ] Capabilities dropped (`drop: [ALL]`) unless a specific capability is justified
- [ ] No hardcoded secrets — secrets flow through the project's secrets module (e.g. ExternalSecret / SealedSecret) referencing the configured store
- [ ] Secret resources follow the secrets module's contract (refresh interval, deletion policy) and have a same-PR consumer (no speculative secrets)
- [ ] Accelerated workloads (GPU, etc.) declare their resource request + runtime class in the overlay, not the base
- [ ] The manifest build passes (e.g. `kubectl kustomize build <overlay>`) without error
- [ ] Namespaces requiring elevated PodSecurity keep it; don't silently downgrade

## IaC (when the project uses IaC)

- [ ] The IaC tool's validate command passes (`terraform validate`, etc.)
- [ ] No secrets in variable files or HCL/templates — use the project's secret-injection pattern
- [ ] Environment-specific values come from variables, not inline literals
- [ ] Non-sensitive shared config lives in the project's shared vars file
- [ ] Changes are idempotent — a plan against already-applied state shows no diff

## Config-management runs (Ansible / equivalent, when active)

- [ ] No secrets in playbooks, vars files, or inventory — use the project's runtime secret-injection pattern
- [ ] Connection identity matches the project's convention
- [ ] Tasks are idempotent — safe to run twice
- [ ] Templates that mix shell and templating syntax carry the delimiter-remap guard

## Seam check summary

After completing surface-specific checks, explicitly state:
- Which (if any) protected-seam-registry entries were touched
- Whether each crossing was flagged by the author
- Whether operator sign-off is needed before merge (see `seam-alert-routing`)

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, …) are project-specific. The
consuming project supplies them — in its own overlay skills or the agent's working context. This
skill is the generic pattern.

This skill is the *generic checklist*. It applies **the project's** values, never hard-coded ones:

- lint / format / test commands for the application-code checks — project-specific (the project's stack config)
- the IaC tool and its validate command — project-specific (the project's stack config)
- `storage_fast`, `storage_bulk`, `fsGroup`, `tolerations`, `runtimes`, `domains` — project-specific
- the secret store and its contract (refresh/deletion policy) — project-specific (the project's secrets module)
- how manifests deploy and the manifest-build command — project-specific (the project's gitops module)
- the project's protected-seam registry to check each PR against — project-specific

Never carry another project's StorageClass, fsGroup, store name, or seam list into a review.
