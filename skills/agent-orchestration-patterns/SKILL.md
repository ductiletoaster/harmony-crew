---
name: agent-orchestration-patterns
description: The autonomous agent-runtime contract — how a single agent run is dispatched (acquire-workspace → run-agent → push-and-PR → report), the exit-code contract, the result format, and retry behaviour. Distinct from orchestration-patterns (which is Lead's multi-agent dispatch). Load when writing or debugging the execution platform itself.
category: domain
durability: durable
---

Generic agent-runtime contract. **This skill owns the run lifecycle and the exit-code/result
contract** — the shape every dispatch of a single autonomous agent follows, independent of which
workflow engine runs it. The concrete platform scalars (orchestrator, namespace, runner image,
gateway, workspace storage class, repo-root env var, workflow template) all come from the recipe
`runtime:` block. This is the *execution-platform* contract; multi-agent worker composition (when
Lead fans work out across several agents) is `orchestration-patterns` — keep them separate.

## Two dispatch modes

| Mode | Where it runs | When |
|---|---|---|
| **Local subprocess** | The operator's workstation, interactive | Chat-mode collaboration and developer workflows; stays a subprocess permanently |
| **In-cluster runtime** | The `runtime:` orchestrator, unattended | The default unattended dispatch path — a workflow manages lifecycle, the agent runs inside the runner container |

The CLI entry point is the project task CLI (`identity.cli`), e.g. `<identity.cli> agent run` for
the in-cluster path and `<identity.cli> agent run --local` for the subprocess path.

## Run lifecycle — the workflow step contract

An in-cluster run is a sequence of steps the orchestrator drives. The **step shape is fixed**;
only the engine that schedules them and the scalars they reference vary:

1. **acquire-workspace** — provision a fresh, ephemeral workspace volume and clone the repo into
   it. The runner finds the clone path via the env var named in `runtime.repo_root_env`. The
   workspace PVC uses `runtime.storage_class`; it is **ephemeral** — `Delete` reclaim, nothing
   written there survives the run. Persist to the vault or to the git remote, never to workspace.
2. **run-agent** — execute the agent inside the `runtime.runner_image` container, in
   `runtime.namespace`, routing LLM/MCP traffic through `runtime.gateway`. The agent does the
   task and writes a structured result (below).
3. **push-and-pr** — push the work branch and open a PR. Every run operates on a **fresh branch**
   so re-dispatch is idempotent.
4. **report-success / report-failure** — an exit handler keyed on the run's exit code: on success,
   surface the result; on failure, escalate per the exit-code contract.

Each step's success/failure is decided by the exit-code contract, not by inspecting logs.

## Exit-code contract

The exit codes are the **interface between the agent and the orchestrator** — they are fixed and
engine-independent:

| Code | Meaning | Orchestrator action |
|---|---|---|
| `0` | Success | Mark the step complete; proceed |
| `75` | Transient failure | Retry with backoff — network blip, rate limit, temporary unavailability |
| `1` | Structural failure | No retry — escalate to a human; the task is broken |

`75` is the only "try again" signal. `1` means the task is structurally broken and needs human
attention — retrying it just burns budget. An agent that silently exits `0` while producing wrong
output is worse than a clean `1`: **validate the output before returning `0`.**

## Result format

Every run writes a structured result to a known location (the local agent-result path the runner
exposes), parseable by the exit handler without re-reading the agent's full transcript:

```json
{
  "summary": "what was accomplished",
  "status": "success | partial | failed",
  "artifacts": ["list of produced artifacts"],
  "issues_opened": [123, 124],
  "notes_written": ["path/to/note"]
}
```

`summary` + `status` + `artifacts` are the minimum. The handler routes on `status`; the rest is
provenance for the next phase.

## Retry behaviour

Retry is driven entirely by the exit-code contract: the orchestrator retries **only** on `75`,
with bounded backoff. Do not retry on `1`, and do not retry on `0`. A run is allowed to reach
natural completion — don't cap a healthy run with a hard duration limit; cap only the *retry*
window. (The engine-level `retryStrategy` shape is in `argo-workflows-patterns`.)

## Credentials in the runtime

The runner uses **scoped, non-interactive credentials** resolved from the project's secret store,
never the operator's interactive session credentials (those expire with the SSO session and don't
belong in an unattended path). The LLM/MCP gateway token, cluster read credentials, and any
node-access credentials are injected into the runner container as env/secret refs — see the tool
modules (`tool-litellm`, the secrets module) and `secret-management-patterns` for resolution.

## Triggering a run

```bash
<identity.cli> agent run                 # dispatch for all agent-labelled work items (in-cluster)
<identity.cli> agent run --local         # workstation subprocess mode
<identity.cli> agent run --issue 42      # process a single work item
```

Runs can also be triggered by a source-control webhook: an event (e.g. an issue gets an
agent label) reaches a listener that submits a workflow to the `runtime.orchestrator`. The
listener and the CLI submit the **same** workflow template (`runtime.workflow_template`) — there
is one dispatch path, two front doors.

## Project values come from the recipe

| Need | Source |
|---|---|
| Workflow engine that schedules the steps | `runtime.orchestrator` |
| Namespace the run executes in | `runtime.namespace` |
| Runner container image | `runtime.runner_image` |
| Env var holding the cloned-repo path | `runtime.repo_root_env` |
| The workflow template both front doors submit | `runtime.workflow_template` |
| LLM/MCP gateway the runner routes through | `runtime.gateway` |
| Ephemeral workspace PVC class | `runtime.storage_class` |
| The task-CLI dispatch verb | `identity.cli` |

This skill owns the lifecycle, the exit-code contract, and the result format — they are identical
across projects. The recipe supplies only *where* the run executes and *what* image carries it.
