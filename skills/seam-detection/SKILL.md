---
name: seam-detection
description: How to scan a diff or proposed change for crossings of the project's protected-seam registry, flag (don't block), and report the finding. Generic mechanism; the seam set and its detection signatures come from the project recipe (recipe.seams).
category: boundary
durability: durable
---

A **protected seam** is a boundary in the project where an unflagged change is high-risk enough to need operator sign-off. A **seam crossing** is any change that touches one of those boundaries without the author having explicitly flagged it.

This skill is the *detection mechanism*. The actual list of seams — and the concrete signature (file, key, regex, value) that identifies a crossing of each — lives in the project's recipe under `recipe.seams`, not here. The foundation defines *how to scan and report*; the recipe defines *what to scan for*.

## Detection mechanism

For each entry in `recipe.seams`:

1. **Read the seam's signature from the recipe.** Each seam entry names the boundary and the one-line reason it needs sign-off. Where the recipe (or the project's overlay) supplies a concrete signature — a file path, a config key, a forbidden value, a grep — use it.
2. **Scan the diff for that signature.** Restrict to changed files:
   ```bash
   git diff <base>...HEAD                 # full diff
   git diff <base>...HEAD -- <paths>      # scoped to a seam's files
   git diff <base>...HEAD | grep -E '<seam signature from recipe>'
   ```
3. **Apply context, not just a keyword match.** A match is a *candidate*; decide whether it's an actual crossing (see False positives).
4. **Flag, don't block.** A detected crossing is reported and routed to the operator (see `seam-alert-routing`). Detection does not auto-block merge or auto-remediate — it surfaces the crossing for a human decision.

Run any project-wide secret scanner the recipe specifies as part of every seam pass — leaked credentials are a near-universal seam.

## Reporting a seam finding

In a PR comment or review finding:

```
**Seam crossing detected — <seam name from recipe.seams>**

File: <path>
Line: <number>
Change: <what changed>
Risk: <why this matters — the seam's stated reason>
Action required: Operator sign-off before merge.
```

Mark as **Required** in the review. Do not approve or suggest merge until the author acknowledges the crossing and the operator provides sign-off. Routing of the alert is covered by `seam-alert-routing`.

## False positives

Not every touch of a seam-related file is a crossing. Context matters:

- A label, comment, or formatting change inside a seam-adjacent file that doesn't touch the protected key/value is not a crossing
- A test that imports a protected type but doesn't change its contract is not a crossing
- A read-only reference to a protected boundary is not a crossing

When in doubt, flag it. A false positive costs a brief discussion; a missed crossing can break production.

## Project values come from the recipe

- `recipe.seams` — **the entire seam registry.** The names, the boundaries, and the per-seam detection signatures (paths, keys, forbidden values, greps) are the project's, supplied by the recipe and its overlay. This foundation skill deliberately carries **no** seam definitions — it would be wrong to hard-code one project's seams into the shared detection mechanism.
- Any secret scanner, grep base ref, or scoped paths are taken from the recipe / project, not assumed.
- The operator is the fixed sign-off authority; never hard-code a project-specific person.
