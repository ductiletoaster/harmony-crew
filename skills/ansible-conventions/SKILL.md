---
name: ansible-conventions
description: Generic Ansible conventions — role/playbook structure, inventory, runtime secret injection (never on disk), idempotency, and the Jinja2/bash template-conflict fix. Applies the project's user/inventory/secret-tool (project-specific values). Load when writing or modifying Ansible.
category: stack
durability: durable
---

Generic Ansible convention pattern. The *structure* and *disciplines* below are fixed; the
concrete SSH user, inventory layout, secret-injection command, and role names are
project-specific — never hard-code them.

## SSH and inventory

Hosts are reached over SSH as a **dedicated automation user** (not root) with key auth and
passwordless sudo. The username is the project's own — it is project-specific (supplied by the
project); don't assume a name.

```yaml
# inventory — the user is a project value, not a constant
all:
  vars:
    ansible_user: <automation-user>   # project-specific
```

Inventory lives under the project's `ansible/inventory/`. Host definitions cover the managed
nodes the project actually runs.

## Secret injection — runtime only, never on disk

Secrets are **never** stored in playbooks, vars files, or inventory. Inject them at runtime by
wrapping the playbook invocation in the project's secret tool, which resolves secret references
into the process environment for the lifetime of the run:

```bash
<secret-tool> run --env-file=<project-secret-env> -- ansible-playbook playbooks/<playbook>.yml
```

The env file contains **reference URIs** in the store's own scheme (e.g. a `<store>://…` path),
not secret values — the secret tool resolves them at invocation time. The tool, the env-file
path, and the reference scheme all come from the project's secrets configuration. This is
the secrets-resolved-at-runtime rule: nothing sensitive ever lands in the repo or on disk.

## Role structure

Roles live under `ansible/roles/`, one directory per role, each self-contained
(`tasks/`, `handlers/`, `templates/`, `defaults/`). The project's role set is its own — name
roles after what they configure, keep them single-purpose, and let playbooks compose them.

## Boot-only / hardware-touching services — handle with care

Some services must be **enabled but never started by Ansible** — typically ones that rebind
hardware, drop into a one-shot at boot, or would disrupt running workloads if cycled mid-run. For
these, set `enabled: true` and **omit `state:`** entirely:

```yaml
- name: Enable a boot-only service
  ansible.builtin.systemd:
    name: <service>
    enabled: true
    daemon_reload: true
  # No 'state:' key — let it activate on next boot; never start/restart it live
```

Reach for this pattern whenever starting a service in-flight could hang or crash active work
(GPU/driver rebinds are the classic case). Which services qualify is project-specific.

## Jinja2 / bash template conflict

Bash array syntax `${#array[@]}` collides with Jinja2's comment tag `{# ... #}`. In any template
mixing bash and Jinja2, remap Jinja2's comment delimiters with this header so `{#` is treated as
literal bash:

```
#jinja2: comment_start_string:'{##', comment_end_string:'##}'
```

## Idempotency

All playbooks and roles must be safe to run repeatedly. Test with `--check` before applying to
production hosts. Use `changed_when: false` for commands that are inherently read-only but
otherwise report a changed state in Ansible's model.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, …) are project-specific. The
consuming project supplies them — in its own overlay skills or the agent's working context. This
skill is the generic pattern.

| Need | Source |
|---|---|
| SSH automation user | project-specific (the project's infrastructure config) |
| Secret-injection tool + env-file path + reference scheme | the project's secrets configuration |
| Inventory hosts / role set | the project's own `ansible/` tree |
| Which services are boot-only / hardware-touching | project-specific (role notes) |

This skill owns the Ansible disciplines; the project supplies the user, the secret tool, and the
role set.
