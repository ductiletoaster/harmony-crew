---
name: argo-workflows-patterns
description: Argo WorkflowTemplate authoring for agent dispatch — template/step structure, the runner container spec, the retryStrategy keyed on the exit-code contract, and the ephemeral workspace volume. For projects whose autonomous runtime uses Argo Workflows. The pod toleration / runtime-class / securityContext shape is deferred to k8s-workload-patterns. Load when writing or debugging an agent-dispatch WorkflowTemplate.
category: stack
durability: durable
---

Generic Argo WorkflowTemplate authoring for the agent runtime. **Activation:** load this only when
the project's autonomous runtime uses Argo Workflows (a project on a different engine — Tekton, etc. —
authors against that engine instead; the *contract* it implements is still
`agent-orchestration-patterns`). **This skill owns the WorkflowTemplate skeleton**; the project
supplies every scalar. The pod-level toleration, `securityContext`,
and `runtimeClassName` are **not owned here** — that block shape is `k8s-workload-patterns`; fill
it from the project's platform conventions and drop it into the container template.

## Setup

Agent workflows run in `runtime.namespace`. The runner image is `runtime.runner_image` (versioned)
— it carries the agent CLI, the toolchain (`git`, the project CLI, the LLM client), and exposes the
cloned repo path via the env var named in `runtime.repo_root_env`.

## WorkflowTemplate structure

The template/step skeleton is fixed; only the project-specific scalars vary. The pod scheduling/security
block (`tolerations`, `securityContext`, optional `runtimeClassName`) is the
`k8s-workload-patterns` shape — shown abbreviated here, authored there:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: <runtime.workflow_template>
  namespace: <runtime.namespace>
spec:
  entrypoint: main
  templates:
    - name: main
      steps:
        - - name: run-agent
            template: run-agent

    - name: run-agent
      container:
        image: <runtime.runner_image>:<tag>      # pin the tag — see the caveat below
        command: [ "<agent entry point>" ]
        env:
          - name: <runtime.repo_root_env>
            value: <clone path inside the runner>
          - name: <LLM/MCP gateway base URL>
            value: <runtime.gateway>             # resolve per tool-litellm / the gateway module
          # gateway token + scoped cluster creds: secretKeyRef from the project secret store
        resources:
          requests: { cpu: "500m", memory: "1Gi" }
          limits:   { cpu: "2000m", memory: "4Gi" }
      # tolerations / securityContext / runtimeClassName: the k8s-workload-patterns block,
      # filled from facts.tolerations, facts.fsGroup, facts.runtimes — NOT hand-rolled here.
```

**Critical — image transforms don't reach WorkflowTemplate CRDs.** Kustomize `images:` transforms
do not propagate into a `WorkflowTemplate`. Pin the runner image tag **directly in the YAML**;
do not rely on `kustomization.yaml` `images:` to set it.

## Exit codes and retryStrategy

The exit codes are the `agent-orchestration-patterns` contract; the `retryStrategy` is how Argo
*acts* on them. Retry **only** the transient code:

| Exit code | Meaning | Argo action |
|---|---|---|
| `0` | Success | Mark the step complete |
| `75` | Transient failure | Retry (per `retryStrategy`) |
| `1` | Structural failure | Fail immediately, no retry |

```yaml
retryStrategy:
  limit: "3"
  retryPolicy: OnError
  backoff:
    duration: "30s"
    factor: "2"
  expression: "exitCode == 75"
```

Don't put a hard `maxDuration` on the agent step itself — a healthy run is allowed to reach
natural completion. Bound the *retry* window, not the run.

## Ephemeral workspace volume

Each Workflow gets an ephemeral workspace volume on the runtime's runtime-tier StorageClass:

```yaml
volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes: [ ReadWriteOnce ]
      storageClassName: <runtime.storage_class>     # the ephemeral-workspace class
      resources:
        requests:
          storage: 5Gi
```

The volume is **deleted on Workflow completion** (the runtime-tier class is `Delete` reclaim).
Nothing written to workspace survives the run — persist to the vault or the git remote, never to
the workspace PVC.

## Triggering

```bash
<identity.cli> agent run                 # dispatch for all agent-labelled work items
<identity.cli> agent run --issue 42      # single work item
```

A source-control webhook can also submit the same `runtime.workflow_template` (event → listener →
Argo submit). One template, two front doors — see `agent-orchestration-patterns`.

## Namespace PodSecurity

The runner pod must satisfy the `runtime.namespace` PodSecurity level. The default agent runner
needs nothing privileged: no `hostNetwork`, no `hostPID`, drop ALL capabilities — which is exactly
the `k8s-workload-patterns` security-context skeleton, so a runner authored against that block
complies with a `baseline` (or stricter) namespace by construction.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, the protected-seam registry, …)
are project-specific. The consuming project supplies them — in its own overlay skills or the
agent's working context. This skill is the generic pattern.

| Need | Source |
|---|---|
| Workflow template name | the project's agent-runtime config |
| Namespace | the project's agent-runtime config |
| Runner image | the project's agent-runtime config |
| Repo-root env var | the project's agent-runtime config |
| LLM/MCP gateway URL | the project's agent-runtime config |
| Ephemeral workspace StorageClass | the project's agent-runtime config |
| Toleration key / `fsGroup` / runtime classes (the pod block) | the project's platform conventions/config — via `k8s-workload-patterns` |
| Dispatch verb | `identity.cli` |

This skill owns the WorkflowTemplate skeleton and the retry shape; the project supplies the
runtime scalars, and the pod scheduling/security block is deferred to `k8s-workload-patterns`.
