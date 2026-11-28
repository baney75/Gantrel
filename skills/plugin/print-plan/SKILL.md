---
name: print-plan
description: Plan a 3D print before slicing with the gantrel-printer CLI. Shows how to turn the part on the bed, whether it needs supports, how long it will take, how much filament it uses, and checks with math that every setting suits the printer, the filament and the part. Use when someone asks how to orient or lay a part, whether it needs supports, how long a print takes, how much filament it needs, which settings to use, whether a filament works on their printer, or to check their slicer settings.
---

# print-plan

## Goal

The person knows, for one part on one printer with one filament:

- how to turn the part on the bed,
- whether it needs supports,
- about how long it takes and how much filament it uses,
- the settings, and that every setting passed the check.

Or they know why that printer and filament do not go together.

Planning only reads files. It never talks to a printer, and it never starts a print.

## Inputs

- The part file: STL or 3MF.
- The printer: a paired printer name from `gantrel-printer list`, or a profile key from
  `gantrel-printer profiles` (for example `creality-k2`).
- The filament: PLA, PLA-CF, PETG, PETG-CF, ABS, ASA, TPU, PA, PA-CF, PC, PVA or HIPS.
  For a paired printer, run `gantrel-printer filaments <name> --json` first (the `filaments` tool in Local Studio) to learn the loaded family and slot, then plan with that material.
  Ask the person if you do not know it. Do not guess.
- The goal. Use `quality` unless the person says they want it fast. Use `balanced` for "normal".
  Use `speed` only when they ask for speed.
- Load direction, only if the person says the part takes a load (a hook, a bracket, a clip).
  Ask which way the force pulls in the file's axes: x, y or z.

## Steps

1. Run `command -v gantrel-printer`. If it prints nothing, tell the person to install it with
   `uv tool install git+https://github.com/Students-of-Local/Gantrel`, then stop. Never install it yourself.
2. Run the plan command, with the bash tool, in the foreground:

       gantrel-printer plan <file> --printer <name> --material <filament> --goal quality

   Add `--load-axis z` (or x, or y) when the part takes a load. Add `--write-oriented <out.stl>`
   when the person wants a file already turned the right way.
3. Read the exit code and the output:

   | Exit | Output starts with | What it means | What you do |
   |---|---|---|---|
   | 0 | `Plan for` | A plan that passed every check | Go to step 4 |
   | 1 | `REFUSED: the part is` | The part is bigger than this printer builds | Go to step 5 |
   | 1 | `REFUSED:` (anything else) | This printer cannot print this filament | Go to step 5 |
   | 1 | `ERROR (mesh)` | The file is broken, too big, or not a mesh | Tell the person the error and its advice |
   | 1 | `ERROR (config)` | Unknown printer or filament | Run `gantrel-printer profiles`, fix the name, run again |

4. Tell the person, in this order, using the numbers the command printed:
   - Orientation: the `Orientation:` line (the rotation and the reason).
   - Supports: the `Supports:` line.
   - Time: the `Time:` line. Say it is Gantrel's estimate, and the slicer's number is better.
   - Filament: the `Filament:` line.
   - Every `WARN:` line, in plain words, with its advice. A warning that says "Gantrel's default"
     and "not a printer spec" means Gantrel does not know that limit for this printer: ask the
     person to check it (the hotend's top temperature, whether the nozzle is hardened steel). It
     is not a reason to stop.
   Then follow the `NEXT:` line.
5. Tell the person the `REFUSED:` line and every `FAIL:` line, in plain words. When the part is
   too big, give its size and the printer's, and suggest scaling it down, splitting it, or a
   printer with a bigger build volume; another filament will not help. Otherwise suggest the fix
   the line gives (another filament, or a printer with an enclosure or a hardened nozzle).
   When the line gives both reasons (the part does not fit, and the filament cannot pass on this
   printer), tell the person both. Then follow the `NEXT:` line.
   Do not use `--force` or any other way around it.

## Checking settings the person already has

If the person has settings from a slicer or from `gantrel-printer slice --json`, save them as a
JSON file and run:

    gantrel-printer check <settings.json> --printer <name> --material <filament> --model <file>

Leave out `--model` if there is no part file. With the JSON from `plan --json`, give the
original part file (the check turns it the plan's way) or the `--write-oriented` file. With
settings from anywhere else, the part is checked as the file has it, z up, so give a file turned
the way it will sit on the bed. Exit 0 means every rule passed. Exit 1 means at
least one `FAIL:` line: tell the person each one and its fix. Say the warnings too. A speed or
acceleration warning never means the print fails: the printer runs the move at its own top speed,
or the limit was Gantrel's default and the person should check their printer's.

## Rules and checks

- Never say a time or a weight the command did not print. Never round a FAIL into a pass.
- Never contact the printer for planning. `plan` and `check` read files only.
- Never start or resume a print. A person starts it on the printer.
- Never bypass a refusal with `--force`.
- Every rule the check uses has its formula and numbers in `--json` output. When the person asks
  why, quote the `formula` and `values` of that rule.
- Only a limit the printer's maker publishes (cited in Gantrel's profile) can fail a rule or
  refuse a plan. A limit marked "Gantrel default, not a spec" was not published for that printer:
  the rule warns instead, and you tell the person what to check. Never call that a refusal.

### Slicer craft quick reference

| Topic | Rule |
| --- | --- |
| Overhangs | Gantrel warns past 45 deg from vertical across materials; OrcaSlicer defaults to 60 deg from vertical (30 deg from horizontal). |
| Bridges | Conservative unsupported bridge limit is 5 to 10 mm (8 to 10 mm in ABS); `print-plan` warns hard past 25 mm. |
| Layer height | Start near half the nozzle width (`0.2 mm` for `0.4 mm` nozzle; `0.3 mm` for `0.6 mm` nozzle). |
| Infill under load | Use gyroid or triangular infill. Avoid Grid infill (self-crossing lines collide with the nozzle). |
| Local strength | Use local slicer modifiers to add infill or walls around bolt holes only (not high global infill). |
| Fit-test coupon | Split out a small mounting-interface test coupon (<30 min) before a multi-hour build. |
| Counterbores | In OrcaSlicer/Creality Slicer, enable `partially bridged` or `sacrificial layer` for support-free inverted counterbores. |
| Warping & cutouts | Use `mouse-ear` corner brims on sharp corners. Verify material-saving cutouts in slicer preview (extra perimeters can add filament and time). |
| Filament flags | Hardened steel nozzle for CF (`PLA-CF`, `PETG-CF`, `PA-CF`); flow and temperature tuning for foaming `LW-PLA`; active filtration or external ventilation for `ABS`, `ASA`, `PC`, `PA`. |

## Sources

- Filament numbers and their sources: `src/gantrel_printer/data/materials.json` in the Gantrel
  repository. Every value lists where it came from.
- The formulas: "Planning a print" in `docs/PRINTERS.md`.
- Travis Foss, *10 Smart 3D Printing Tips: Tolerances, Holes, and Slicer Tricks*, DigiKey Maker.io
  (2026-05-04), citing Rahix (`rahix.de/blog/design-for-3d-printing/`) and Slant 3D.
