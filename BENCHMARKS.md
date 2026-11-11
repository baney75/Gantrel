# Benchmarking local models

We need to know which local models can actually do Gantrel's work, on which hardware. Guessing is not allowed.

## Built on the Local AI registry

Model launches come from Sybil Solutions' [Local AI registry](https://github.com/sybil-solutions/local-ai-registry) ([local.sybilsolutions.ai](https://local.sybilsolutions.ai)). Each registry recipe is a validated way to run a model on a specific GPU that passed its general gates: it loads, chats, reasons, calls tools, holds context and decodes at 15 tok/s or more. This works on any device the registry covers.

Gantrel adds its own task gates on top. A model only counts as working for Gantrel when it passes them.

## Gantrel task gates

- **Geometry validity:** manifold, correctly scaled, exportable.
- **Dimension accuracy:** within tolerance of the spec or measured ground truth.
- **Printability:** slices cleanly with expected settings.
- **Research quality:** finds correct specs and cites real sources; invents none.
- **Photo measurement:** ruler-in-photo dimensions within the published error bound.

## How a run works

1. Pick a registry recipe for the hardware and launch it.
2. Run the task gates in `tests/` against it.
3. Save the result to `benchmarks/results/<model>/<card>.json` with the recipe ID, date, hardware, pass rate per gate and a log hash.
4. The app offers a model for a task only where a passing result exists for that hardware.

## Per-model instructions

Each model that passes gets a folder in `models/<model>/` (copy `models/_template/`) with the prompt format, settings and skill wording that model needs, plus its own tests. Skills stay shared; only model-specific adjustments live here.
