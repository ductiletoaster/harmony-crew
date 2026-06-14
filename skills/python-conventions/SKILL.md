---
name: python-conventions
description: Generic Python conventions — package manager, linter, test runner, src-layout, CLI (Typer) and MCP-server (FastMCP) patterns. Applies the project's values (project-specific stack + CLI name). Load for any Python work.
category: stack
durability: durable
---

Generic Python convention pattern. The *shape* of the conventions below is fixed across
projects; every concrete tool, command, and path is project-specific (the project's stack config
and CLI name) — never hard-code them here.

## Runtime and tooling

A project's Python toolchain is project-specific:

| Concern | Source | Typical value |
|---|---|---|
| Package manager / venv | project-specific | `uv` (`uv run`, `uv add`, `uv sync`) |
| Lint + format | project-specific | `ruff` (replaces flake8 / isort / black) |
| Test runner | project-specific | `pytest` |
| Source layout | project-specific | `src` |

Use the project's values, not these examples — a project on a different stack overrides any of them.

## Project structure (src layout)

When the project uses a `src` layout, packages live under `src/`, one directory per package, with
clear dependency direction (shared library ← CLI / MCP servers depend on it, never the reverse):

```
src/
├── <core-lib>/      # shared library: config, console, runner, secrets, errors
├── <cli-pkg>/       # the project CLI — depends on the core library
└── <mcp-pkg>/       # MCP server(s) — depend on the core library
```

The package names are the project's own; the *layout discipline* (src/, one package per dir,
acyclic deps) is the reusable pattern.

## CLI (Typer + Rich)

The project's task CLI name is project-specific. New commands follow the command-group pattern:

```python
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def my_command(arg: str = typer.Argument(..., help="Description")):
    """One-line docstring shown in --help."""
    console.print(f"[green]{arg}[/green]")
```

The CLI is the operator-facing surface; MCP tools are the agent-facing surface. Don't duplicate
logic — if both surfaces need a capability, the MCP tool is canonical and the CLI is a thin
wrapper. See `mcp-server-design` for the full surface-decision framework.

## MCP servers (FastMCP)

In-house MCP servers use FastMCP:

```python
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description shown to agents."""
    return result
```

Tool descriptions must be precise — agents use them for tool selection. Phrasing matters. See
`mcp-server-design`.

## Testing

```bash
<pkg> run pytest                  # run all tests
<pkg> run pytest tests/unit/      # a subdirectory
<pkg> run pytest -x               # stop on first failure
```

Tests live under `tests/` alongside source. Prefer real dependencies over mocks that can drift
from reality — divergent mocks hide production failures.

## Linting and formatting

```bash
<pkg> run ruff check              # lint
<pkg> run ruff check --fix        # auto-fix
<pkg> run ruff format             # format
<pkg> run ruff format --check     # CI gate — checked separately from `ruff check`
```

`ruff check` and `ruff format --check` are **separate gates**; CI runs both, so run both before
every PR. Ruff config lives in `pyproject.toml`.

## Running the CLI

```bash
<pkg> run <cli> <command>         # always via the package manager, never the bare entrypoint
```

The venv is managed by the package manager (project-specific); never activate it manually.

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, …) are project-specific. The
consuming project supplies them — in its own overlay skills or the agent's working context. This
skill is the generic pattern.

| Need | Source |
|---|---|
| Package manager / venv tool (the `<pkg>` above) | project-specific (the project's stack config) |
| Linter + formatter | project-specific (the project's stack config) |
| Test runner | project-specific (the project's stack config) |
| Source layout discipline | project-specific (the project's stack config) |
| The CLI command name (the `<cli>` above) | project-specific |
| Package / module names | the project's own `src/` tree |

This skill owns the *conventions*; the project supplies the *names*. A new project changes its
own config, not this skill.
