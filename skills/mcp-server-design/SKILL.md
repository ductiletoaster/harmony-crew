---
name: mcp-server-design
description: Designing and implementing MCP servers using FastMCP — tool design, description quality, error handling, and the MCP vs CLI surface decision. Load when building new MCP tools or servers.
category: architecture
durability: durable
---

## Surface decision first

Before writing an MCP tool, confirm the primary caller: agent or human?

- **Agent-primary** → MCP tool first; optional CLI shim if humans need a debug path
- **Human-primary** → CLI command in `hmy`; no MCP unless agents genuinely need it
- **Both** → MCP canonical; CLI is a thin wrapper that forwards structured args

The MCP tool is the source of truth for validation, schema, and side effects. The CLI never duplicates logic — it calls the MCP tool or the underlying library directly. See CLAUDE.md interface boundary rules for the full decision framework.

## FastMCP basics

```python
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
def my_tool(param: str, optional_param: int = 10) -> dict:
    """
    One concise sentence: what this tool does and what it returns.
    Agents use this description for tool selection — precision matters.
    """
    return {"result": ..., "status": "success"}
```

## Tool description quality

The tool docstring is the primary mechanism agents use to decide whether to call the tool. Write it as:
- One sentence describing the action and output
- If the tool has important constraints or side effects, add them in a second sentence

Bad: `"""Search the vault."""`
Good: `"""Full-text search across all Obsidian vault content. Returns matching note paths and excerpts."""`

## Error handling

Return structured errors rather than raising exceptions — exceptions surface as tool call failures with no useful context:

```python
@mcp.tool()
def my_tool(path: str) -> dict:
    """Read a note from the vault by path."""
    try:
        content = vault.read(path)
        return {"content": content, "found": True}
    except NoteNotFoundError:
        return {"content": None, "found": False, "error": f"No note at {path}"}
```

For transient errors (network, rate limits), raise — let the caller decide on retry. For logical errors (not found, invalid input), return structured error so the agent can handle it.

## Failure semantics by surface

The same underlying capability may have different failure modes across surfaces:

| Surface | Failure mode | Why |
|---|---|---|
| MCP tool (agent side effect) | Soft-fail — log, return error, don't block | Vault trouble shouldn't abort an unrelated task |
| CLI command (human primary action) | Hard-fail — exit 1, print error | Operator needs to know their action didn't land |

Document this asymmetry if both surfaces exist.

## Server registration

MCP servers are registered in `.mcp.json` at the repo root. LiteLLM aggregates in-cluster MCP servers. Workstation Claude Code sessions use `.mcp.json` to discover available tools.

## Lifecycle MCP write pattern

For vault writes from any agent or tool:

```python
# kind routing:
# fleeting → fleeting/
# research → research/
# runbook → notes/runbooks/
# agent-run → 90-Archive/Agent-Notes/

result = lifecycle_writeNote(
    kind="research",
    title="Option Analysis: X vs Y",
    tags=["research", "platform"],
    issue=42,           # optional: link to GitHub issue
    source_agent="researcher",
    content="..."
)
```
