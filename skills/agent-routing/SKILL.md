---
name: agent-routing
description: How every role assembles its skill + tool loadout from the project recipe. Load this first — it tells you which tool modules to pull for this project and where the project's facts live.
---

Your behavioural knowledge is split across three layers. Assemble your loadout in this order:

1. **Read the project recipe** — `.pi/project.yaml` (pi) or `.claude/project-profile.md` (Claude Code). It's small. It declares the project's active tools, platform facts, protected seams, and stack. Everything project-specific you need is in there.

2. **Load your role's base skills** — the fixed, project-agnostic skills for your role. These are foundation skills, the same in every project:
   - *implementer:* `seam-detection`, the relevant `<stack>-conventions`, `k8s-*` patterns
   - *reviewer:* `pr-review-checklist`, `seam-detection`
   - *investigator:* `incident-runbook-template`
   - *lead:* `plan-generation`, `plan-validation`, `orchestration-patterns`
   - *triage:* `intake-process`
   - *responder:* the recipe's `tools.memory` module (the project's knowledge corpus)
   - *researcher:* `autonomous-agent-design`; writes its note via the recipe's `tools.memory` module

3. **Load a tool module for every active tool** — for each entry under the recipe's `tools.*`, load `tool-<module>` (e.g. `tools.gitops.module: argocd` → load `tool-argocd`; `tools.memory.module: vault-substrate` → `tool-vault-substrate`). Each module is a generic operating pattern that reads its own `tools.<role>` block for endpoint / auth / mcp. **Skip modules the recipe doesn't activate** — don't load `tool-argocd` for a project that runs Flux.

4. **Apply facts, not constants** — when a pattern skill needs a concrete value (StorageClass, `fsGroup`, domain, secret-store name, repo path), take it from the recipe's `facts` / `stack`. Pattern skills never hard-code project values.

The recipe is the **only** project-specific input. Everything else you load is foundation. A project you've never seen is workable the moment you've read its recipe.
