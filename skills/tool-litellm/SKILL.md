---
name: tool-litellm
description: Operating a LiteLLM gateway as an agent — LLM inference routing plus MCP tool federation. Load this when the project uses LiteLLM.
---

Generic LiteLLM gateway operating pattern. Load this when the project uses LiteLLM. The
project provides the gateway endpoint and auth ref (env vars, mounted secrets, or its
overlay) — never hard-code them.

## This module is the dependency root

LiteLLM is both the **LLM router** and the **MCP federation point**. Every other tool module
that reaches its tool surface via an `mcp:` prefix (ArgoCD reads, the vault substrate, ComfyUI,
SearXNG, …) federates *through this gateway*. So:

- **If any active module has an `mcp:` field, this module must be loaded and its gateway
  reachable first.** A `vault-*` or `comfyui-*` call is a call into the LiteLLM `/mcp`
  endpoint, authenticated by this gateway's credential. No gateway, no federated tools.
- The gateway credential is one bearer token (a virtual key) that carries **both** concerns:
  which models the caller may route to, and which federated MCP tools the caller may see.

## Surfaces

- **LLM inference** = OpenAI-compatible chat/completions against the gateway endpoint, model
  selected by alias. This is how role agents that name a `litellm:<model>` reach a model.
- **MCP federation** = the gateway's `/mcp` endpoint exposes each registered upstream's tools
  under a `<prefix>-*` namespace (e.g. `argocd-list_applications`, `vault_writeNote`,
  `comfyui-generate_image`). The prefix for a given upstream is project-specific (supplied by
  the project's gateway config).

Both surfaces authenticate with the same bearer credential — the project-supplied gateway auth.

## Conventions (project-agnostic)

- **One credential, two scopes.** The virtual key carries LLM-routing scope and MCP-tool
  scope together. Send it as `Authorization: Bearer <key>` in the MCP client config; individual
  federated tool calls then need no extra credentials.
- **Tool visibility is the intersection of server registration and the key's grant.** A
  federated tool only appears if its upstream is registered on the gateway *and* the key is
  scoped to that upstream's access group. A key scoped to nothing broad still only sees what
  it's granted.
- **Mind the prompt budget on small-context models.** The full federated catalogue can overflow
  a small-context model's prompt before user input. Scope the key to just the upstreams the
  agent needs rather than the everything-group default.
- **Server registration is config-as-code, not a live API.** MCP upstreams are declared in the
  gateway's config; add/change an upstream by PR against that config, not by a runtime call.
- **Never echo the key into output.** Pass it via env var; treat it like any other secret.

## Everything project-specific is supplied by the project

| Need | Source |
|------|--------|
| Gateway endpoint (inference + `/mcp`) | project-specific (env var, mounted secret, or overlay) |
| Bearer credential (LLM + MCP scope) | project-specific (env var, mounted secret, or overlay) |
| Which upstreams are federated, and their prefixes | project-specific (the project's gateway config) |
| Model aliases, VK scoping quirks, group taxonomy | project-specific (the project's overlay/notes) |

This module is the entire LiteLLM-specific surface, and the federation root the `mcp:`-using
modules depend on. To make LiteLLM work for a new project, that project supplies the endpoint
and auth in its own overlay or context — it writes no gateway skill of its own.
