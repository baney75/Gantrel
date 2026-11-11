# Select models in Gantrel

> **Status: planned, not released.** Gantrel has no release yet, so there is nothing to install today. These steps are the target behavior. Each one becomes true only when its test in [TESTING.md](https://github.com/baney75/Gantrel/blob/main/TESTING.md) passes, and [SUPPORTED.md](https://github.com/baney75/Gantrel/blob/main/SUPPORTED.md) is the source of truth for what works now. An agent must check SUPPORTED.md first and tell the person plainly if a step isn't supported yet.

You pick models inside Gantrel. Fonsviva downloads, stores and serves them.

## Steps

1. In Gantrel, open **Settings → Models**. It lists models on your connected machines that passed Gantrel's tests on that hardware (see [BENCHMARKS](https://github.com/baney75/Gantrel/blob/main/BENCHMARKS.md)).
2. Pick one for each task, or choose **Install** on a recommended model. Gantrel asks Fonsviva to download it and shows progress.

## Check

- `fonsviva models list --app gantrel` shows the selected models as `in use by gantrel`.
- Gantrel shows the model as ready. Models without a passing result for this hardware are marked "not tested here" and are not used for real work.
