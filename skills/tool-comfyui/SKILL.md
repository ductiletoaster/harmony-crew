---
name: tool-comfyui
description: Operating ComfyUI as an agent for media generation — images, audio, and custom workflows — through the comfyui-* MCP surface. Active only when the project recipe declares a tools.* entry whose module = comfyui; reads the mcp prefix from that entry.
---

Generic ComfyUI media-generation operating pattern. **Activation:** load this only when the recipe
has a `tools.*` entry whose `module` is `comfyui` (the recipe author chooses the role key — it's
commonly `media`, but read the module value, not the key). Take the MCP prefix from **that comfyui
entry's** `.mcp` — never hard-code it.

> The federated MCP surface depends on `tool-litellm` (the gateway). Load that module first; the
> `comfyui-*` calls below route through the gateway's `/mcp` endpoint.

## When to use

Creative / media generation only: generating images, music, or running custom ComfyUI workflows.
Not for infrastructure, secrets, or knowledge tasks.

## Surfaces

Generate (and manage jobs/assets) entirely through the MCP surface — there is no separate CLI.
ComfyUI is a plain job-running store (not a reconciler), so submitting and reading work is a
direct tool call. Submission is async: you submit a job, then poll it to completion.

## Tool surface — the `comfyui-*` namespace

The `mcp:` prefix on the recipe entry parameterises the namespace; the tool *names* below are the
stable API.

**Generation:**
- `comfyui-generate_image(prompt, workflow?, options?)` → `{job_id, status}`
- `comfyui-generate_song(prompt, options?)` → `{job_id, status}`
- `comfyui-run_workflow(workflow_id, inputs)` → `{job_id, status}`
- `comfyui-regenerate(job_id, options?)` → re-run a prior job with same/modified params

**Job management:**
- `comfyui-get_job(job_id)` → status, output asset IDs when complete
- `comfyui-cancel_job(job_id)` → cancel an in-progress job
- `comfyui-get_queue_status()` → queue depth + active jobs

**Assets:**
- `comfyui-list_assets(type?, limit?)` → browse generated assets
- `comfyui-get_asset_metadata(asset_id)` → full metadata for an asset
- `comfyui-view_image(asset_id)` → retrieve image content for display

**Workflows:**
- `comfyui-list_workflows()` → available workflows

## Pattern (project-agnostic)

1. Submit a generation job → get a `job_id`.
2. Poll `comfyui-get_job(job_id)` until status is `complete`. (Generation is async — never assume
   the result is ready on the submit call.)
3. Retrieve output via `comfyui-get_asset_metadata` or `comfyui-view_image`.

## Everything project-specific comes from the recipe

| Need | Source |
|------|--------|
| MCP tool prefix (the `comfyui-*` namespace) | the comfyui entry's `.mcp` |
| Available workflows, model/checkpoint specifics, GPU placement | the comfyui entry's `.notes` + `facts` (discover live with `comfyui-list_workflows`) |

This module is the entire ComfyUI-specific surface. To make ComfyUI work for a new project, that
project adds a `tools.*` entry with `module: comfyui` to its recipe — it writes no media skill of
its own.
