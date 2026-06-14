---
name: litellm-routing-model
description: LiteLLM gateway auth model — virtual keys, teams, MCP access groups, and the per-surface tool-budget taxonomy. Load before touching VK scopes, MCP server registrations, or adding a consumer surface.
---

# LiteLLM Routing Model

The LiteLLM gateway (`litellm.lab.pixeloven.com`, in-cluster `litellm.nexus.svc.cluster.local:4000`) is both the LLM router and the MCP federation point. One bearer credential — a virtual key (VK) — carries both concerns: model routing and MCP tool scope.

## Two-level MCP access enforcement

Tool visibility on `/mcp` is the intersection of three things:

1. **Server → groups.** Each MCP upstream is registered in the LiteLLM configmap (`infrastructure/kubernetes/base/nexus/litellm/configmap.yaml`, `mcp_servers:` block) with `access_groups`. Config-as-code — change via PR, not the admin UI.
2. **Team → allowed groups.** The team's `object_permission.mcp_access_groups` is the allowlist a member VK can opt into. One team today: `harmony-public`. DB entity — managed via `/team/update` with the master key.
3. **VK → opted-in groups.** The key's `object_permission.mcp_access_groups`. A VK with no groups set inherits the team's full allowlist — that is the over-broad default #747 removed; always set groups explicitly on new VKs.

After `/team/update`, the proxy's permission cache needs one retried request before changes take effect.

## Group taxonomy (#747)

| Group | Servers | Meaning |
|-------|---------|---------|
| `public` | all | Full operator surface. Workstation VK only — never give it to a pod. |
| `ops` | argocd | Cluster operations |
| `knowledge` | vault, qmd_search | Memory substrate + search |
| `imagegen` | comfyui | Image generation (~100 tools — the main prompt-budget hazard) |
| `companions` | vault, qmd_search | Companion-facing subset |
| `search` | qmd_search | Minimum-consequence floor: 4 read-only search tools. For VKs that need no MCP at all — **a group matching zero servers is treated as UNRESTRICTED in v1.86.2**, so "no tools" cannot be expressed via groups; `search` is the safe floor instead. |

## Surfaces → VKs

| VK alias (1P field, `op://Harmony/LiteLLM/*`) | Consumer | Groups |
|---|---|---|
| `workstation_key` | Claude Code `.mcp.json` (`LITELLM_API_KEY` in fish env) | `[public]` |
| `hmy_agents_key` | pi-worker pods: homelab-agents CronJob, agent-platform WorkflowTemplate, pi-web/pi-worker | `[ops, knowledge]` |
| `openclaw_agents_key` | OpenClaw operator squad | `[ops, knowledge]` |
| `openclaw_companions_key` | Companions (Vesper, Echo) | `[companions]` |
| `openwebui_key` | Open WebUI | `[search]` today; add `imagegen` when #746 Path B lands |
| `hmy_memory_key` | vault-mcp extraction LLM | `[search]` — LLM-only consumer; `search` is the no-MCP floor |

## Rules

- **New consumer surface → new VK** with explicit groups, named field in the 1P `LiteLLM` item, ESO entry only if a pod mounts it (same-PR consumer rule).
- **Small-context local models** need tightly-scoped groups — the full `[public]` catalog overflows a 32k prompt before user input (see `feedback_local_model_tool_budget`).
- **Admin operations** use the master key (`op://Harmony/LiteLLM/master_key`) against `/key/*`, `/team/*`. Never echo keys into output; pass via env var.
- **MCP servers** live in the configmap, not the DB — `PUT /v1/mcp/server` 404s on config-defined servers. Edit the configmap and restart the deployment.
- Model aliases: bare names (`gpt-5.4-mini`) are canonical; `model_group_alias` maps provider-prefixed forms. Per-backend prefixes for local engines (`llamacpp/*`, `ollama/*`) — see `feedback_litellm_model_namespacing`.
