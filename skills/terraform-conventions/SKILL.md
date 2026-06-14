---
name: terraform-conventions
description: Generic Terraform conventions — staged module structure, secret-provider reads at plan/apply time, centralized variables, idempotency. Applies the project's stages + providers (project-specific stack config). Load when writing or reviewing Terraform.
category: stack
durability: durable
---

Generic Terraform convention pattern. The *structure* and *discipline* below are fixed; the
concrete stage names, providers, and IaC commands are project-specific (the project's stack config
and its secret-backing provider config) — never hard-code them.

## Stage structure

When the project uses Terraform, its infrastructure is split into **ordered stages**,
declared in the project's stack config. Each stage is an independently-applied root module; shared
logic lives in reusable modules:

```
<iac-root>/
├── <stage-1>/    # first stage in the project's stage list
├── <stage-2>/    # second stage — depends on stage-1's outputs
└── modules/      # reusable Terraform modules shared across stages
```

Apply stages **in the project's declared stage order**; destroy in reverse. If the project ships a
task CLI, it wraps the staging sequence — invoke stages through it rather than running
`terraform apply` per directory by hand.

## Providers

Read provider names from the project's stack config and its configured tools — they name the
project's infrastructure provider(s) and secret-backing provider:

- **Infrastructure provider** (the thing Terraform provisions — a hypervisor, a cloud, a DNS
  zone): project-specific (named in the project's stack config). Authenticate via API token, never
  username/password.
- **Secret-backing provider** (resolves secret references at plan/apply time): its name and
  the auth ref are project-specific (from the project's secrets configuration). The provider reads
  secrets at runtime via the token in that entry's `.auth`:

```hcl
data "<secret_provider>_item" "secret" {
  vault = "<store>"   # project-specific
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
- The secret-backing provider's token (project-specific, from the project's secrets configuration)
  is exported into the environment at runtime — never written to disk, never committed.
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

Run staged operations through the project's task CLI when one is declared:

```bash
<cli> <infra-verb> plan <stage>      # terraform plan for a named stage
<cli> <infra-verb> apply <stage>     # terraform apply for a named stage
<cli> <infra-verb> destroy <stage>   # destroy a stage (reverse order; later stages first)
```

The verb and subcommands are the project's own; the *stage-ordered* discipline is the pattern.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, …) are project-specific. The
consuming project supplies them — in its own overlay skills or the agent's working context. This
skill is the generic pattern.

| Need | Source |
|---|---|
| IaC tool (this skill assumes `terraform`) | project-specific (the project's stack config) |
| Stage names + apply order | project-specific (the project's stack config) |
| Infrastructure provider | project-specific (the project's stack config) |
| Secret-backing provider + store name + auth ref | the project's secrets configuration |
| IaC root directory | the project's own tree |
| Task-CLI verb that wraps the stages | project-specific |

This skill owns the staged-module discipline; the project supplies the stage names and providers.
