---
name: architecture-home-design
description: Apply residential architecture, home design, IRC circulation and stair rules, NKBA kitchen and bathroom clearances, wood-frame structural deflection and boring/notching limits, MEP rough-in clearances, NEC panel workspace, building envelope control layers, and ASHRAE 62.2 ventilation formulas. Use when planning, reviewing, or auditing floor plans, home designs, remodels, framing, or MEP layouts.
---

# architecture-home-design

## Goal

Produce code-compliant, buildable residential architectural plans and deterministic compliance audits across circulation, stairs, kitchens, bathrooms, wood framing, plumbing, HVAC, electrical workspace, and building science.

## Inputs

- Architectural dimensions in US customary units (`1 ft = 12 in`) and design tier (standard IRC vs universal access; code-minimum vs high-performance envelope).
- Room types, fixture layouts, joist/stud sizes and spans, drain pipe sizes, conditioned floor area, and bedroom count.

## Steps

1. Classify the audit domain and extract EVERY exact number from the user's request (never copy example values).
2. Compute every limit using the exact formulas below (`L/360`, `L/240`, `D/3`, `D/4`, `0.25*W`, `slope*L_ft`, `0.01*area + 7.5*(bedrooms + 1)`).
3. Evaluate every limit strictly: if ANY actual value is below its minimum (`actual < min`) or above its maximum (`actual > max`), set `"verdict": "FAIL"`; set `"PASS"` only when ALL checked items comply.
4. Keep internal thinking very brief (under 150 words) and emit the raw JSON object immediately without verbose restatements.
5. When structured JSON is requested, output ONLY one valid raw JSON object (`{...}`) with evaluated decimal numbers (NEVER write math operators like `180/360`, NEVER emit `<tool_call>` or XML), exact booleans (`true`/`false`), and exact requested keys.

## Rules and checks

### 1. IRC Circulation, Stairs & Doors

- **Hallway clear width:** minimum `36 in` (42 to 48 in preferred).
- **Residential stairs (IRC):**
  - Max riser height: `7.75 in` (`irc_max_riser_in = 7.75`).
  - Min tread depth: `10.0 in` (`irc_min_tread_in = 10.0`, add 1 in nosing if open risers).
  - Min headroom: `80 in` (`6'-8"`, `irc_min_headroom_in = 80`).
  - Min clear width: `36 in` (`irc_min_width_in = 36`).
- **Interior doors:**
  - Standard interior door min width: `32 in` (`min_standard_door_in = 32`).
  - Universal / accessible door min width: `36 in` (`universal_door_in = 36`).
  - Pull-side latch clearance: minimum `18 in` (`min_pull_latch_in = 18`).

### 2. IRC & NKBA Kitchen and Bathroom Clearances

- **Kitchen work triangle & aisles:**
  - Total perimeter `triangle_perimeter_ft = leg1 + leg2 + leg3` must be `13 to 26 ft`, AND every individual leg must be `4 to 9 ft` (if any leg is `< 4 ft` or `> 9 ft`, `verdict = "FAIL"`).
  - Work aisle width: minimum `42 in` for 1-cook (`min_1cook_aisle_in = 42`), minimum `48 in` for multi-cook (`min_multicook_aisle_in = 48`).
  - Standard counter height: `36 in` AFF.
- **Bathroom clearances:**
  - Toilet compartment: minimum `30 in` total width (`min_toilet_width_in = 30`), at least `15 in` each side from centerline (`min_toilet_side_cl_in = 15`), and minimum `21 in` clear in front.
  - Shower compartment: minimum `900 sq in` interior area (`min_shower_area_sqin = 900`), minimum `30 in` inscribed circle (`min_shower_circle_in = 30`), and minimum `24 in` clear entry opening (`min_shower_opening_in = 24`).
  - Lavatory (sink): minimum `21 in` front clearance (`min_lav_front_in = 21`) and `15 in` side centerline clearance.

### 3. Structural Wood Framing & Deflection (IRC)

- **Floor joist deflection (span `L` in inches):**
  - Max live-load deflection: `max_live_in = L / 360`.
  - Max total-load deflection: `max_total_in = L / 240`.
  - If actual live `> L/360` OR actual total `> L/240`, `verdict = "FAIL"`.
- **Joist boring & notching (actual joist depth `D` in inches; 2x10 = 9.25 in, 2x12 = 11.25 in):**
  - Max bored hole diameter: `max_hole_d_in = D / 3`.
  - Min distance from bored hole edge to top or bottom of joist: `min_edge_dist_in = 2.0 in`.
  - Middle 1/3 of span: **ZERO notches allowed** (`allow_middle_third_notch = false`).
  - End notches (at support, outside middle 1/3): `max_end_notch_in = D / 4`.
- **Bearing wall studs & framing tolerances:**
  - Load-bearing stud max notch: `max_stud_notch_in = 0.25 * stud_width` (25% of actual width; 2x4 = 3.5 in -> 0.875 in; 2x6 = 5.5 in -> 1.375 in).
  - Wall out-of-plumb tolerance: max `0.25 in` (`1/4"`) in 10 ft (`max_plumb_in_per_10ft = 0.25`).
  - Stud bow tolerance: max `0.125 in` (`1/8"`) in 8 ft (`max_bow_in_per_8ft = 0.125`).

### 4. MEP Clearances & Building Science

- **Sanitary drain slope (match pipe diameter first; smaller pipe = steeper slope):**
  - Small pipe diameter `<= 2.5 in` (`1.5 in`, `2.0 in`, `2.5 in`): MUST use `0.25 in/ft` (`1/4"/ft`), so `total_drop_in = 0.25 * L_ft`.
  - Large pipe diameter `>= 3.0 in` (`3.0 in`, `4.0 in`): uses `0.125 in/ft` (`1/8"/ft`), so `total_drop_in = 0.125 * L_ft`.
  - Total drop over run length `L_ft`: `total_drop_in = slope * L_ft`.
- **HVAC main trunk:** reserve `8 to 12 in` vertical drop budget (`hvac_drop_min_in = 8`, `hvac_drop_max_in = 12`).
- **NEC electrical panel dedicated workspace:** minimum `30 in` wide x `36 in` deep x `78 in` (`6'-6"`) high (`nec_min_width_in = 30`, `nec_min_depth_in = 36`, `nec_min_height_in = 78`).
- **Building envelope 4 control layers:** Water Resistive Barrier (WRB), Air Barrier (`code_max_ach50 = 3.0`, `high_perf_max_ach50 = 1.5`; FAIL if `ach50 >= limit`), Vapor Control, Continuous Thermal Control.
- **ASHRAE 62.2 residential ventilation:**
  - Continuous whole-house mechanical ventilation: compute `term1 = 0.01 * floor_area_sqft` and `term2 = 7.5 * (bedrooms + 1)`, then sum `ashrae_62_2_cfm = term1 + term2` (`0.01 * floor_area_sqft + 7.5 * (bedrooms + 1)`).
  - Spot local exhaust minimums: `kitchen_min_cfm = 100`, `bath_min_cfm = 50`.
  - Check ALL THREE limits (`continuous_cfm >= ashrae_62_2_cfm`, `kitchen_spot_cfm >= 100`, `bath_spot_cfm >= 50`): ANY single shortfall sets `verdict = "FAIL"`.

## Sources

- International Residential Code (IRC) stair, door, hallway, bathroom, and wood-frame boring/notching limits; NKBA Kitchen & Bath Planning Guidelines.
- National Electrical Code (NEC 110.26) dedicated panel working space; ASHRAE Standard 62.2 residential ventilation; Building Science Corporation 4-control-layer enclosure fundamentals.
- Verified OSS architectural calculator & BIM references: `Abhinavbwj/Skills-Architects` (MIT, SHA `30a0845d`, Python `architect-calculator` scripts & IBC reference) and `IfcOpenShell/IfcOpenShell` (LGPL-3.0, SHA `9e02d93a`).
