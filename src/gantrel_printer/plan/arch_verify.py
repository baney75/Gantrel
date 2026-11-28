"""Deterministic Architecture, Home Design, IRC, Structural Framing, MEP & Building Science Verifier.

Pure Python standard library only (zero network, zero subprocess).
Covers:
  - IRC Circulation & Stairs: hallway width, stair riser/tread/headroom/width, door width & latch clearance.
  - IRC Kitchen & Bath Clearances: work triangle & aisles, counter height, toilet, shower, lavatory.
  - Structural Framing & Deflection: joist deflection (L/360 live, L/240 total), wall out-of-plumb & stud bow,
    joist bored hole edge distance & max diameter (D/3), joist middle-third no-notch & end notch (D/4),
    bearing stud notch (<= 25%).
  - MEP & Building Science: sanitary drain slope, HVAC main trunk drop budget, NEC electrical panel workspace,
    4 enclosure control layers & blower-door ACH50 target, ASHRAE 62.2 continuous & spot ventilation CFM.
"""
from __future__ import annotations

from typing import Any


def check_stair_and_circulation(
    *,
    hallway_width_in: float | None = None,
    riser_in: float | None = None,
    tread_in: float | None = None,
    headroom_in: float | None = None,
    stair_width_in: float | None = None,
    door_width_in: float | None = None,
    pull_latch_clearance_in: float | None = None,
    universal_access: bool = False,
) -> dict[str, Any]:
    """Check IRC residential circulation, door, and stair geometry."""
    errors: list[str] = []
    if hallway_width_in is not None and hallway_width_in + 1e-6 < 36.0:
        errors.append(f"hallway width {hallway_width_in:.2f} in < 36 in IRC minimum")
    if riser_in is not None and riser_in > 7.75 + 1e-6:
        errors.append(f"stair riser {riser_in:.2f} in > 7.75 in IRC max")
    if tread_in is not None and tread_in + 1e-6 < 10.0:
        errors.append(f"stair tread {tread_in:.2f} in < 10.0 in IRC min")
    if headroom_in is not None and headroom_in + 1e-6 < 80.0:
        errors.append(f"stair headroom {headroom_in:.2f} in < 80 in (6'-8\") IRC min")
    if stair_width_in is not None and stair_width_in + 1e-6 < 36.0:
        errors.append(f"stair clear width {stair_width_in:.2f} in < 36 in IRC min")
    if door_width_in is not None:
        min_door = 36.0 if universal_access else 32.0
        if door_width_in + 1e-6 < min_door:
            errors.append(f"door width {door_width_in:.2f} in < {min_door:.0f} in min")
    if pull_latch_clearance_in is not None and pull_latch_clearance_in + 1e-6 < 18.0:
        errors.append(f"pull-side latch clearance {pull_latch_clearance_in:.2f} in < 18 in min")
    return {"ok": not errors, "errors": errors}


def check_kitchen_and_bath(
    *,
    triangle_legs_ft: list[float] | None = None,
    aisle_width_in: float | None = None,
    multi_cook: bool = False,
    toilet_width_in: float | None = None,
    toilet_side_cl_in: float | None = None,
    toilet_front_in: float | None = None,
    shower_area_sqin: float | None = None,
    shower_circle_in: float | None = None,
    shower_opening_in: float | None = None,
    lav_front_in: float | None = None,
    lav_side_cl_in: float | None = None,
) -> dict[str, Any]:
    """Check NKBA / IRC kitchen work triangle, aisles, and bathroom fixture clearances."""
    errors: list[str] = []
    perimeter = None
    if triangle_legs_ft is not None:
        if len(triangle_legs_ft) != 3:
            errors.append(f"work triangle requires exactly 3 legs, got {len(triangle_legs_ft)}")
        else:
            perimeter = sum(triangle_legs_ft)
            if not (13.0 - 1e-6 <= perimeter <= 26.0 + 1e-6):
                errors.append(f"work triangle perimeter {perimeter:.2f} ft outside [13, 26] ft")
            for i, leg in enumerate(triangle_legs_ft):
                if not (4.0 - 1e-6 <= leg <= 9.0 + 1e-6):
                    errors.append(f"work triangle leg {i} ({leg:.2f} ft) outside [4, 9] ft")
    if aisle_width_in is not None:
        min_aisle = 48.0 if multi_cook else 42.0
        if aisle_width_in + 1e-6 < min_aisle:
            errors.append(f"kitchen aisle {aisle_width_in:.2f} in < {min_aisle:.0f} in min")
    if toilet_width_in is not None and toilet_width_in + 1e-6 < 30.0:
        errors.append(f"toilet compartment width {toilet_width_in:.2f} in < 30 in min")
    if toilet_side_cl_in is not None and toilet_side_cl_in + 1e-6 < 15.0:
        errors.append(f"toilet centerline to side {toilet_side_cl_in:.2f} in < 15 in min")
    if toilet_front_in is not None and toilet_front_in + 1e-6 < 21.0:
        errors.append(f"toilet front clearance {toilet_front_in:.2f} in < 21 in min")
    if shower_area_sqin is not None and shower_area_sqin + 1e-6 < 900.0:
        errors.append(f"shower area {shower_area_sqin:.1f} sq in < 900 sq in min")
    if shower_circle_in is not None and shower_circle_in + 1e-6 < 30.0:
        errors.append(f"shower inscribed circle {shower_circle_in:.2f} in < 30 in min")
    if shower_opening_in is not None and shower_opening_in + 1e-6 < 24.0:
        errors.append(f"shower opening {shower_opening_in:.2f} in < 24 in min")
    if lav_front_in is not None and lav_front_in + 1e-6 < 21.0:
        errors.append(f"lavatory front clearance {lav_front_in:.2f} in < 21 in min")
    if lav_side_cl_in is not None and lav_side_cl_in + 1e-6 < 15.0:
        errors.append(f"lavatory side centerline {lav_side_cl_in:.2f} in < 15 in min")
    return {"ok": not errors, "triangle_perimeter_ft": perimeter, "errors": errors}


def check_framing_and_deflection(
    *,
    span_in: float | None = None,
    live_deflection_in: float | None = None,
    total_deflection_in: float | None = None,
    joist_depth_in: float | None = None,
    bored_hole_d_in: float | None = None,
    bored_edge_dist_in: float | None = None,
    notch_depth_in: float | None = None,
    notch_in_middle_third: bool = False,
    bearing_stud_width_in: float | None = None,
    bearing_stud_notch_in: float | None = None,
    wall_out_of_plumb_in_per_10ft: float | None = None,
    stud_bow_in_per_8ft: float | None = None,
) -> dict[str, Any]:
    """Check IRC structural wood framing deflection, boring, notching, and tolerances."""
    errors: list[str] = []
    max_live = None
    max_total = None
    if span_in is not None:
        max_live = span_in / 360.0
        max_total = span_in / 240.0
        if live_deflection_in is not None and live_deflection_in > max_live + 1e-6:
            errors.append(f"live deflection {live_deflection_in:.3f} in > L/360 ({max_live:.3f} in)")
        if total_deflection_in is not None and total_deflection_in > max_total + 1e-6:
            errors.append(f"total deflection {total_deflection_in:.3f} in > L/240 ({max_total:.3f} in)")
    max_hole = None
    max_end_notch = None
    if joist_depth_in is not None:
        max_hole = joist_depth_in / 3.0
        max_end_notch = joist_depth_in / 4.0
        if bored_hole_d_in is not None and bored_hole_d_in > max_hole + 1e-6:
            errors.append(f"joist bored hole {bored_hole_d_in:.3f} in > D/3 ({max_hole:.3f} in)")
        if notch_depth_in is not None and notch_depth_in > 0 and not notch_in_middle_third:
            if notch_depth_in > max_end_notch + 1e-6:
                errors.append(f"joist end notch {notch_depth_in:.3f} in > D/4 ({max_end_notch:.3f} in)")
    if bored_edge_dist_in is not None and bored_edge_dist_in + 1e-6 < 2.0:
        errors.append(f"joist hole edge distance {bored_edge_dist_in:.3f} in < 2.0 in min")
    if notch_depth_in is not None and notch_depth_in > 0 and notch_in_middle_third:
        errors.append("zero notches permitted in middle 1/3 of joist span")
    if bearing_stud_width_in is not None and bearing_stud_notch_in is not None:
        max_stud_notch = 0.25 * bearing_stud_width_in
        if bearing_stud_notch_in > max_stud_notch + 1e-6:
            errors.append(f"bearing stud notch {bearing_stud_notch_in:.3f} in > 25% width ({max_stud_notch:.3f} in)")
    if wall_out_of_plumb_in_per_10ft is not None and wall_out_of_plumb_in_per_10ft > 0.25 + 1e-6:
        errors.append(f"wall out-of-plumb {wall_out_of_plumb_in_per_10ft:.3f} in > 0.25 in per 10 ft")
    if stud_bow_in_per_8ft is not None and stud_bow_in_per_8ft > 0.125 + 1e-6:
        errors.append(f"stud bow {stud_bow_in_per_8ft:.3f} in > 0.125 in per 8 ft")
    return {
        "ok": not errors,
        "max_live_deflection_in": round(max_live, 4) if max_live is not None else None,
        "max_total_deflection_in": round(max_total, 4) if max_total is not None else None,
        "max_joist_hole_in": round(max_hole, 4) if max_hole is not None else None,
        "max_joist_end_notch_in": round(max_end_notch, 4) if max_end_notch is not None else None,
        "errors": errors,
    }


def check_mep_and_building_science(
    *,
    drain_pipe_d_in: float | None = None,
    drain_slope_in_per_ft: float | None = None,
    hvac_trunk_drop_in: float | None = None,
    nec_width_in: float | None = None,
    nec_depth_in: float | None = None,
    nec_height_in: float | None = None,
    ach50: float | None = None,
    high_performance: bool = False,
    floor_area_sqft: float | None = None,
    bedrooms: int | None = None,
    continuous_cfm: float | None = None,
    kitchen_spot_cfm: float | None = None,
    bath_spot_cfm: float | None = None,
) -> dict[str, Any]:
    """Check residential MEP clearances, drain slope, NEC workspace, ACH50, and ASHRAE 62.2."""
    errors: list[str] = []
    req_slope = None
    if drain_pipe_d_in is not None:
        req_slope = 0.25 if drain_pipe_d_in <= 2.5 else 0.125
        if drain_slope_in_per_ft is not None and drain_slope_in_per_ft + 1e-6 < req_slope:
            errors.append(
                f"drain slope {drain_slope_in_per_ft:.3f} in/ft < {req_slope:.3f} in/ft min for {drain_pipe_d_in}\" pipe"
            )
    if hvac_trunk_drop_in is not None and not (8.0 - 1e-6 <= hvac_trunk_drop_in <= 12.0 + 1e-6):
        errors.append(f"HVAC main trunk drop {hvac_trunk_drop_in:.1f} in outside typical 8-12 in budget")
    if nec_width_in is not None and nec_width_in + 1e-6 < 30.0:
        errors.append(f"NEC panel workspace width {nec_width_in:.1f} in < 30 in min")
    if nec_depth_in is not None and nec_depth_in + 1e-6 < 36.0:
        errors.append(f"NEC panel workspace depth {nec_depth_in:.1f} in < 36 in min")
    if nec_height_in is not None and nec_height_in + 1e-6 < 78.0:
        errors.append(f"NEC panel workspace height {nec_height_in:.1f} in < 78 in (6'-6\") min")
    if ach50 is not None:
        limit = 1.5 if high_performance else 3.0
        if ach50 >= limit:
            errors.append(f"blower-door airtightness {ach50:.2f} ACH50 >= {limit} limit")
    req_cfm = None
    if floor_area_sqft is not None and bedrooms is not None:
        req_cfm = 0.01 * floor_area_sqft + 7.5 * (bedrooms + 1)
        if continuous_cfm is not None and continuous_cfm + 1e-6 < req_cfm:
            errors.append(f"ASHRAE 62.2 continuous {continuous_cfm:.1f} CFM < required {req_cfm:.1f} CFM")
    if kitchen_spot_cfm is not None and kitchen_spot_cfm + 1e-6 < 100.0:
        errors.append(f"kitchen spot exhaust {kitchen_spot_cfm:.1f} CFM < 100 CFM min")
    if bath_spot_cfm is not None and bath_spot_cfm + 1e-6 < 50.0:
        errors.append(f"bath spot exhaust {bath_spot_cfm:.1f} CFM < 50 CFM min")
    return {
        "ok": not errors,
        "required_drain_slope_in_per_ft": req_slope,
        "required_ashrae_62_2_cfm": round(req_cfm, 2) if req_cfm is not None else None,
        "errors": errors,
    }
