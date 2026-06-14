---
name: intake-process
description: How triage classifies incoming issues and PRs — domain classification, labelling, and routing to a foundation role. Generic mechanism; the project's actual label set is project-specific. Load when processing new issues, PRs, or unlabelled work items.
category: process
durability: cross-cutting
---

Triage is a lightweight intake filter: classify each item by **domain** and **work type**, apply the project's labels, and route to the right foundation role. It does not make implementation decisions, access infrastructure, or write code.

## Classify by domain

Apply exactly one domain classification per item — the primary domain, not every domain it grazes. The project owns the concrete label *names* (read them from the project's label set); the foundation only fixes the *kinds* of domain to recognise:

| Domain kind | Applies to |
|---|---|
| infrastructure | manifests, IaC, config management, cluster/platform operations |
| platform / application | the project's CLI, services, libraries, agent tooling |
| ops | health degradations, incidents, monitoring findings |
| agents | agent topology, skills, orchestration |
| research | pre-implementation option analysis, technology evaluation |
| docs | documentation, runbooks |
| qa | post-deploy verification failures, regression findings |

Map each kind to the project's actual label string. If the project defines a different domain taxonomy, use it — the classify-then-label step is what's fixed, not the label vocabulary.

## Classify by work type → route to a role

After the domain, classify work type to pick the destination role. Route to **foundation roles** (the same set in every project):

| Work type | Signal | Route to |
|---|---|---|
| Simple question / reply needed | a question answerable from knowledge, no investigation or write | responder |
| Active incident / degradation | something failing, degraded, or unreachable now | investigator |
| Pre-implementation research | "evaluate options for…", "research…", or a research-domain item | researcher |
| Trivial explicit change | clear, bounded scope with an obvious owner surface and no design needed | implementer |
| PR opened, no orchestrated plan | code review needed | reviewer |
| Multi-step / ambiguous / plan needed | more than one role, unclear scope | lead |

## Processing an issue

1. Read the title and body
2. Apply the domain label
3. Classify work type
4. Post a routing comment:
   ```
   Classified as <domain>. Routing to <role> — <one-sentence reason>.
   ```
5. If the destination role has a queue mechanism, add the project's routing label for it

## Processing a PR

1. Check whether the PR is part of an orchestrated plan (lead-driven work carries plan context in the description)
2. If yes: lead is already tracking it — add the domain label only
3. If no: route to reviewer with the domain label applied

## Ambiguity handling

When domain or work type is unclear:
- Default route: lead
- Don't guess at implementation intent or priority
- Don't apply multiple domain labels — pick the primary one
- A brief "unclear scope, routing to lead for triage" comment is correct

## What triage does not do

- Does not make implementation decisions
- Does not access infrastructure or the cluster
- Does not write code or manifests
- Does not re-classify items that already carry a domain label from a previous pass

## Project-specific values

Concrete values (paths, StorageClass names, endpoints, labels, the protected-seam registry, …)
are project-specific. The consuming project supplies them — in its own overlay skills or the
agent's working context. This skill is the generic pattern.

- **Label vocabulary** — the actual strings for domain and routing labels come from the project (its tracker's label set), not from this skill. The foundation fixes the *kinds* of domain and the route targets.
- **Destination roles** are the fixed foundation roles (lead / triage / investigator / researcher / responder / reviewer / implementer). Never hard-code a project-specific role name.
- **Tracker** — issues/PRs live on whatever tracker the project uses; the classify/comment/route mechanism is the same regardless.
