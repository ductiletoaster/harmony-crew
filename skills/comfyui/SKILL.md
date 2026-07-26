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

Assets — **two kinds of tool, and the difference is load-bearing:**

*Content tools (return the image BYTES inline — use these to deliver):*
- `comfyui-view_image(asset_id)` → the image as an inline image content block (PNG/JPEG/WebP only)
- `comfyui-convert_image(asset_id, format, quality?)` → re-encodes to png/jpeg/webp and returns the bytes inline; **prefer this** — it lets you shrink to jpeg/webp to fit channel size caps, and it completes faster than `view_image` (which can hit an MCP call timeout on large PNGs)
- `comfyui-get_image(filename, …)` → fetches by filename and returns bytes inline (use `get_history` first to get the filename)

*Metadata tools (return only a URL / provenance — NEVER deliverable):*
- `comfyui-list_assets(type?, limit?)` → browse generated assets (returns each asset's internal `/view?…` URL)
- `comfyui-get_asset_metadata(asset_id)` → full provenance + the workflow snapshot
- `comfyui-list_output_images(...)` → filesystem listing of output files (no bytes)

The `url` / `/view?filename=…` field these metadata tools return points at the **ComfyUI server on the cluster's internal network**. It is not fetchable by the user's chat client, and on many gateways the outbound send path will refuse it outright (private-IP SSRF guard). Sending it as text or as a `media` URL is the single most common delivery failure — use a **content** tool instead.

Workflows:
- `comfyui-list_workflows()` → available ComfyUI workflows

## Pattern

1. Submit job → get `job_id`
2. Poll `comfyui-get_job(job_id)` until status is `complete`
3. Get the image **bytes** with a *content* tool — `comfyui-convert_image` (preferred) or `comfyui-view_image` / `comfyui-get_image`. Do **not** stop at `get_asset_metadata` / `list_assets`; their `/view` URL is not deliverable.
4. **Deliver it to the user** (see below) — the job completing is not the same as the user receiving the asset.

## Delivering the result

Generating an asset is only half the task — the user has to actually *receive* it. A raw `asset_id`, a `MEDIA:<asset_id>` token, or an internal `/view?filename=…` URL is **not** something the user can see, and chat gateways commonly **block** the `/view` URL at send time (it resolves to a private cluster IP → SSRF-blocked, with no config to allow it). You must turn the image into a real, native attachment sourced from **bytes**, never from that URL. How depends on the harness:

- **Chat gateways (e.g. OpenClaw personas — `message(action=send)`):**
  1. Obtain the image bytes with a **content** tool — `comfyui-convert_image(asset_id, format="jpeg", quality=80)` is preferred (smaller payload, fits size caps, avoids the `view_image` timeout).
  2. Write those bytes to a **local file the agent can read**, under an allowed media root — `/tmp/openclaw/<name>.jpg` (or the agent's workspace). Use the agent's filesystem/exec tool to persist them; do **not** try to paste the base64 into the send call.
  3. Send it as a genuine attachment: `message(action=send, media="/tmp/openclaw/<name>.jpg")` (structured `media` / `path` field — a local **path**, not a URL). If the gateway hands you an offloaded managed-media ref for the tool image (`media://inbound/<id>`), you may pass that ref instead; but the staged local-file path is the reliable route.
  - **Never** put a `MEDIA:<asset_id>` token, an `asset_id`, or a raw `/view?…` URL in `media=` or in the message text — the recipient sees a broken hash or an unreachable/blocked internal link, not the picture. **Never** point `media=` at the ComfyUI `/view` URL.
  - Note: `comfyui-get_image(save_dir=…)` and `comfyui-convert_image(out_path=…)` write on the **ComfyUI/MCP server's** filesystem, not the agent's — those files are not sendable. Take the **inline bytes** from the tool result and write them locally yourself.
- **Dev harnesses (Claude Code / pi):** write the asset to a file path and surface that path; the session/operator picks it up from there.

Confirm the asset reached the user, not merely that the job reported `complete`. If you cannot attach it, say so plainly rather than pasting an internal reference or the `/view` URL.

## Auth

Routes through LiteLLM MCP. The gateway requires a LiteLLM virtual key as a Bearer token; the MCP client config supplies it (`Authorization: Bearer ${LITELLM_API_KEY}` in the MCP client config), so individual tool calls need no extra credentials.

## Security — this server is more than image generation

The full server exposes **~35 tools**, and the catalog is **not** limited to generation. Alongside `generate_image` / `generate_song` / `run_workflow` it carries **privileged operational tools** — host-path and manifest operations and node-control actions (e.g. `add_extra_path`, `apply_manifest`, `bisect_start`). Those can read/write host paths, mutate ComfyUI's deployed configuration, and drive node lifecycle. They are not something an image-generating surface (a chat UI, a companion agent, a web app) should be able to call.

**Scope with a per-server `allowed_tools` allowlist** to the generation subset — the `generate_*`, `run_workflow`, `regenerate`, job-management, and asset/read tools above — and exclude the host-path/manifest/node-control tools. This is the only reliable per-server tool restriction (`disallowed_tools` is broken in v1.86.2; see `litellm-routing-model`). A surface granted the image-generation capability should see only the generation subset, never the full 35.

The concrete allowlist and which surfaces hold the image-generation capability are deployment-specific — they live in the consumer's local skill.
