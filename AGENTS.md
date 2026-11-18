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

## Learner-owned textbook workflow

- At each learning request, read `docs/study-map.md`, `docs/weekly-rhythm.md` and
  `docs/study-tasks.md`, then the relevant case and the learner's code.
- Turns + Cantera is the near-term thesis priority. Anderson Chapter 7 (quasi-1D
  nozzle / MacCormack) is the active CFD thread. Moukalled and GitHub resources
  support specific questions; they are not mandatory parallel full courses.
- Propose one 60–120 minute task based on the user's actual reading or difficulty.
  State equations, assumptions, units, inputs/outputs, a small implementation plan,
  and a quantitative verification route. Confirm edition/section if needed; do not
  invent page numbers or assume the learner has completed prerequisite chapters.
- The learner writes core code. Give hints and incremental feedback, not full
  implementations or complete reference answers unless explicitly requested.
- When reviewing, explain the cause of errors and test rationale. Run relevant
  tests, record evidence, update the task and learning map, then commit on the
  feature branch. Do not mark a task complete merely because code runs.
- Each computation has one canonical case location. Reading notes link to it;
  do not duplicate Cantera scripts, rename working entry points for a new map,
  or mass-generate unstarted exercises and task files.
- Keep at most one active learning task in `docs/study-tasks.md`. Create detailed
  notes inside the owning case only when work begins. Preserve completed records.
- Do not commit textbook PDFs, unreviewed upstream code or the local supplied
  scaffold. Its integration decisions are recorded in `docs/textbook-integration.md`.
