---
name: comfyui
description: ComfyUI MCP tools for media generation — images, audio, workflows, and asset management.
category: domain
durability: durable
tier: subject
---

## When to Use

Use for creative/media generation tasks: generating images, music, or running custom ComfyUI workflows. Not for infrastructure or knowledge tasks.

## Available Tools

Generation:
- `comfyui-generate_image(prompt, workflow?, options?)` → `{job_id, status}`
- `comfyui-generate_song(prompt, options?)` → `{job_id, status}`
- `comfyui-run_workflow(workflow_id, inputs)` → `{job_id, status}`
- `comfyui-regenerate(job_id, options?)` → re-run a previous job with same or modified params

Job management:
- `comfyui-get_job(job_id)` → job status, output asset IDs when complete
- `comfyui-cancel_job(job_id)` → cancel an in-progress job
- `comfyui-get_queue_status()` → current queue depth and active jobs

Assets:
- `comfyui-list_assets(type?, limit?)` → browse generated assets
- `comfyui-get_asset_metadata(asset_id)` → full metadata for an asset
- `comfyui-view_image(asset_id)` → retrieve image content for display

Workflows:
- `comfyui-list_workflows()` → available ComfyUI workflows

## Pattern

1. Submit job → get `job_id`
2. Poll `comfyui-get_job(job_id)` until status is `complete`
3. Retrieve output via `comfyui-get_asset_metadata` or `comfyui-view_image`

## Auth

Routes through LiteLLM MCP. The gateway requires a LiteLLM virtual key as a Bearer token; the MCP client config supplies it (`Authorization: Bearer ${LITELLM_API_KEY}` in the MCP client config), so individual tool calls need no extra credentials.

## Security — this server is more than image generation

The full server exposes **~35 tools**, and the catalog is **not** limited to generation. Alongside `generate_image` / `generate_song` / `run_workflow` it carries **privileged operational tools** — host-path and manifest operations and node-control actions (e.g. `add_extra_path`, `apply_manifest`, `bisect_start`). Those can read/write host paths, mutate ComfyUI's deployed configuration, and drive node lifecycle. They are not something an image-generating surface (a chat UI, a companion agent, a web app) should be able to call.

**Scope with a per-server `allowed_tools` allowlist** to the generation subset — the `generate_*`, `run_workflow`, `regenerate`, job-management, and asset/read tools above — and exclude the host-path/manifest/node-control tools. This is the only reliable per-server tool restriction (`disallowed_tools` is broken in v1.86.2; see `litellm-routing-model`). A surface granted the image-generation capability should see only the generation subset, never the full 35.

The concrete allowlist and which surfaces hold the image-generation capability are deployment-specific — they live in the consumer's local skill.
