# Research engineering rules

- Read existing code, documentation and Git status before editing. Work on a branch.
- Prefer minimal, independently verifiable changes. Preserve research records and user work.
- Every computational feature needs a documented command, assumptions, units, parameters,
  and meaningful numerical tests where feasible. Never remove valid failing tests to pass CI.
- Never fabricate data, citations, paper results or claims of physical correctness.
- Distinguish Planned, Implemented, Tested and Validated; record evidence and scope.
- Analytical solutions establish numerical verification, not experimental validation.
- Keep case-specific code in its case until actual reuse justifies a stable src/codelab API.
- Do not commit credentials, environments, solver binaries or large intermediate results.
- External software tests are optional integration tests; ordinary CI must remain lightweight.
- Cite upstream work and check licensing before copying. No external repository vendoring.
- Report changed files, commands actually run, results and remaining limitations.
- Do not force-push, rewrite history, change remote settings or merge without authorization.
