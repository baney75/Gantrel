---
name: mechanical-tolerance-dfm
description: Calculate worst-case and RSS tolerance stack-ups, bolted-joint torque and thread engagement depth, bolt edge and pitch clearances, rectangular beam bending stress and safety factors, and thin-walled pressure vessel hoop and axial stresses. Use when sizing mechanical assemblies, brackets, housings, fasteners, or load-bearing parts.
---

# mechanical-tolerance-dfm

## Goal

Verify mechanical assemblies and structural components with deterministic stack-up, fastener, beam, and pressure-vessel math before committing to fabrication.

## Inputs

- Part nominal dimensions and bilateral tolerances (`+/- tol` in mm), fastener size `d` (mm), preload `F` (N), nut factor `K`, substrate material, loads/moments (`N*mm`), geometry (`b, h, r, t` in mm), internal pressure `P` (MPa), and material yield strength `Sy` (MPa).

## Steps

1. Identify the calculation and extract EVERY exact number from the prompt (never copy example values).
2. Compute every formula to a final decimal number (`wc_min = nom - wc_tol`, `Z = b*h*h/6`, `sigma = M/Z`, `SF = Sy/sigma`).
3. Evaluate every limit strictly: if `wc_min < 0`, `SF < 2.0`, or ANY `actual < min` / `actual > max`, set `"verdict": "FAIL"`; set `"PASS"` only when ALL checks pass.
4. When structured JSON is requested, output ONLY one valid raw JSON object (`{...}`) with evaluated decimal numbers (NEVER write math operators inside JSON, NEVER emit `<tool_call>` or XML) and exact requested keys.

## Rules and checks

### 1. 1D Tolerance Stack-Up (Worst-Case and RSS)

- **Nominal gap:** `nominal_gap_mm = outer_nominal - sum(inner_nominals)`.
- **Worst-Case (WC) tolerance:** `wc_tol_mm = sum(abs(tol_i))` across ALL dimensions in the loop.
- **Worst-Case minimum gap:** `wc_min_gap_mm = nominal_gap_mm - wc_tol_mm`.
  - `wc_verdict = "PASS"` if `wc_min_gap_mm >= 0` (zero interference), else `"FAIL"`.
- **Root-Sum-Square (RSS) tolerance:** `rss_tol_mm = sqrt(sum(tol_i^2))` (for example `sqrt(0.3^2 + 0.4^2) = 0.5`).

### 2. Bolted Joints, Torque, Thread Engagement & Spacing

- **Tightening torque:** `torque_nm = K * F * (d / 1000)` (convert `d` from mm to meters by dividing by `1000`; default dry steel `K = 0.20`).
- **Minimum thread engagement depth (`min_engagement_mm`):**
  - Steel substrate: `1.0 * d`.
  - Cast iron substrate: `1.25 * d`.
  - Aluminum substrate: `1.5 * d`.
  - Plastic / polymer substrate: `2.0 * d`.
  - `verdict = "PASS"` if `actual_engagement >= min_engagement_mm`, else `"FAIL"`.
- **Bolt hole edge distance and pitch spacing:**
  - Minimum edge distance (center to plate edge): `min_edge_dist_mm = 1.5 * d`.
  - Minimum center-to-center pitch spacing: `min_pitch_mm = 3.0 * d`.
  - `verdict = "PASS"` only if BOTH `edge_dist >= 1.5 * d` AND `pitch >= 3.0 * d`; otherwise `"FAIL"`.

### 3. Rectangular Beam Bending Stress

- **Section modulus:** `section_modulus_mm3 = (b * h * h) / 6` (`b` = width mm, `h` = height mm).
- **Peak bending stress:** `bending_stress_mpa = M / section_modulus_mm3` (`M` in `N*mm`, result directly in `MPa` since `1 N/mm^2 = 1 MPa`).
- **Safety factor:** `safety_factor = Sy / bending_stress_mpa`.
- `verdict = "PASS"` if `safety_factor >= 2.0`, else `"FAIL"`.

### 4. Thin-Walled Cylindrical Pressure Vessel

- **Thin-wall validity:** `r / t >= 10` (otherwise thick-walled Lame equations are required).
- **Hoop (circumferential) stress:** `hoop_stress_mpa = (P * r) / t`.
- **Axial (longitudinal) stress:** `axial_stress_mpa = (P * r) / (2 * t) = hoop_stress_mpa / 2`.
- **Safety factor (governs on hoop stress):** `safety_factor = Sy / hoop_stress_mpa`.
- `verdict = "PASS"` if `r / t >= 10` AND `safety_factor >= 2.0`, else `"FAIL"`.

## Sources

- Shigley's *Mechanical Engineering Design* (bolted-joint torque, beam bending, thin-walled cylinders) and ASME Y14.5 / Machinery's Handbook (1D worst-case & RSS tolerance stack-up, thread engagement, edge/pitch minimums).
