# Gantrel

Gantrel is an open-source 3D design studio built for local AI. It starts with 3D printing and grows into product design, for hobbyists up to professionals.

Think of it as precise parametric CAD (like FreeCAD), freeform modeling and rendering (like Blender), and an agent coding workspace (like t3code) combined into one easy app that a local model can drive.

**First version (planned for Feb 1, 2027):** an agent workspace for 3D printing, built on a fork of [t3code](https://github.com/pingdotgg/t3code). A local model writes and edits parts using existing CAD libraries (build123d or CadQuery), shows them in a 3D viewer with an inline mode, slices them, and sends them to your printer after you confirm. It connects to Klipper, OctoPrint, PrusaLink, Bambu Lab and Creality printers and their cameras, and agents can write adapters for other devices with your approval. Product design comes next. Architecture and building design are out of scope for now.

The parts and licenses are in [docs/STACK.md](docs/STACK.md), and the printer plan and safety rules are in [docs/PRINTERS.md](docs/PRINTERS.md).

## What it will do (planned)

Nothing below is built yet. See [SUPPORTED.md](SUPPORTED.md) for what works today.


- Lets the user describe what they want and has the model design it.
- Produces printable parts first, then product models.
- Takes photos from the user as reference. Hold a standard ruler up in the photo and Gantrel uses it to get real-world dimensions. They're accurate only near the ruler's plane, so the app shows its error.
- Researches on its own with built-in search (SearXNG and more) and browser automation to find specs, standards, materials and references.
- Connects to 3D printers on your network and shows their cameras. A print never starts without your confirm.
- Makes renders and short videos of a design.

## Skills are the core

Gantrel's skills are standardized, precise and tested. Every skill follows one strict format with clear instructions and specifics that force the model to do the work right: correct units, valid geometry and printable tolerances. A weak skill is a bug.

## Autoresearch matters

Autoresearch is central to Gantrel, not an add-on. Good design depends on real information like part dimensions, material limits and existing designs. Gantrel's models are expected to research before they design and to cite what they found. Contributors should treat research quality as seriously as geometry quality.

## Local first

Gantrel runs on local models, so designs, photos and research stay on the user's machine.

## Setup

Gantrel runs on [Fonsviva](https://github.com/baney75/Fonsviva), the shared local compute layer. If Fonsviva is already installed, Gantrel uses it and you pick models inside the app. If not, the app installs it for you and walks you through setup. Cloud providers are set up only in Fonsviva, for personal use only.

Agents setting this up for someone: start at [docs/agents.md](docs/agents.md) or [llms.txt](llms.txt). Site: https://baney75.github.io/Gantrel/

## Status

Early planning. Contributions and ideas are welcome.

## License

MIT
