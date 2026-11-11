# Gantrel

Gantrel is an open-source 3D design studio built for local AI. It covers everything from 3D printing to product design to architecture, for hobbyists up to professionals.

Think of it as precise parametric CAD (like FreeCAD), freeform modeling and rendering (like Blender), and an agent coding workspace (like t3code) combined into one extremely easy app that a local model can drive.

## What it does

- Lets the user describe what they want and has the model design it.
- Produces printable parts, product models, and architectural plans and buildings.
- Takes photos from the user as reference. Hold a standard ruler up in the photo and Gantrel uses it to get real-world dimensions.
- Researches on its own with built-in search (SearXNG and more) and browser automation to find specs, standards, materials and references.

## Skills are the core

Gantrel's skills are standardized and must be powerfully good. Every skill follows one strict format with clear instructions and specifics that force the model to do the work right: correct units, valid geometry, printable tolerances, buildable structures. A weak skill is a bug.

## Autoresearch matters

Autoresearch is central to Gantrel, not an add-on. Good design depends on real information like part dimensions, material limits, building codes and existing designs. Gantrel's models are expected to research before they design and to cite what they found. Contributors should treat research quality as seriously as geometry quality.

## Local first

Gantrel runs on local models, so designs, photos and research stay on the user's machine.

## Setup

Gantrel runs on [Fonsviva](https://github.com/baney75/Fonsviva), the shared local compute layer. If Fonsviva is already installed, Gantrel uses it and you pick models inside the app. If not, the app installs it for you and walks you through setup. Cloud providers are set up only in Fonsviva, for personal use only.

Agents setting this up for someone: start at [docs/agents.md](docs/agents.md) or [llms.txt](llms.txt). Site: https://baney75.github.io/Gantrel/

## Status

Early planning. Contributions and ideas are welcome.

## License

MIT
