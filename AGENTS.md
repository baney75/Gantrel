# AGENTS.md

Instructions for AI coding agents (Claude Code, Codex, Cursor and others) working in Gantrel.

## What this project is

A local-AI 3D design studio for hobbyists up to professionals, from 3D printing to product design to architecture. It combines precise CAD, freeform modeling and rendering, and an agent workspace in one easy app. It uses autoresearch (SearXNG, browser automation) and reference photos, including a ruler in the shot for real dimensions.

## Ground rules

- **Local first, compute via Fonsviva.** Features must work with local models on the user's own hardware. All compute, including RunPod and other cloud providers, comes via [Fonsviva](https://github.com/baney75/Fonsviva). This app never adds providers, stores provider keys or calls a cloud provider itself. It connects to Fonsviva and shows where each job ran. Cloud providers are personal use only and are set up in Fonsviva.
- **Private and secure by default.** User data is encrypted at rest and in transit. Never log, print or send secrets or personal data.
- **Trusted models only.** Use safe, reputable open models. Document which models a feature was tested with.
- **Easy beats clever.** Every feature has to be usable by a non-technical person.
- **Design comes from DESIGN.md.** Follow it for all UI work. If it is empty or silent on something, ask the designer rather than inventing a style.
- **Prove it works.** Back every change with behavior tests or a recorded real run. Don't claim something works without evidence.
- **Small, reviewable changes.** One concern per pull request, with a clear description.
- **Autoresearch is essential.** Before designing, the model researches real dimensions, materials, tolerances, standards and building codes, and cites what it found. Research quality matters as much as geometry quality.
- **Real-world correctness.** Units, tolerances and printability or buildability are checked, not assumed.

## Skills

Skills live in `skills/maintainer/` (for building this project) and `skills/runtime/` (used by agents inside the app). All are original and tested; see `skills/README.md`. Load the skill that matches your task before starting, and improve it when you learn something.

## Testing and honesty

Never claim the software can do something without a passing test. Follow `TESTING.md`, keep `SUPPORTED.md` honest, and benchmark models per `BENCHMARKS.md`. Model-specific instructions live in `models/<model>/`.

## Releases

Gantrel ships on two channels, Nightly and Stable. See `RELEASES.md`. Never push directly to `stable`.

## Repository layout

- `AGENTS.md`: this file
- `CLAUDE.md`: Claude Code entry point, points here
- `DESIGN.md`: design system and UX rules, owned by the designer
- `RELEASES.md`: Nightly and Stable channels
- `CONTRIBUTING.md`: how to contribute, including design work and coauthorship
- `TESTING.md`, `SUPPORTED.md`, `BENCHMARKS.md`: accuracy, honest scope and model benchmarks
- `skills/maintainer/`, `skills/runtime/`: original, tested skills
- `models/`: per-model instructions
- `tests/`, `benchmarks/results/`: tests and published results
- `design/`: design exports and notes
