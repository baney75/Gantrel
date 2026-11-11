# Open-source stack (planned)

Nothing here is built yet. This is the list of existing projects Gantrel v0 plans to assemble, in build order, with each license and how Gantrel uses it. Gantrel's own code stays MIT.

| Build | Part | License | How Gantrel uses it |
|---|---|---|---|
| 1 | [t3code](https://github.com/pingdotgg/t3code) | MIT | Forked for the desktop app, projects, threads and provider layer. Upstream isn't taking big features, so Gantrel keeps a fork and rebases. |
| 1 | [Local Studio](https://github.com/sybil-solutions/local-studio) | MIT | Sybil's t3code fork; its local provider code. |
| 1 | [Backplane](https://github.com/BackplaneWorks/Backplane) | MIT | A t3code fork for agentic hardware design with KiCad and FreeCAD viewers. Reference for adding CAD panes and skills to a t3code fork. Its KiCad fork keeps KiCad's license (GPL-3.0) and isn't used. |
| 2 | [build123d](https://github.com/gumyr/build123d), [CadQuery](https://github.com/CadQuery/cadquery) | Apache-2.0 | The CAD libraries the model writes code for. |
| 2 | OpenCascade (OCP wheels) | LGPL-2.1 | Used unmodified as a library. |
| 2, 9 | [bubblewrap](https://github.com/containers/bubblewrap) | LGPL-2.0+ | Sandbox on Linux for model-written scripts and agent-written adapters. macOS uses sandbox-exec. |
| 3 | [three.js](https://github.com/mrdoob/three.js) | MIT | 3D viewer. |
| 3 | occt-import-js | LGPL-2.1 | Opens STEP files in the viewer, unmodified. |
| 3, 4, 13 | [trimesh](https://github.com/mikedh/trimesh) | MIT | Mesh import, checks and export. |
| 4 | [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer), [PrusaSlicer](https://github.com/prusa3d/PrusaSlicer), [Creality Print](https://github.com/CrealityOfficial/CrealityPrint) | AGPL-3.0 | Slicing from the command line. Run as separate programs, not linked or modified. |
| 5 | [python-zeroconf](https://github.com/python-zeroconf/python-zeroconf) | LGPL-2.1 | Finding printers on the network. |
| 5 to 8 | Printer hosts and cameras | various | See [PRINTERS.md](PRINTERS.md). |
| 10 | [Obico](https://github.com/TheSpaghettiDetective/obico-server) | AGPL-3.0 | Local failure detection, run unmodified as its own service. If we ever modify it and offer it over a network, we must publish that source. |
| 11 | [SearXNG](https://github.com/searxng/searxng) | AGPL-3.0 | Local search, run unmodified as its own container. |
| 11 | [Playwright](https://github.com/microsoft/playwright) | Apache-2.0 | The research agent's browser. |
| 12 | [OpenCV](https://github.com/opencv/opencv) | Apache-2.0 | Finding the ruler and correcting perspective in reference photos. |
| 13 | [Blender](https://www.blender.org/) | GPL-3.0 | Renders and turntable videos, run headless as a separate program. |
| 13 | FFmpeg | LGPL-2.1 or GPL | Video encoding, run as a separate program. |
| 14 | [Local AI registry](https://github.com/sybil-solutions/local-ai-registry) | MIT | Model recipes and the benchmark. |
| 15 | electron-builder | MIT | Packaging, already used by t3code. |

## License rule

Gantrel links only to MIT, Apache, BSD and LGPL libraries. GPL and AGPL programs run as separate processes or services that Gantrel talks to over a command line or network API, unmodified. Before any of that changes, check the license again and record the decision here.

## After v0

These wants are kept, and come after the first Dev release (planned for Feb 1, 2027): RunPod offload through Fonsviva once Fonsviva has cloud providers, a phone companion (t3code already has mobile apps to start from), agent-made themes, product-design tools beyond printing, and architecture views.
