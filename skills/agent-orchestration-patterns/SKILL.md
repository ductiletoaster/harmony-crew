---
name: agent-orchestration-patterns
description: How the Harmony agent runtime works end-to-end — Argo Workflows, Pydantic AI orchestrator, exit codes, result format, and retry behavior. Load when writing or debugging autonomous agent workflows.
tier: concept
requires: [cluster]
audience: [crew]
---

## Runtime architecture

Harmony's autonomous agent runtime has two layers:

**Claude Code CLI** — workstation-interactive sessions (`hmy agent run --local`). Subprocess model; stays subprocess permanently. Used for chat-mode collaboration and developer workflows.

**Argo Workflows + Pydantic AI** — in-cluster execution (`hmy agent run`). The default dispatch path. Argo Workflow templates manage lifecycle; Pydantic AI orchestrator script runs as the `execute-claude` step inside each Workflow pod.

## Argo Workflow structure

Workflows run in the `agent-platform` namespace. Key components:

- **WorkflowTemplate** — reusable template defining the agent execution steps
- **Workflow** — a single execution instance, triggered by `hmy agent run` or webhook
- **`execute-claude` step** — runs `orchestrator.py` in the project's agent-runner container

`maxWorkerInvocations: 1` is the default per Workflow (configurable via frontmatter).

**Kustomize image transform caveat:** Image transforms don't reach WorkflowTemplate CRDs. Pin image tags directly in workflow YAML files — don't rely on `kustomization.yaml` `images:` to propagate there.

## Pydantic AI orchestrator (`orchestrator.py`)

Entry point: `/opt/harmony/orchestrator.py`. Runs inside the runner image.

Key behaviors:
- Uses `AnthropicModel` or `OpenAIModel` via LiteLLM passthrough
- Routes through the in-cluster LiteLLM gateway (`ANTHROPIC_BASE_URL` → `http://<litellm-service>.<ns>.svc:4000/anthropic`; concrete service/namespace in the consumer's topology / access-map skill)
- Produces structured `AgentResult` to `/tmp/agent-result.json`
- Tools: memory substrate (see `memory-substrate`), filesystem (`bash`, `read_file`, `write_file`, `list_directory`)

## Exit codes

| Code | Meaning | Argo retry behavior |
|---|---|---|
| 0 | Success | No retry |
| 75 | Transient failure | Retry (configurable backoff) |
| 1 | Structural failure | No retry — escalate |

Exit 75 is the signal for "try again" — transient API errors, rate limits, temporary unavailability. Exit 1 means the task is structurally broken and human attention is needed.

## Agent result format

```json
{
  "summary": "what was accomplished",
  "status": "success | partial | failed",
  "artifacts": ["list of produced artifacts"],
  "issues_opened": [123, 124],
  "notes_written": ["vault/path/to/note.md"]
}
```

## Credentials in-cluster

Agents access cluster resources via scoped credentials:
- `KUBECONFIG` → `op://<vault>/<item>/<field>` (read-only SA; concrete path in the consumer's secret-management local skill)
- `TALOSCONFIG` → `op://<vault>/<item>/<field>` (cluster-management SA-derived; concrete path in the consumer's secret-management local skill)
- `ANTHROPIC_AUTH_TOKEN` → from `litellm-hmy-agents-key` ExternalSecret

Never use the operator's interactive credentials (`~/.kube/config`, `~/.talos/config`) in automated paths — they expire with the SSO session.

## hmy agent commands

```bash
hmy agent run                     # Dispatch workers for agent-labelled issues (cluster)
hmy agent run --local             # Workstation subprocess mode
hmy agent run --issue 42          # Process a single issue
hmy agent reconcile               # Rebase active agent branches onto main
```

## Webhook trigger

GitHub events route through the platform's public webhook endpoint (Cloudflare Tunnel → FastAPI listener on port 8000; the concrete hostname lives in the consumer's topology skill). The listener dispatches Argo Workflows in response to issue events.

```bash
hmy agent webhook start           # Start listener (localhost:8000)
hmy agent webhook status          # Check listener
hmy agent webhook stop            # Stop listener
```
