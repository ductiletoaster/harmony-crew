---
name: ansible-conventions
description: Ansible role structure, inventory conventions, secret injection via op.env, and known gotchas (Jinja2/bash conflicts, nvidia-idle-power). Load when writing or modifying Ansible roles, playbooks, or inventory.
tier: subject
requires: []
audience: [crew]
---

## SSH and inventory

All Proxmox hosts use `ansible_user: harmony` — not root. The `harmony` user has SSH key authentication and passwordless sudo.

Inventory lives at `ansible/inventory/`. Host definitions include Proxmox nodes and the Omni VM.

## Secret injection

Secrets are never stored on disk. Inject at runtime via `op run`:

```bash
op run --env-file=ansible/op.env -- ansible-playbook playbooks/<playbook>.yml
```

`ansible/op.env` contains `op://` URI references — 1Password resolves them at invocation time. Never hardcode credentials in playbooks, vars files, or inventory.

## Role structure

Roles live under `ansible/roles/`. Key roles:

| Role | Purpose |
|---|---|
| `omni/` | Sidero Omni VM configuration (Docker, Traefik, Authentik, wolweb) |
| `proxmox_power/` | CPU governor (powersave), EEE, GPU hookscripts, nvidia-idle-power |

## nvidia-idle-power — critical gotcha

The `nvidia-idle-power` service unbinds GPUs from their current drivers to set minimum power limits. **Never use `state: started` or `state: restarted`** — this will hang or crash if VMs are actively using the GPU.

Correct usage:
```yaml
- name: Enable nvidia-idle-power
  ansible.builtin.systemd:
    name: nvidia-idle-power
    enabled: true
    daemon_reload: true
  # No 'state:' key — boot-only service, never started by Ansible
```

## Jinja2 / bash template conflict

Bash array syntax `${#array[@]}` conflicts with Jinja2's comment tag `{# ... #}`. In templates that mix bash and Jinja2, add this header:

```
#jinja2: comment_start_string:'{##', comment_end_string:'##}'
```

This remaps Jinja2's comment delimiters so `{#` is treated as literal bash.

## wolweb

Wake-on-LAN is handled by the `wolweb` container on the Omni VM, managed by `ansible/roles/omni/`. It is **not** a Kubernetes workload.

## Idempotency

All playbooks and roles must be safe to run repeatedly. Test with `--check` before applying to production hosts. Use `changed_when: false` for commands that are inherently read-only but trigger changed state in Ansible's model.
