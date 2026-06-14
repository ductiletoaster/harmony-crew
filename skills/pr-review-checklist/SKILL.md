---
name: pr-review-checklist
description: Structured checklist the reviewer runs against PRs across all surface types — application code, infrastructure manifests, IaC. Generic mechanism; concrete values and the seam set come from the project recipe. Load for every pre-merge review.
category: process
durability: cross-cutting
---

Every review opens with a one-sentence summary judgment (Pass / Pass with required changes / Block), then lists findings by category: Required, Recommended, Note.

The checklist below is the **reusable cross-surface review mechanism**. It names *categories* of checks, not project constants — every concrete value (StorageClass, fsGroup, secret-store name, lint/test commands) is read from the recipe, and the protected-seam set being checked is the recipe's, not a fixed list.

## Universal checks (all PRs)

- [ ] PR scope matches stated purpose — no unrelated changes bundled
- [ ] No secrets hardcoded in any changed file (tokens, passwords, API keys)
- [ ] Every entry in the project's seam registry (`recipe.seams`) checked — see `seam-detection`. State which seams were touched and whether the author flagged each crossing
- [ ] Commit message follows the project's commit format

## Application code (the recipe's `stack` language)

Run the project's lint, format, and test commands (from `stack.<lang>` — e.g. `lint`, `test`):

- [ ] Lint passes
- [ ] Format check passes (formatting is often a separate gate from lint)
- [ ] Tests pass
- [ ] New public functions/methods have a short docstring (one line, purpose only — no wall-of-text)
- [ ] No raw `print()` to stdout where the project uses a console/logging convention
- [ ] CLI commands declare their arguments/options with help strings
- [ ] MCP tools have precise descriptions (agents select tools by description)
- [ ] No parallel implementation of a capability that already exists on another surface — thin wrappers, not duplicate logic (see the project's interface-boundary rules)

## Infrastructure manifests (when the recipe activates a gitops / k8s module)

Take concrete values from `recipe.facts`; take the deploy/reconcile rules from the active tool module (`tool-argocd`, `tool-flux`, …).

- [ ] Required scheduling constraint present on every workload — toleration / node-selector keys from `facts.tolerations`
- [ ] StorageClass matches data type: `facts.storage_fast` for databases/ephemeral, `facts.storage_bulk` for user data/media
- [ ] Pod security context matches platform conventions: `fsGroup` from `facts.fsGroup`, non-root, hardened seccomp profile
- [ ] Capabilities dropped (`drop: [ALL]`) unless a specific capability is justified
- [ ] No hardcoded secrets — secrets flow through the recipe's `secrets` module (e.g. ExternalSecret / SealedSecret) referencing the configured store
- [ ] Secret resources follow the secrets module's contract (refresh interval, deletion policy) and have a same-PR consumer (no speculative secrets)
- [ ] Accelerated workloads (GPU, etc.) declare their resource request + runtime class in the overlay, not the base
- [ ] The manifest build passes (e.g. `kubectl kustomize build <overlay>`) without error
- [ ] Namespaces requiring elevated PodSecurity keep it; don't silently downgrade

## IaC (when the recipe's `stack.iac` is set)

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
- Which (if any) `recipe.seams` entries were touched
- Whether each crossing was flagged by the author
- Whether operator sign-off is needed before merge (see `seam-alert-routing`)

## Project values come from the recipe

This skill is the *generic checklist*. It applies **the project's** values, never hard-coded ones:

- `recipe.stack.<lang>` — lint / format / test commands for the application-code checks
- `recipe.stack.iac` — the IaC tool and its validate command
- `recipe.facts` — `storage_fast`, `storage_bulk`, `fsGroup`, `tolerations`, `runtimes`, `domains`
- `recipe.tools.secrets` — the secret store and its contract (refresh/deletion policy)
- `recipe.tools.gitops` (and its `tool-<module>`) — how manifests deploy and the manifest-build command
- `recipe.seams` — the project's protected-seam registry to check each PR against

Never carry another project's StorageClass, fsGroup, store name, or seam list into a review.
