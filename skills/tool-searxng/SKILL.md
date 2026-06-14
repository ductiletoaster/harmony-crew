---
name: tool-searxng
description: Privacy-respecting public web search via a self-hosted SearXNG, through the searxng-* MCP surface. Active only when the project recipe declares a tools.* entry whose module = searxng; reads the mcp prefix from that entry.
---

Generic SearXNG web-search operating pattern. **Activation:** load this only when the recipe has a
`tools.*` entry whose `module` is `searxng` (the recipe author chooses the role key — it's commonly
`search`, but read the module value, not the key). Take the MCP prefix from **that searxng entry's**
`.mcp` — never hard-code it.

> The federated MCP surface depends on `tool-litellm` (the gateway). Load that module first; the
> `searxng-*` calls below route through the gateway's `/mcp` endpoint.

## When to use

Reach for SearXNG when you need **current public-web** information that the project's own corpus
doesn't have — upstream docs, vendor changelogs, third-party GitHub issues — and you want a
privacy-respecting search that stays on your own infrastructure.

Don't use it for:
- Anything in the project's own memory substrate → use the `vault_*` search tools.
- The project's own GitHub org → use `gh search` / `gh issue list` / `gh pr list`.
- Code in the current workspace → use `Grep`.

## Surfaces

Search runs entirely through the MCP surface — there is no CLI. SearXNG is a plain read-only
service (not a reconciler), so both tools are direct read calls.

## Tool surface — the `searxng-*` namespace

The `mcp:` prefix on the recipe entry parameterises the namespace; the tool *names* below are the
stable API.

### `searxng-searxng_web_search` — public web search

Common parameters: `query` (required), `pageno` (default 1), `time_range` (`day`/`month`/`year` —
bias to recent material when a topic moves fast), `language` (default `all`), `safesearch`
(default off). Returns an array of `{title, url, content, engine, score}`. Pull the top N, decide
which URL(s) deserve a follow-up read.

### `searxng-web_url_read` — URL → markdown

Fetches a URL and returns the body as markdown (cleaner than raw HTML). Parameters: `url`
(required), `startChar`/`endChar` (chunked reads of large pages), `section` (target a heading),
`paragraphs` (paragraph-level text only). Use after a search when a snippet isn't enough. Anti-bot
pages, paywalls, and JS-heavy SPAs may still return noisy/empty content — report the gap rather
than working around it.

## Discipline (project-agnostic)

- **Anchor with a quoted unique landmark.** SearXNG dispatches to engines that tokenise
  aggressively — a dotted name loses its dot, an `@org/package` may lose the org prefix. Wrap a
  unique term (a package name, a version string, a known URL fragment) in quotes. An anchored
  query returns the actual project pages on the first try; an all-common-terms query matches
  everything.
- **Don't over-narrow with categories.** The `categories` param (e.g. `it`) can drop relevant
  general results on an already-anchored query. Try without it first; only narrow if too noisy.
- **Don't loop more than ~5 searches without a clear reason.** Bandwidth, upstream bot detection,
  and your own context budget all push back.
- **If a search or read tool errors, stop and report.** Don't auto-retry — the limiter is
  conservative by design.

## Everything project-specific comes from the recipe

| Need | Source |
|------|--------|
| MCP tool prefix (the `searxng-*` namespace) | the searxng entry's `.mcp` |
| Instance specifics, enabled engines, rate-limit quirks | the searxng entry's `.notes` |

This module is the entire SearXNG-specific surface. To make web search work for a new project, that
project adds a `tools.*` entry with `module: searxng` to its recipe — it writes no search skill of
its own.
