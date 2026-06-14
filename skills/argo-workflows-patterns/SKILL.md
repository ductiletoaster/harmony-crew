---
name: argo-workflows-patterns
description: Argo Workflows patterns for Harmony — WorkflowTemplate structure, exit codes, retry logic, and the agent-platform namespace conventions. Load when writing or debugging Argo Workflow templates for the autonomous agent runtime.
category: stack
durability: durable
---

## Namespace and setup

Autonomous agent workflows run in the `agent-platform` namespace. Argo Workflows v3.6+ is installed cluster-wide.

The runner image is `harmony-agent-runner` (versioned). It contains: `claude`, `node`, `git`, `gh`, `uv`, `hmy`. The `HARMONY_REPO_ROOT` env var is set to `/opt/harmony`.

## WorkflowTemplate structure

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: <template-name>
  namespace: agent-platform
  annotations:
    harmony.io/maxWorkerInvocations: "1"  # per-workflow invocation cap
spec:
  entrypoint: main
  templates:
    - name: main
      steps:
        - - name: execute-claude
            template: run-agent

    - name: run-agent
      container:
        image: ghcr.io/ductiletoaster/harmony-agent-runner:<tag>
        command: [uv, run, python, /opt/harmony/orchestrator.py]
        env:
          - name: ANTHROPIC_BASE_URL
            value: http://litellm.nexus.svc:4000/anthropic
          - name: ANTHROPIC_AUTH_TOKEN
            valueFrom:
              secretKeyRef:
                name: litellm-hmy-agents-key
                key: token
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
```

**Critical:** Image transforms do not reach WorkflowTemplate CRDs. Pin image tags directly in the YAML — do not rely on `kustomization.yaml` `images:` transforms.

## Exit codes and retry

| Exit code | Meaning | Argo action |
|---|---|---|
| 0 | Success | Mark step complete |
| 75 | Transient failure | Retry (configure in `retryStrategy`) |
| 1 | Structural failure | Fail immediately, no retry |

```yaml
retryStrategy:
  limit: "3"
  retryPolicy: OnError
  backoff:
    duration: "30s"
    factor: "2"
    maxDuration: "5m"
  expression: "exitCode == 75"
```

The `maxDuration` cap was removed from `execute-claude` retry in spec-022 — workflows can now run to natural completion.

## Workspace volumes

Each Workflow gets an ephemeral workspace volume (`harmony-runtime` StorageClass, ~1-5GB):

```yaml
volumeClaimTemplates:
  - metadata:
      name: workspace
    spec:
      accessModes: [ReadWriteOnce]
      storageClassName: harmony-runtime
      resources:
        requests:
          storage: 5Gi
```

Volumes are deleted on Workflow completion (`Delete` reclaim policy). Don't write anything to workspace that needs to persist — use the vault or GitHub.

## Triggering workflows

```bash
hmy agent run                     # Dispatch for all agent-labelled issues
hmy agent run --issue 42          # Single issue
```

Workflows can also be triggered by webhook events (GitHub issue labelled → FastAPI → Argo submit).

## PSA for agent-platform namespace

The `agent-platform` namespace uses `baseline` PodSecurity enforcement. Runner pods must comply — no hostNetwork, no hostPID, drop ALL capabilities.
