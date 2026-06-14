# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""test_routing — assert recipe-resolve produces the right per-project loadout.

The point of the recipe contract is that the SAME foundation routes to DIFFERENT
tool modules per project, purely from the recipe. This test pins that:

  * fireforge (divergent) resolves to tool-flux + tool-sealed-secrets, and does
    NOT pull tool-argocd / tool-comfyui.
  * the Harmony example resolves to tool-argocd + tool-comfyui.
  * the resolved `gitops` endpoint differs between the two recipes (proving the
    connection target comes from the recipe entry, not a hard-coded default).

Run: `python tests/test_routing.py` (or `uv run tests/test_routing.py`).
Exit 0 if all assertions pass, 1 on the first failure.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESOLVE = REPO_ROOT / "scripts" / "recipe-resolve.py"

FIREFORGE = REPO_ROOT / "tests" / "recipe-fireforge.yaml"
HARMONY = REPO_ROOT / "recipe.example.yaml"


def resolve(recipe: Path) -> list[tuple[str, str, str]]:
    """Run recipe-resolve and parse its tab-separated output into rows.

    Invoke through `uv run` so recipe-resolve's inline script deps (pyyaml) are
    provisioned — the bare test interpreter does not carry them.
    """
    proc = subprocess.run(
        ["uv", "run", str(RESOLVE), str(recipe)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"recipe-resolve exited {proc.returncode} for {recipe}:\n{proc.stderr}"
        )
    rows: list[tuple[str, str, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        role, module, target = line.split("\t")
        rows.append((role, module, target))
    return rows


def main() -> int:
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    fire = resolve(FIREFORGE)
    harm = resolve(HARMONY)

    fire_modules = {module for _role, module, _t in fire}
    harm_modules = {module for _role, module, _t in harm}

    # fireforge: divergent modules present, Harmony-only modules absent
    check("tool-flux" in fire_modules, "fireforge: expected tool-flux in loadout")
    check(
        "tool-sealed-secrets" in fire_modules,
        "fireforge: expected tool-sealed-secrets in loadout",
    )
    check(
        "tool-argocd" not in fire_modules,
        "fireforge: tool-argocd must NOT be in loadout",
    )
    check(
        "tool-comfyui" not in fire_modules,
        "fireforge: tool-comfyui must NOT be in loadout",
    )

    # Harmony example: argocd + comfyui present
    check("tool-argocd" in harm_modules, "harmony: expected tool-argocd in loadout")
    check("tool-comfyui" in harm_modules, "harmony: expected tool-comfyui in loadout")

    # gitops endpoint differs between the two recipes
    fire_gitops = next((t for r, _m, t in fire if r == "gitops"), None)
    harm_gitops = next((t for r, _m, t in harm if r == "gitops"), None)
    check(fire_gitops is not None, "fireforge: no gitops role resolved")
    check(harm_gitops is not None, "harmony: no gitops role resolved")
    check(
        fire_gitops != harm_gitops,
        f"gitops endpoint must differ between recipes "
        f"(fireforge={fire_gitops!r}, harmony={harm_gitops!r})",
    )

    if failures:
        print(f"FAIL: {len(failures)} assertion(s):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("PASS: routing assertions hold")
    print(f"  fireforge modules: {sorted(fire_modules)}")
    print(f"  harmony   modules: {sorted(harm_modules)}")
    print(f"  gitops endpoints differ: {fire_gitops!r} != {harm_gitops!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
