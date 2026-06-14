---
name: agent-routing
description: How every role assembles its skill + tool loadout — base skills for the role, the tool-usage skills the current task needs, and the relevant convention skills. The project's specific values come from its own overlay/context.
---

Your behavioural knowledge is split across layers. Assemble your loadout in this order:

1. **Load your role's base skills** — the fixed, project-agnostic skills for your role. These are foundation skills, the same in every project:
   - *implementer:* `seam-detection`, the relevant `<stack>-conventions`, `k8s-*` patterns
   - *reviewer:* `pr-review-checklist`, `seam-detection`
   - *investigator:* `incident-runbook-template`
   - *lead:* `plan-generation`, `plan-validation`, `orchestration-patterns`
   - *triage:* `intake-process`
   - *responder:* the project's memory/knowledge-corpus tool-usage skill
   - *researcher:* `autonomous-agent-design`; writes its note via the project's memory tool-usage skill

2. **Load the tool-usage skills relevant to the current task** — pull `tool-<module>` for each tool the work actually touches (e.g. `tool-argocd` when the work touches ArgoCD; `tool-vault-substrate` when it touches the vault memory substrate). Each module is a generic operating pattern; the project provides the endpoint / auth / mcp (env vars, mounted secrets, or its overlay). **Don't load a module the project doesn't use** — don't load `tool-argocd` for a project that runs Flux.

3. **Load the relevant convention skills** — when a pattern skill needs a concrete value (StorageClass, `fsGroup`, domain, secret-store name, repo path), that value is project-specific. Pattern skills never hard-code project values; the consuming project supplies them in its own overlay or the agent's working context.

Everything you load here is foundation — generic patterns. The project's specific values come from its own overlay/context, never baked into these skills.
