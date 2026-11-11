# Add a cloud provider

> **Status: planned, not released.** Gantrel has no release yet, so there is nothing to install today. These steps are the target behavior. Each one becomes true only when its test in [TESTING.md](https://github.com/baney75/Gantrel/blob/main/TESTING.md) passes, and [SUPPORTED.md](https://github.com/baney75/Gantrel/blob/main/SUPPORTED.md) is the source of truth for what works now. An agent must check SUPPORTED.md first and tell the person plainly if a step isn't supported yet.

Gantrel has no cloud settings. Cloud providers such as RunPod are added and turned on **only in Fonsviva**, for personal use only. Follow [Fonsviva: add a cloud provider](https://baney75.github.io/Fonsviva/setup/add-cloud-provider) and the [vetted provider list](https://baney75.github.io/Fonsviva/providers).

## What this means for Gantrel

Gantrel jobs use the person's personal profile, so cloud can be allowed in Fonsviva with cost shown first and a per-job confirm.

## Check

- Gantrel's job view labels every job with where it ran.
- Gantrel never asks for a provider key.
