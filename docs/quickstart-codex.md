# Quickstart — OpenAI Codex

Codex (CLI / IDE extension / cloud) consumes the foundation as a **solo harness**: it reads `AGENTS.md` natively, loads the full skill catalog, and reaches platform capabilities over MCP — but it runs **no crew roles** (Codex has no named-subagent registry). Where the entry file's routing table says "dispatch to Implementer/Reviewer/…", Codex applies the same skills inline itself.

## 1. The behavioral contract — already compatible

Codex reads the repo-root **`AGENTS.md`** natively (it originated the standard) — the same file Claude Code and pi.dev use, no shim required. Hierarchical `AGENTS.md` files in subdirectories also work. If the repo has no `AGENTS.md` yet, run onboarding from any harness (or copy `templates/AGENTS.md` and fill the ▸ blocks).

## 2. Install the skills

Codex loads portable `SKILL.md` skills from `.agents/skills/` (repo-level, scanned from cwd up to the repo root) and `~/.agents/skills/` (user-level). The foundation's schema-v2 frontmatter extras (`tier`/`requires`/`audience`/`expects-local`) are ignored by Codex — the files load as-is.

**User-level (recommended — no vendoring into the repo):**

```sh
git clone --depth 1 -b v0.10.0 https://github.com/ductiletoaster/harmony-crew /tmp/hc
mkdir -p ~/.agents/skills && cp -R /tmp/hc/skills/. ~/.agents/skills/
```

**Repo-level (teams that want skills pinned + committed):** copy into `<repo>/.agents/skills/` instead and commit. This vendors the catalog — pin the tag and re-run the copy to update, or the vendored copy drifts from the foundation.

Your project's own local skills (the `expects-local` slot fillings) go in the repo's `.agents/skills/` either way; on a name collision the repo-level copy is the one closest to your working directory.

## 3. Grant the capabilities (MCP)

Codex speaks streamable-HTTP MCP with bearer auth — exactly the LiteLLM gateway's shape. In `~/.codex/config.toml` (or a trusted project's `.codex/config.toml`):

```toml
[mcp_servers.litellm]
url = "https://<your-litellm-host>/mcp"
bearer_token_env_var = "LITELLM_API_KEY"
```

Set `LITELLM_API_KEY` to the surface's **virtual key** — per the capability-parity pattern, a Codex surface is a new consumer: mint it its own VK with explicit `mcp_access_groups` (see `litellm-routing-model`); never reuse another surface's key. The VK decides which capabilities (KB, search, image gen, cluster reads, …) this Codex install can reach.

## 4. Verify

Start a Codex session in the repo and ask it to **"run the doctor"** — the `doctor` skill loads from the installed catalog and reports install state, reachable capabilities, and unfilled local-skill slots, closing with the onboarding profile. Then, if the repo isn't onboarded yet: **"onboard this project to harmony-crew"**.

## What Codex doesn't get

- **Crew roles** — no `lead`/`implementer`/`reviewer` dispatch; the orchestration skills (`plan-*`, `orchestration-patterns`, `delta-handling`) still load and their plan/review disciplines apply, but Codex executes phases itself rather than dispatching workers.
- **Auto-updates** — there is no plugin/package manager in the path; updating = re-running the step-2 copy at a newer tag.
