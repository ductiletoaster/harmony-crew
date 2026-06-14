# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""recipe-lint — validate a harmony-crew project recipe.

Checks a recipe (default: recipe.example.yaml) against the foundation contract:

  * top-level keys are a subset of the allowed set
  * every tools.<role> key is in the closed role enum
  * every tools.<role>.module names a tool-<module> skill present in the repo
  * per-module required fields are present

Exit 0 if clean, exit 1 if any error. Each error prints the offending path.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - defensive
    print(
        "error: PyYAML is required. Run via `uv run scripts/recipe-lint.py ...` "
        "(the inline script header declares pyyaml), or `pip install pyyaml`.",
        file=sys.stderr,
    )
    sys.exit(2)

# Repo root = parent of the scripts/ directory this file lives in.
REPO_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_TOP_LEVEL = {"identity", "tools", "facts", "seams", "stack"}

ROLE_ENUM = {"gateway", "gitops", "secrets", "memory", "media", "exec", "search"}

# Per-module required fields. Unknown modules are an error.
MODULE_REQUIRED_FIELDS = {
    "argocd": ["endpoint", "auth", "mcp"],
    "litellm": ["endpoint", "auth"],
    "external-secrets": ["store", "prefix"],
    "vault-substrate": ["mcp"],
    "comfyui": ["mcp"],
    "coder": ["endpoint", "auth"],
    "searxng": ["mcp"],
}


def lint(recipe_path: Path) -> list[str]:
    errors: list[str] = []

    if not recipe_path.exists():
        return [f"{recipe_path}: file not found"]

    try:
        with recipe_path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        return [f"{recipe_path}: invalid YAML — {exc}"]

    if data is None:
        return [f"{recipe_path}: empty recipe"]
    if not isinstance(data, dict):
        return [f"{recipe_path}: top-level recipe must be a mapping"]

    # 1. top-level keys subset
    for key in data:
        if key not in ALLOWED_TOP_LEVEL:
            errors.append(
                f"{key}: unknown top-level key "
                f"(allowed: {', '.join(sorted(ALLOWED_TOP_LEVEL))})"
            )

    # 2-4. tools.<role> checks
    tools = data.get("tools")
    if tools is not None:
        if not isinstance(tools, dict):
            errors.append("tools: must be a mapping of <role> -> entry")
        else:
            for role, entry in tools.items():
                path = f"tools.{role}"

                # 2. role key in closed enum
                if role not in ROLE_ENUM:
                    errors.append(
                        f"{path}: role '{role}' not in enum "
                        f"({', '.join(sorted(ROLE_ENUM))})"
                    )

                if not isinstance(entry, dict):
                    errors.append(f"{path}: entry must be a mapping")
                    continue

                module = entry.get("module")
                if not module:
                    errors.append(f"{path}.module: missing required 'module' field")
                    continue

                # 3. module has a corresponding tool-<module> skill in the repo
                skill_path = REPO_ROOT / "skills" / f"tool-{module}" / "SKILL.md"
                if not skill_path.exists():
                    errors.append(
                        f"{path}.module: module '{module}' has no tool-{module} skill"
                    )

                # 4. per-module required fields
                if module not in MODULE_REQUIRED_FIELDS:
                    errors.append(
                        f"{path}.module: unknown module '{module}' "
                        f"(no required-field rule)"
                    )
                else:
                    for field in MODULE_REQUIRED_FIELDS[module]:
                        if field not in entry or entry[field] in (None, ""):
                            errors.append(
                                f"{path}.{field}: module '{module}' "
                                f"requires field '{field}'"
                            )

    return errors


def main(argv: list[str]) -> int:
    recipe_arg = argv[1] if len(argv) > 1 else "recipe.example.yaml"
    recipe_path = Path(recipe_arg)

    errors = lint(recipe_path)

    if errors:
        print(f"FAIL: {recipe_path} — {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  ERROR {err}", file=sys.stderr)
        return 1

    print(f"OK: {recipe_path} — no errors")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
