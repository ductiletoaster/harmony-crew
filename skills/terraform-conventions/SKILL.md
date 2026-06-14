---
name: terraform-conventions
description: Generic Terraform conventions — staged module structure, secret-provider reads at plan/apply time, centralized variables, idempotency. Applies the project's stages + providers from the recipe's stack.iac. Load when writing or reviewing Terraform.
category: stack
durability: durable
---

Generic Terraform convention pattern. The *structure* and *discipline* below are fixed; the
concrete stage names, providers, and IaC commands come from the recipe's `stack.iac` (and the
relevant `tools.*` entries for secret-backing providers) — never hard-code them.

## Stage structure

When `stack.iac.tool: terraform`, the project's infrastructure is split into **ordered stages**,
declared in `stack.iac.stages`. Each stage is an independently-applied root module; shared logic
lives in reusable modules:

```
<iac-root>/
├── <stage-1>/    # first stage in stack.iac.stages
├── <stage-2>/    # second stage — depends on stage-1's outputs
└── modules/      # reusable Terraform modules shared across stages
```

Apply stages **in `stack.iac.stages` order**; destroy in reverse. If the project ships a task
CLI (`identity.cli`), it wraps the staging sequence — invoke stages through it rather than running
`terraform apply` per directory by hand.

## Providers

Read provider names from the recipe — `stack.iac.notes` and the active `tools.*` entries name the
project's infrastructure provider(s) and secret-backing provider:

- **Infrastructure provider** (the thing Terraform provisions — a hypervisor, a cloud, a DNS
  zone): named in `stack.iac.notes`. Authenticate via API token, never username/password.
- **Secret-backing provider** (resolves secret references at plan/apply time): take its name and
  the auth ref from the recipe's `secrets`-role `tools.*` entry. The provider reads secrets at
  runtime via the token in that entry's `.auth`:

```hcl
data "<secret_provider>_item" "secret" {
  vault = "<store-from-recipe>"
  title = "<item-name>"
}
```

Never hardcode secrets in `.tf` or `.tfvars` files.

## Variable conventions

- **Centralized identifiers.** Every host/node IP, name, or endpoint is defined once in
  `variables.tf` (e.g. a `nodes` map) — never inline a literal IP in a resource.
- **Shared non-sensitive config** lives in a common `.tfvars` (e.g. `common.tfvars`): the
  infrastructure constants shared across stages (IPs, node names, DNS zone IDs).

```hcl
# variables.tf
variable "nodes" {
  type = map(object({
    host = string
    ip   = string
  }))
}
```

## Authentication

- Terraform authenticates to the infrastructure provider via an API token.
- The secret-backing provider's token (the recipe's secrets-entry `.auth`) is exported into the
  environment at runtime — never written to disk, never committed.
- DNS / external-service credentials likewise flow through the secret provider or env vars at
  apply time.

## Idempotency

All Terraform operations must be safe to run repeatedly. `terraform plan` on an already-applied
state shows no diff for stable resources. Test with `plan` before `apply`.

## Validation

```bash
terraform validate          # syntax + schema check, no API calls
terraform plan              # show what would change
```

## Commands

Run staged operations through the project's task CLI when one is declared (`identity.cli`):

```bash
<cli> <infra-verb> plan <stage>      # terraform plan for a named stage
<cli> <infra-verb> apply <stage>     # terraform apply for a named stage
<cli> <infra-verb> destroy <stage>   # destroy a stage (reverse order; later stages first)
```

The verb and subcommands are the project's own; the *stage-ordered* discipline is the pattern.

## Project values come from the recipe

| Need | Source |
|---|---|
| IaC tool (this skill assumes `terraform`) | `stack.iac.tool` |
| Stage names + apply order | `stack.iac.stages` |
| Infrastructure provider | `stack.iac.notes` |
| Secret-backing provider + store name + auth ref | the secrets-role `tools.*` entry (`.store`, `.auth`, `.prefix`) |
| IaC root directory | the project's own tree |
| Task-CLI verb that wraps the stages | `identity.cli` |

This skill owns the staged-module discipline; the recipe owns the stage names and providers.
