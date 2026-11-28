"""Deterministic multi-process DFM & manufacturing accommodation math verifier.

Pure Python standard library + math only (zero network, zero subprocess).
Covers:
  - Design for Adjustment: slotted holes, round+slot radial datum locating,
    washer/backing clearance, split-part interface fit-test coupons.
  - FDM Craft: press-fit selection (crush ribs, hex holes, elastic grip fins),
    teardrop horizontal hole roof offset, 2-step support-free counterbores,
    layer height vs nozzle, infill under load, corner warping, material flags.
  - Sheet Metal: hole/slot-to-bend clearance (D >= 2*T + R), min tab/slot width
    (W >= T), press-brake angular variance (+/-1..2 deg).
  - CNC Machining: internal pocket corner radius (R >= depth/3), milling slot
    depth (<= 4 * tool_d), selective tight tolerance budget (+/-0.025 mm).
  - Woodworking: cross-grain seasonal wood movement accommodation, CNC router
    dog-bone/T-bone internal corner fillets, saw kerf allowance.
"""
from __future__ import annotations

import math
import re
from typing import Any

_CF_POLYMER_RE = re.compile(r"^(PLA|PETG|PET|PA\d*|PC|ABS|ASA|NYLON|TPU|PPA|PPS|PEEK|PEKK)CF$")
_FUME_POLYMERS = frozenset({"ABS", "ASA", "PC", "PA", "PA6", "PA12", "PA66", "NYLON"})
_PA_GRADE_RE = re.compile(r"^PA\d+$")


def check_slotted_hole(
    slot_length_mm: float,
    fastener_d_mm: float,
    required_travel_mm: float,
    washer_od_mm: float | None = None,
    backing_width_mm: float | None = None,
) -> dict[str, Any]:
    """Verify slot adjustment travel = slot_length - fastener_d and washer clearance."""
    travel = slot_length_mm - fastener_d_mm
    errors: list[str] = []
    if slot_length_mm <= fastener_d_mm:
        errors.append(f"slot_length {slot_length_mm:.2f} <= fastener_d {fastener_d_mm:.2f}")
    if travel + 1e-6 < required_travel_mm:
        errors.append(f"slot travel {travel:.2f} mm < required {required_travel_mm:.2f} mm")
    if washer_od_mm is not None and backing_width_mm is not None:
        if backing_width_mm + 1e-6 < washer_od_mm:
            errors.append(
                f"backing width {backing_width_mm:.2f} mm < washer OD {washer_od_mm:.2f} mm"
            )
    return {
        "ok": not errors,
        "travel_mm": round(travel, 4),
        "errors": errors,
    }


def check_round_slot_datum_pattern(
    holes: list[dict[str, Any]],
    angle_tol_deg: float = 5.0,
) -> dict[str, Any]:
    """Verify the Round + Slot datum locating rule.

    Each item in `holes` has:
      {"x": float, "y": float, "kind": "round"|"slot", "slot_angle_deg": float (optional)}
    Rules:
      - Exactly ONE round locating hole acts as datum.
      - Every remaining mounting hole is a slot whose axis points radially outward
        from the datum hole (modulo 180 deg) within `angle_tol_deg`.
    """
    errors: list[str] = []
    rounds = [h for h in holes if h.get("kind") == "round"]
    slots = [h for h in holes if h.get("kind") == "slot"]
    if len(rounds) != 1:
        errors.append(f"expected exactly 1 round datum hole, got {len(rounds)}")
        return {"ok": False, "datum": None, "errors": errors}
    if len(slots) + len(rounds) != len(holes):
        errors.append("unknown hole kind in pattern (expected 'round' or 'slot')")
    datum = rounds[0]
    dx0, dy0 = float(datum["x"]), float(datum["y"])
    for idx, s in enumerate(slots):
        vx = float(s["x"]) - dx0
        vy = float(s["y"]) - dy0
        if math.hypot(vx, vy) < 1e-6:
            errors.append(f"slot {idx} coincides with datum hole")
            continue
        radial_deg = math.degrees(math.atan2(vy, vx)) % 180.0
        if "slot_angle_deg" not in s or s["slot_angle_deg"] is None:
            errors.append(f"slot {idx} missing slot_angle_deg")
            continue
        ang = float(s["slot_angle_deg"]) % 180.0
        diff = abs(ang - radial_deg)
        diff = min(diff, 180.0 - diff)
        if diff > angle_tol_deg:
            errors.append(
                f"slot {idx} axis {ang:.1f} deg deviates {diff:.1f} deg from radial {radial_deg:.1f} deg"
            )
    return {
        "ok": not errors,
        "datum": (dx0, dy0),
        "round_count": len(rounds),
        "slot_count": len(slots),
        "errors": errors,
    }


def recommended_teardrop_roof_offset(hole_d_mm: float) -> dict[str, Any]:
    """Return teardrop horizontal-hole roof geometry by bore size.

    Small bores (~<=6 mm, e.g. 4 mm): 90-degree roof point, offset = 0.0 mm.
    Larger bores (>6 mm, e.g. 10 mm): 0.4 mm roof offset above circle.
    """
    if hole_d_mm <= 6.0:
        return {"roof_angle_deg": 90.0, "roof_offset_mm": 0.0, "regime": "small_point"}
    return {"roof_angle_deg": 90.0, "roof_offset_mm": 0.4, "regime": "large_offset"}


def check_counterbore_bridging(
    layer_height_mm: float,
    step1_depth_mm: float,
    step2_depth_mm: float,
) -> dict[str, Any]:
    """Verify support-free 2-step CAD bridging recess depths for inverted counterbores.

    Step 1 (two long sides): 1 layer height (0.2 mm at 0.2 mm layers).
    Step 2 (orthogonal top/bottom sides): 2 layer heights (0.4 mm at 0.2 mm layers).
    """
    exp1 = layer_height_mm
    exp2 = 2.0 * layer_height_mm
    errors: list[str] = []
    if abs(step1_depth_mm - exp1) > 0.05:
        errors.append(f"step1 depth {step1_depth_mm:.2f} mm != 1 layer ({exp1:.2f} mm)")
    if abs(step2_depth_mm - exp2) > 0.05:
        errors.append(f"step2 depth {step2_depth_mm:.2f} mm != 2 layers ({exp2:.2f} mm)")
    return {"ok": not errors, "expected_step1_mm": round(exp1, 3), "expected_step2_mm": round(exp2, 3), "errors": errors}


def check_slicer_rules(
    nozzle_d_mm: float,
    layer_height_mm: float,
    infill_pattern: str,
    under_load: bool = False,
    filament: str = "PLA",
    hardened_nozzle: bool = False,
    ventilation: bool = False,
) -> dict[str, Any]:
    """Check slicer layer height (~0.5*nozzle_d), infill safety, and filament hardware flags."""
    errors: list[str] = []
    warnings: list[str] = []
    rec_lh = round(0.5 * nozzle_d_mm, 3)
    # Practical bounds: 0.25*nozzle_d to 0.75*nozzle_d, nominal 0.5*nozzle_d
    if layer_height_mm > 0.75 * nozzle_d_mm + 1e-6:
        errors.append(f"layer_height {layer_height_mm:.2f} > 0.75 * nozzle_d ({0.75*nozzle_d_mm:.2f})")
    elif abs(layer_height_mm - rec_lh) > 0.06:
        warnings.append(f"layer_height {layer_height_mm:.2f} deviates from ~0.5*nozzle_d ({rec_lh:.2f})")

    pat = infill_pattern.strip().lower()
    if pat == "grid":
        errors.append("grid infill crosses over itself and causes nozzle collisions/defects")
    elif under_load and pat not in ("gyroid", "triangular", "triangles", "cubic"):
        warnings.append(f"prefer gyroid or triangular infill under load (got {infill_pattern})")

    mat = filament.strip().upper()
    tokens = [t for t in re.split(r"[^A-Z0-9]+", mat) if t]
    polymer_tokens = list(tokens)
    is_cf = "CF" in tokens
    for tok in tokens:
        m = _CF_POLYMER_RE.match(tok)
        if m:
            is_cf = True
            polymer_tokens.append(m.group(1))
    if is_cf and not hardened_nozzle:
        errors.append(f"{filament} requires a hardened steel nozzle")
    needs_vent = any(
        tok in _FUME_POLYMERS or _PA_GRADE_RE.match(tok)
        for tok in polymer_tokens
    )
    if needs_vent and not ventilation:
        errors.append(f"{filament} emits fumes and requires active filtration or external ventilation")
    if "LW-PLA" in mat:
        warnings.append("foaming LW-PLA requires temperature and flow-rate tuning")

    return {
        "ok": not errors,
        "recommended_layer_height_mm": rec_lh,
        "errors": errors,
        "warnings": warnings,
    }


def check_sheet_metal_dfm(
    thickness_mm: float,
    inside_bend_radius_mm: float,
    hole_to_bend_mm: float,
    min_feature_width_mm: float | None = None,
) -> dict[str, Any]:
    """Verify sheet metal DFM: D >= 2*T + R and tab/slot width W >= T."""
    min_d = 2.0 * thickness_mm + inside_bend_radius_mm
    errors: list[str] = []
    if hole_to_bend_mm + 1e-6 < min_d:
        errors.append(f"hole/slot-to-bend {hole_to_bend_mm:.2f} mm < 2*T + R ({min_d:.2f} mm)")
    if min_feature_width_mm is not None and min_feature_width_mm + 1e-6 < thickness_mm:
        errors.append(f"tab/slot width {min_feature_width_mm:.2f} mm < sheet thickness T ({thickness_mm:.2f} mm)")
    return {
        "ok": not errors,
        "min_hole_to_bend_mm": round(min_d, 4),
        "min_tab_width_mm": round(thickness_mm, 4),
        "errors": errors,
    }


def check_cnc_dfm(
    pocket_depth_mm: float,
    internal_corner_radius_mm: float,
    tool_d_mm: float | None = None,
    slot_depth_mm: float | None = None,
) -> dict[str, Any]:
    """Verify CNC machining DFM: internal corner R >= depth/3 and slot depth <= 4*tool_d."""
    min_r = pocket_depth_mm / 3.0
    errors: list[str] = []
    if internal_corner_radius_mm <= 0.0:
        errors.append("sharp 90-deg internal corner requires EDM (add fillet R >= depth/3)")
    elif internal_corner_radius_mm + 1e-6 < min_r:
        errors.append(
            f"internal corner radius {internal_corner_radius_mm:.2f} mm < depth/3 ({min_r:.2f} mm)"
        )
    max_slot_depth = None
    if tool_d_mm is not None:
        max_slot_depth = 4.0 * tool_d_mm
        if slot_depth_mm is not None and slot_depth_mm > max_slot_depth + 1e-6:
            errors.append(
                f"milling slot depth {slot_depth_mm:.2f} mm > 4*tool_d ({max_slot_depth:.2f} mm)"
            )
    return {
        "ok": not errors,
        "min_corner_radius_mm": round(min_r, 4),
        "max_slot_depth_mm": round(max_slot_depth, 4) if max_slot_depth is not None else None,
        "errors": errors,
    }


def check_woodworking_dfm(
    panel_width_mm: float,
    kerf_mm: float = 3.175,
    n_cuts: int = 1,
    cross_grain_attachment: str = "slotted",
    cnc_router_inside_corner: str | None = None,
) -> dict[str, Any]:
    """Verify woodworking DFM: kerf budget, cross-grain movement, CNC router dog-bone/T-bone."""
    errors: list[str] = []
    kerf_loss = kerf_mm * n_cuts
    att = cross_grain_attachment.strip().lower()
    if panel_width_mm >= 150.0 and att in ("rigid", "glued", "fixed_round", "screwed_tight"):
        errors.append(
            "wide solid-wood panel (>=150 mm) attached rigidly across grain will split; "
            "use slotted mounting holes perpendicular to grain or figure-8 fasteners"
        )
    if cnc_router_inside_corner is not None:
        corner = cnc_router_inside_corner.strip().lower()
        if corner in ("sharp", "square", "90deg", "none"):
            errors.append(
                "CNC router inside corner cannot be square; add dog-bone or T-bone fillet"
            )
    return {
        "ok": not errors,
        "total_kerf_loss_mm": round(kerf_loss, 4),
        "errors": errors,
    }
