---
name: terraform-conventions
description: Terraform conventions for Harmony — bpg/proxmox provider, 1Password provider, variable structure, and stage separation. Load when writing or reviewing Terraform configurations.
tier: subject
requires: []
audience: [crew]
---

## Stage structure

```
infrastructure/terraform/
├── stage1-omni/    # Omni VM provisioning + DNS (Cloudflare)
├── stage2-talos/   # Talos VM provisioning
└── modules/        # Reusable Terraform modules
```

Stages must be applied in order: stage1 → stage2. Destroy in reverse. The `hmy infra` commands wrap the staging sequence.

## Providers

**bpg/proxmox** — Proxmox VE API provider. API-only, no SSH required from Terraform.

**1Password** — reads secrets at plan/apply time via `OP_SERVICE_ACCOUNT_TOKEN` env var:
```hcl
data "onepassword_item" "secret" {
  vault = "Harmony"
  title = "<item-name>"
}
```

Never hardcode secrets in `.tf` or `.tfvars` files.

## Variable conventions

**Centralized IPs:** All Proxmox node IPs are defined in `variables.tf` under `proxmox_nodes` — never inline literal IPs in resources.

**Shared non-sensitive config:** `common.tfvars` holds infrastructure constants shared across stages (IPs, node names, Cloudflare zone ID).

```hcl
# variables.tf
variable "proxmox_nodes" {
  type = map(object({
    host = string
    ip   = string
  }))
}
```

## Authentication

- Terraform authenticates to Proxmox via API token (not username/password)
- Secret read at runtime: `OP_SERVICE_ACCOUNT_TOKEN` provides access to the 1Password provider
- DNS (Cloudflare) credentials via 1Password provider or env vars at apply time

## Idempotency

All Terraform operations must be safe to run repeatedly. `terraform plan` on an already-applied state should show no diff for stable resources. Test with `terraform plan` before `apply`.

## Validation

```bash
terraform validate          # Syntax + schema check (no API calls)
terraform plan              # Show what would change
```

## Commands via hmy

```bash
hmy infra plan stage1       # terraform plan for stage1
hmy infra apply stage1      # terraform apply for stage1
hmy infra plan stage2       # terraform plan for stage2
hmy infra apply stage2      # terraform apply for stage2
hmy infra destroy stage2    # Destroy Talos VMs (safe to repeat)
hmy infra destroy stage1    # Destroy Omni VM (requires confirmation)
```
