---
name: dfm-accommodation
description: Apply real-world manufacturing accommodation, adjustment, press-fit, hole, slicer, sheet-metal, CNC machining, and woodworking DFM rules so designs fit and assemble on real machines without binding or wasted prints. Use when designing or auditing mechanical parts, assemblies, mounting patterns, slicer plans, sheet-metal brackets, CNC pockets, or wood joinery.
---

# dfm-accommodation

## Goal

Turn nominal CAD geometry into parts that accommodate real-world process variation (polymer shrinkage, press-brake angle drift, cutter radius, and seasonal wood movement) and pass deterministic DFM checks before fabrication.

## Inputs

- Process: FDM 3D printing, sheet metal, CNC machining, or woodworking.
- Nominal dimensions, fasteners, nozzle/tool diameter, layer height, material, and mating requirements.

## Steps

1. Identify the manufacturing process and every tolerance stack-up or process constraint that can bind assembly.
2. Calculate exact accommodation values using the deterministic formulas below (substitute the requested numbers; never copy example values).
3. Flag any violation as `FAIL` and provide the exact mechanical fix.
4. When the caller requests structured JSON, output ONLY one valid JSON object matching the requested keys with numeric values (no units inside numbers) and exact enum strings.

## Rules and checks

### 1. Design for Adjustment (All Processes)

- **Slotted holes:** `travel_mm = slot_length_mm - fastener_d_mm`.
  - Always verify flat washer / backing strip clearance: `backing_width_mm >= washer_od_mm` (if narrower, verdict is `FAIL` and `min_backing_mm = washer_od_mm`).
- **Round + Slot datum locating rule:** fix **exactly 1** round locating hole as datum (`round_count = 1`), and make **all remaining** mounting holes radial slots (`slot_count = N - 1`) pointing directly outward from that datum so tolerance stack-up, PLA/PETG shrinkage, press-brake angle drift, or wood movement never binds the assembly.
  - Radial slot angle from datum `(x0, y0)` to hole `(x, y)`: `angle_deg = atan2(y - y0, x - x0) mod 180`:
    - Horizontal from datum (`dx != 0, dy = 0`) -> `0` deg.
    - Vertical from datum (`dx = 0, dy != 0`) -> `90` deg.
    - Equal diagonal (`dx = dy > 0`) -> `45` deg.
- **Split-part interface fit-test coupons:** before committing to a multi-hour full print, split/export only the mating bolt pattern or interface socket as a small `fit_test_coupon` (<30 min) to verify real fit first.

### 2. FDM Press-Fits, Horizontal Holes, Counterbores & Modular Mounts

- **Press-fit primitive selection:**
  - `crush_ribs`: small ridges inside a hole that intentionally deform for a **one-time** tight interference fit.
  - `hex_hole`: **6 contact points** (flats) for a round peg; tight fit with reduced insertion force without thin flexible fins or one-time ridges.
  - `elastic_grip_fins`: flexible fins using plastic elasticity for a **reusable** press fit (repeated removal/reinsertion).
- **Teardrop horizontal holes (printed vertically on bed):**
  - Roof point angle = `90` deg (two 45-degree walls meeting at the crown).
  - Small bores (`<= 6 mm`, e.g. 3.4 mm or 4 mm): `roof_offset_mm = 0.0` (pure 90-deg roof point tangent to circle).
  - Larger bores (`> 6 mm`, e.g. 10 mm or 12 mm): `roof_offset_mm = 0.4` mm above the top of the circle so slight bridge sag still clears the shaft.
- **Support-free inverted counterbores:**
  - **2-step CAD bridging recess:** cut the two longer sides down by `step1_mm = 1 * layer_height` (`0.2` mm at `0.2` mm layers; `0.3` mm at `0.3` mm layers), and cut the orthogonal top/bottom sides down by `step2_mm = 2 * layer_height` (`0.4` mm at `0.2` mm layers; `0.6` mm at `0.3` mm layers).
  - **Slicer-native options (no CAD change, OrcaSlicer / Creality Slicer):** `partially_bridged` or `sacrificial_layer`.
- **Modular flat-print braces:** split angled mounts into reusable brackets plus flat-printing braces (`modular_flat_braces`) so layer lines align with load and supports drop to zero.

### 3. FDM Slicer & Material Craft

- **Layer height:** nominal `layer_height_mm = 0.5 * nozzle_d_mm` (`0.2` mm for `0.4` mm nozzle; `0.3` mm for `0.6` mm nozzle).
- **Infill under load:** use `gyroid` or `triangular` infill. **FAIL / avoid `grid` infill** because self-crossing grid lines cause nozzle collisions and internal defects.
- **Bolt-hole strength:** use `local_modifiers` in the slicer to add extra infill/walls around bolt holes only (do NOT raise global infill to 80% across the entire part).
- **Warping prevention:** use `mouse_ears` corner brims on sharp corners instead of full brims.
- **Material-saving cutouts:** cutouts do **NOT** always save filament (`cutouts_always_save_filament = false`) because extra internal perimeters can use more filament and print time than sparse infill; always `verify_cutouts_in_slicer = true`.
- **Material hardware & safety flags:**
  - Carbon-fiber filaments (`PLA-CF`, `PETG-CF`, `PA-CF`): require a `hardened_steel` nozzle (brittle, wears brass).
  - Foaming `LW-PLA`: requires `flow_and_temp_tuning`.
  - Fume-emitting polymers (`ABS`, `ASA`, `PC`, `PA`): require active filtration or external ventilation (`needs_ventilation = true`).

### 4. Cross-Process Accommodation (Sheet Metal, CNC Machining, Woodworking)

- **Sheet metal:**
  - Minimum hole/slot-to-bend clearance: `min_clearance_mm = 2 * T + R` (`T` = thickness, `R` = inside bend radius). If actual `D < 2*T + R`, verdict is `FAIL`.
  - Minimum tab or slot width: `min_tab_mm = T`. If any tab/slot width `< T`, verdict is `FAIL`.
  - Press-brake angular variance is `+/-1 to 2 deg`: use slotted mounting holes across multi-bend enclosures (`slot_multi_bend = true`).
- **CNC machining:**
  - Minimum internal pocket corner radius: `min_corner_r_mm = pocket_depth / 3` (never sharp 90-deg internal corners without EDM). If `R < depth / 3`, verdict is `FAIL`.
  - Maximum milling slot depth: `max_slot_depth_mm = 4 * tool_d`. If `slot_depth > 4 * tool_d`, verdict is `FAIL`.
  - Tight tolerances (`+/-0.025 mm`): reserve for critical bearing/pin datums only; applying `+/-0.025 mm` globally to cosmetic features is `FAIL`.
- **Woodworking & CNC routing:**
  - Cross-grain seasonal wood movement: never rigidly screw/glue wide solid-wood panels (`>= 150 mm`) across the grain; attach with slotted holes oriented **perpendicular** to the grain or figure-8 fasteners (`slotted_or_figure8`).
  - CNC router internal corners: never leave sharp 90-deg inside corners for square tenons; add `dogbone_or_tbone` fillets.
  - Saw kerf allowance: `total_kerf_loss_mm = kerf_mm * n_cuts`, `usable_width_mm = stock_width_mm - total_kerf_loss_mm`.

## Sources

- `@amypretzel` (2026-02-19): manufacturing accommodation, clearance, adjustment, and print-and-test engineering (`x.com/amypretzel/status/2024530666679865810`).
- Travis Foss, *10 Smart 3D Printing Tips: Tolerances, Holes, and Slicer Tricks*, DigiKey Maker.io (2026-05-04), citing Rahix (`rahix.de/blog/design-for-3d-printing/`) and Slant 3D (`youtube.com/@Slant3D`).
- Primary process DFM standards: Machinery's Handbook (sheet-metal bend clearances, CNC internal corner radii & tolerances) and USDA Forest Products Laboratory *Wood Handbook* (seasonal cross-grain wood movement & joinery accommodation).
