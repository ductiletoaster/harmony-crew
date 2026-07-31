## Operating context

You run inside a Kubernetes pod, dispatched by Argo Workflows to execute one scoped task end-to-end. You have a fresh git workspace at `/workspace/<issue-number>/` checked out to a new branch named `agent/<issue-number>-<slug>`. After you finish, separate Workflow steps push your commits and open the PR — you do not run `git push` or `gh pr create` yourself; make sure the latest commit message carries the PR-shape content below.

If the task body is unclear or impossible, exit non-zero with a brief diagnostic — do not invent the task. The Workflow's `report-failure` step routes to the operator. When done, exit cleanly (status 0); the wrapper handles the rest.

Do not include `Co-Authored-By` lines for AI authorship.
