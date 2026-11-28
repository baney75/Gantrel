---
name: pcb-kicad-dfm
description: Audit KiCad schematics and PCB layouts for standard fabrication DFM minimums, IPC-2221 trace current width, LDO thermal junction temperature, RC filter cutoffs, EMC reference ground planes, decoupling and ESD protection placement, and ERC/DRC/BOM release gates. Use when designing or reviewing electronic hardware, PCBs, schematics, or Gerber fabrication outputs.
---

# pcb-kicad-dfm

## Goal

Catch fabrication, thermal, signal-integrity, EMC, and BOM errors before generating Gerbers or ordering boards from a PCB fab.

## Inputs

- PCB fab rules (trace/space, via drill/pad, copper-to-edge in mm), copper weight (oz), power rail voltages/currents, thermal resistance `Rth_ja` (C/W), ambient `Ta` (C), filter `R`/`C` values, and KiCad schematic/layout architecture.

## Steps

1. Extract EVERY exact number from the prompt (never copy example values).
2. Compute annular ring `(pad - drill)/2`, LDO `power_w = (Vin - Vout)*Iout`, `tj_c = Ta + power_w*Rth_ja`, or `fc_hz = 1/(2*pi*R*C)` to final decimal numbers.
3. Evaluate every limit strictly: if ANY `actual < min` or `tj_c > Tj_max`, set `"verdict": "FAIL"`; set `"PASS"` only when ALL checks pass.
4. When structured JSON is requested, output ONLY one valid raw JSON object (`{...}`) with evaluated decimal numbers (NEVER write math operators inside JSON, NEVER emit `<tool_call>` or XML), exact booleans (`true`/`false`), and exact requested keys.

## Rules and checks

### 1. Standard 2-Layer / 4-Layer PCB Fab DFM Minimums

- **Minimum trace width & spacing:** `min_std_trace_mm = 0.127` mm (`5 mil`).
- **Minimum via drill diameter:** `0.30` mm.
- **Via annular ring:** `annular_ring_mm = (via_pad_mm - via_drill_mm) / 2`.
  - Standard minimum annular ring: `0.15` mm (e.g., `0.30` mm drill requires `>= 0.60` mm pad).
  - If `annular_ring_mm < 0.15` mm, `verdict = "FAIL"`.
- **Minimum copper-to-board-edge clearance:** `0.30` mm. If copper-to-edge `< 0.30` mm, `verdict = "FAIL"`.

### 2. Thermal & Circuit Math

- **LDO power dissipation & junction temperature:**
  - `power_w = (Vin - Vout) * Iout`.
  - `tj_c = Ta + power_w * Rth_ja`.
  - `verdict = "PASS"` if `tj_c <= Tj_max` (typically `125 C`), else `"FAIL"`.
- **First-order RC low-pass cutoff frequency:**
  - `fc_hz = 1 / (2 * pi * R * C)` (with `R` in ohms, `C` in farads; `1 kOhm * 100 nF = 1e-4 s -> 1592 Hz`; `10 kOhm * 10 nF = 1e-4 s -> 1592 Hz`).
- **IPC-2221 trace width (external vs internal copper):**
  - Formula: `I = k * (dT^0.44) * (A^0.725)` with `k = 0.048` (external) vs `k = 0.024` (internal).
  - Because internal layers dissipate less heat (`k` is half), an internal trace must be **`wider`** than an external trace for the same current and temperature rise, by approximately **`2.6`x** (`2^(1/0.725) = 2.60`).

### 3. EMC Pre-Compliance & KiCad Release Gates

- **Reference ground plane:** never route high-speed clocks or signals across a split in their adjacent ground plane (`verdict = "FAIL"`, `primary_fix = "continuous_ground_plane"`).
- **4-layer stackup:** place an unbroken solid GND reference plane on **`L2`** directly beneath L1 signals, and length-match high-speed differential pairs (`length_match_diff_pairs = true`).
- **Decoupling & ESD placement:**
  - Place `100 nF` ceramic decoupling capacitors **`adjacent_to_ic_power_pins`** (shortest loop to VCC/GND).
  - Place ESD TVS diodes **`at_external_connector`** (first component on entering I/O lines).
- **Switching regulators:** keep the hot switching current loop (input cap, switch node, inductor) minimal (`hot_loop_rule = "minimize_loop_area"`) and keep switching inductors clear of sensitive analog traces (`keep_analog_clear = true`).
- **KiCad pre-fab gates:**
  - BOTH ERC (schematic) and DRC (PCB) must pass with zero unresolved errors (`require_zero_erc_drc = true`), and power input nets require `PWR_FLAG` or explicit power drivers (`require_power_driver = true`).
  - Cross-check pinouts and absolute max ratings against official datasheets (`verify_datasheets = true`) and verify BOM MPN matches exact PCB footprint (`verify_bom_footprint = true`).

## Sources

- IPC-2221 Generic Standard on Printed Board Design; standard 2/4-layer PCB fab DFM minimums (JLCPCB / PCBWay).
- Clean-room KiCad schematic, EMC pre-compliance, and BOM verification patterns informed by `aklofas/kicad-happy` (MIT, SHA `6b9767e1`, clean-room `skills/*/SKILL.md` only) and `mixelpixx/KiCAD-MCP-Server` (MIT, SHA `2e0ae6cf`, reference only).
