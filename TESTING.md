# Testing: honest claims only

Gantrel must never claim it can do something it can't. Every claim in the README, the docs or the app has a test behind it, and the results are public in this repo.

## Design accuracy standard

Every design task has golden cases with measurable expected results: dimensions within stated tolerance, valid manifold geometry, printable models that slice cleanly, and structures that meet the cited standard or code. Research steps are checked for real, cited sources.

- A model is offered for a task only when it passes that task's suite.
- Dimensions taken from photos with a ruler are tested against measured ground truth with published error.

## Rules

- **No unknown error.** Any output that differs from the expected result fails the test, field by field. "Close enough" is a failure.
- **Known limits are declared.** Anything Gantrel doesn't support yet is listed in `SUPPORTED.md`. The app detects those situations and tells the user plainly instead of guessing.
- **Every model is tested separately.** A model is only offered for a task after it passes that task's suite (see `BENCHMARKS.md`).
- **Real behavior, not mocks.** Tests run the real skills against real local models and check real outputs.
- **Regressions block release.** A drop in any pass rate blocks promotion from Nightly to Stable.

## Layout

- `tests/golden/`: cases with known-correct expected outputs and their sources.
- `tests/skills/<skill-name>/`: tests for each skill.
- `benchmarks/results/`: published pass rates per model and hardware.
