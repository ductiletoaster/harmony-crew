# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""recipe-resolve — print the deterministic tool loadout for a recipe.

Given a recipe path, emit one line per ACTIVE tool module:

    <role>\t<module>\t<endpoint-or-mcp>

This is the ground-truth "loadout" a routing agent should match: exactly which
tool-<module> skills are active for this project, and the connection target each
reaches (its .endpoint, or its .mcp prefix when it has no endpoint). Lines are
sorted by role for stable diffing.

The third column resolves as: the entry's `endpoint` if present, else its `mcp`
prefix, else `-`. (Endpoint-bearing modules and mcp-only modules both surface a
meaningful identity; stub/no-connection modules surface `-`.)

Exit 0 on success, 2 on a malformed/missing recipe. recipe-resolve does NOT
validate the recipe — run recipe-lint for that.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - defensive
    print(
        "error: PyYAML is required. Run via `uv run scripts/recipe-resolve.py ...` "
        "(the inline script header declares pyyaml), or `pip install pyyaml`.",
        file=sys.stderr,
    )
    sys.exit(2)


def resolve(recipe_path: Path) -> list[tuple[str, str, str]]:
    """Return (role, module, endpoint-or-mcp) per active tool entry, sorted by role."""
    if not recipe_path.exists():
        raise FileNotFoundError(f"{recipe_path}: file not found")

    with recipe_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"{recipe_path}: top-level recipe must be a mapping")

    tools = data.get("tools") or {}
    if not isinstance(tools, dict):
        raise ValueError(f"{recipe_path}: tools must be a mapping of <role> -> entry")

    rows: list[tuple[str, str, str]] = []
    for role, entry in tools.items():
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module:
            continue
        target = entry.get("endpoint") or entry.get("mcp") or "-"
        rows.append((str(role), f"tool-{module}", str(target)))

    return sorted(rows, key=lambda r: r[0])


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: recipe-resolve.py <recipe-path>", file=sys.stderr)
        return 2

    recipe_path = Path(argv[1])
    try:
        rows = resolve(recipe_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for role, module, target in rows:
        print(f"{role}\t{module}\t{target}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
