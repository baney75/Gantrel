"""Deterministic contract and verifier tests for skills/runtime/architecture-home-design."""

from __future__ import annotations

import ast
import math
import re
import sys
from pathlib import Path

from gantrel_printer.plan import arch_verify

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "runtime" / "architecture-home-design" / "SKILL.md"
VERIFIER = ROOT / "src" / "gantrel_printer" / "plan" / "arch_verify.py"

FORBIDDEN_IMPORTS = {"socket", "urllib", "http", "requests", "adapters", "subprocess"}
DROPPED_REPOS = ("MP-AI-20", "DDC_Skills", "ShopPrentice")


def test_frontmatter_sections_style_and_sources():
    text = SKILL.read_text(encoding="utf-8")
    assert re.match(r"^---\nname: architecture-home-design\ndescription: .+\n---\n", text)
    for section in ("## Goal", "## Inputs", "## Steps", "## Rules and checks", "## Sources"):
        assert section in text, f"missing {section}"
    # No em/en dashes or invisible Unicode control chars
    assert chr(0x2014) not in text and chr(0x2013) not in text
    assert not re.search(r"[\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069]", text)
    # No citations to dropped repos
    for repo in DROPPED_REPOS:
        assert repo not in text, f"dropped repo cited: {repo}"


def test_arch_verify_pure_stdlib_imports():
    source = VERIFIER.read_text(encoding="utf-8")
    assert chr(0x2014) not in source and chr(0x2013) not in source
    tree = ast.parse(source, filename=str(VERIFIER))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative imports not permitted in pure stdlib verifier"
            if node.module:
                imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint(FORBIDDEN_IMPORTS), f"forbidden imports: {imported_roots & FORBIDDEN_IMPORTS}"
    non_stdlib = imported_roots - sys.stdlib_module_names
    assert not non_stdlib, f"non-stdlib imports found: {non_stdlib}"


def test_check_stair_and_circulation():
    # Empty call passes
    assert arch_verify.check_stair_and_circulation() == {"ok": True, "errors": []}

    # Exact IRC boundary passing case (standard door)
    res = arch_verify.check_stair_and_circulation(
        hallway_width_in=36.0,
        riser_in=7.75,
        tread_in=10.0,
        headroom_in=80.0,
        stair_width_in=36.0,
        door_width_in=32.0,
        pull_latch_clearance_in=18.0,
        universal_access=False,
    )
    assert res["ok"] is True and res["errors"] == []

    # Universal access door passing at 36 in
    res_ua = arch_verify.check_stair_and_circulation(
        door_width_in=36.0,
        universal_access=True,
    )
    assert res_ua["ok"] is True and res_ua["errors"] == []

    # Individual failure branches
    assert arch_verify.check_stair_and_circulation(hallway_width_in=35.5)["ok"] is False
    assert arch_verify.check_stair_and_circulation(riser_in=7.8)["ok"] is False
    assert arch_verify.check_stair_and_circulation(tread_in=9.75)["ok"] is False
    assert arch_verify.check_stair_and_circulation(headroom_in=79.0)["ok"] is False
    assert arch_verify.check_stair_and_circulation(stair_width_in=35.0)["ok"] is False
    assert arch_verify.check_stair_and_circulation(door_width_in=30.0, universal_access=False)["ok"] is False
    assert arch_verify.check_stair_and_circulation(door_width_in=32.0, universal_access=True)["ok"] is False
    assert arch_verify.check_stair_and_circulation(pull_latch_clearance_in=17.5)["ok"] is False

    # Combined failures report every violation
    multi = arch_verify.check_stair_and_circulation(
        hallway_width_in=32.0,
        riser_in=8.25,
        tread_in=9.5,
        headroom_in=76.0,
        stair_width_in=34.0,
        door_width_in=34.0,
        pull_latch_clearance_in=12.0,
        universal_access=True,
    )
    assert multi["ok"] is False
    assert len(multi["errors"]) == 7


def test_check_kitchen_and_bath():
    # Empty call passes
    empty = arch_verify.check_kitchen_and_bath()
    assert empty["ok"] is True and empty["triangle_perimeter_ft"] is None and empty["errors"] == []

    # Boundary passing case (1-cook)
    res_1 = arch_verify.check_kitchen_and_bath(
        triangle_legs_ft=[4.0, 5.0, 4.0],
        aisle_width_in=42.0,
        multi_cook=False,
        toilet_width_in=30.0,
        toilet_side_cl_in=15.0,
        toilet_front_in=21.0,
        shower_area_sqin=900.0,
        shower_circle_in=30.0,
        shower_opening_in=24.0,
        lav_front_in=21.0,
        lav_side_cl_in=15.0,
    )
    assert res_1["ok"] is True
    assert math.isclose(res_1["triangle_perimeter_ft"], 13.0)

    # Upper perimeter boundary + multi-cook passing
    res_2 = arch_verify.check_kitchen_and_bath(
        triangle_legs_ft=[9.0, 9.0, 8.0],
        aisle_width_in=48.0,
        multi_cook=True,
    )
    assert res_2["ok"] is True
    assert math.isclose(res_2["triangle_perimeter_ft"], 26.0)

    # Kitchen triangle perimeter < 13 and > 26
    low_perim = arch_verify.check_kitchen_and_bath(triangle_legs_ft=[4.0, 4.0, 4.5])
    assert low_perim["ok"] is False
    assert math.isclose(low_perim["triangle_perimeter_ft"], 12.5)

    high_perim = arch_verify.check_kitchen_and_bath(triangle_legs_ft=[9.0, 9.0, 8.5])
    assert high_perim["ok"] is False
    assert math.isclose(high_perim["triangle_perimeter_ft"], 26.5)

    # Kitchen triangle leg bounds (< 4 and > 9) with valid total perimeter
    short_leg = arch_verify.check_kitchen_and_bath(triangle_legs_ft=[3.5, 6.0, 6.0])
    assert short_leg["ok"] is False
    assert any("leg 0" in e for e in short_leg["errors"])

    long_leg = arch_verify.check_kitchen_and_bath(triangle_legs_ft=[9.5, 5.0, 5.0])
    assert long_leg["ok"] is False
    assert any("leg 0" in e for e in long_leg["errors"])

    # Aisles: 1-cook vs multi-cook
    assert arch_verify.check_kitchen_and_bath(aisle_width_in=40.0, multi_cook=False)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(aisle_width_in=44.0, multi_cook=True)["ok"] is False

    # Toilet, shower, lavatory failures
    assert arch_verify.check_kitchen_and_bath(toilet_width_in=29.0)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(toilet_side_cl_in=14.5)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(toilet_front_in=20.0)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(shower_area_sqin=899.0)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(shower_circle_in=29.5)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(shower_opening_in=23.5)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(lav_front_in=20.5)["ok"] is False
    assert arch_verify.check_kitchen_and_bath(lav_side_cl_in=14.0)["ok"] is False


def test_check_framing_and_deflection():
    # Empty call passes
    empty = arch_verify.check_framing_and_deflection()
    assert empty["ok"] is True
    assert empty["max_live_deflection_in"] is None
    assert empty["max_total_deflection_in"] is None
    assert empty["max_joist_hole_in"] is None
    assert empty["max_joist_end_notch_in"] is None

    # Passing framing audit (15 ft = 180 in span, 2x10 actual depth 9.25 in, 2x4 stud 3.5 in)
    res_ok = arch_verify.check_framing_and_deflection(
        span_in=180.0,
        live_deflection_in=0.5,
        total_deflection_in=0.75,
        joist_depth_in=9.25,
        bored_hole_d_in=3.08,
        bored_edge_dist_in=2.0,
        notch_depth_in=2.3125,
        notch_in_middle_third=False,
        bearing_stud_width_in=3.5,
        bearing_stud_notch_in=0.875,
        wall_out_of_plumb_in_per_10ft=0.25,
        stud_bow_in_per_8ft=0.125,
    )
    assert res_ok["ok"] is True
    assert res_ok["max_live_deflection_in"] == 0.5
    assert res_ok["max_total_deflection_in"] == 0.75
    assert res_ok["max_joist_hole_in"] == round(9.25 / 3.0, 4)
    assert res_ok["max_joist_end_notch_in"] == round(9.25 / 4.0, 4)

    # Zero notch in middle third is allowed
    res_zero_mid = arch_verify.check_framing_and_deflection(
        joist_depth_in=9.25,
        notch_depth_in=0.0,
        notch_in_middle_third=True,
    )
    assert res_zero_mid["ok"] is True

    # Live deflection > L/360 and total deflection > L/240
    assert arch_verify.check_framing_and_deflection(span_in=180.0, live_deflection_in=0.51)["ok"] is False
    assert arch_verify.check_framing_and_deflection(span_in=180.0, total_deflection_in=0.76)["ok"] is False

    # Joist bored hole > D/3 and edge distance < 2.0 in
    assert arch_verify.check_framing_and_deflection(joist_depth_in=9.25, bored_hole_d_in=3.2)["ok"] is False
    assert arch_verify.check_framing_and_deflection(joist_depth_in=9.25, bored_edge_dist_in=1.75)["ok"] is False

    # Middle-third no-notch (even small notch fails)
    mid_fail = arch_verify.check_framing_and_deflection(
        joist_depth_in=11.25,
        notch_depth_in=0.5,
        notch_in_middle_third=True,
    )
    assert mid_fail["ok"] is False
    assert any("middle 1/3" in e for e in mid_fail["errors"])

    # End notch > D/4
    end_fail = arch_verify.check_framing_and_deflection(
        joist_depth_in=11.25,
        notch_depth_in=2.9,
        notch_in_middle_third=False,
    )
    assert end_fail["ok"] is False
    assert any("D/4" in e for e in end_fail["errors"])

    # Bearing stud > 25% width (2x6 = 5.5 in -> max 1.375 in)
    assert arch_verify.check_framing_and_deflection(bearing_stud_width_in=5.5, bearing_stud_notch_in=1.375)["ok"] is True
    assert arch_verify.check_framing_and_deflection(bearing_stud_width_in=5.5, bearing_stud_notch_in=1.5)["ok"] is False

    # Wall out-of-plumb and stud bow tolerances
    assert arch_verify.check_framing_and_deflection(wall_out_of_plumb_in_per_10ft=0.3)["ok"] is False
    assert arch_verify.check_framing_and_deflection(stud_bow_in_per_8ft=0.15)["ok"] is False


def test_check_mep_and_building_science():
    # Empty call passes
    empty = arch_verify.check_mep_and_building_science()
    assert empty["ok"] is True
    assert empty["required_drain_slope_in_per_ft"] is None
    assert empty["required_ashrae_62_2_cfm"] is None

    # Passing small drain (<= 2.5 in -> 0.25 in/ft), code ACH50 (< 3.0), NEC, HVAC, ASHRAE 62.2
    # 2000 sqft, 3 bedrooms -> 0.01*2000 + 7.5*(3+1) = 20 + 30 = 50.0 CFM
    res_small = arch_verify.check_mep_and_building_science(
        drain_pipe_d_in=2.5,
        drain_slope_in_per_ft=0.25,
        hvac_trunk_drop_in=8.0,
        nec_width_in=30.0,
        nec_depth_in=36.0,
        nec_height_in=78.0,
        ach50=2.9,
        high_performance=False,
        floor_area_sqft=2000.0,
        bedrooms=3,
        continuous_cfm=50.0,
        kitchen_spot_cfm=100.0,
        bath_spot_cfm=50.0,
    )
    assert res_small["ok"] is True
    assert res_small["required_drain_slope_in_per_ft"] == 0.25
    assert res_small["required_ashrae_62_2_cfm"] == 50.0

    # Passing large drain (>= 3.0 in -> 0.125 in/ft), HVAC upper bound 12 in, high-perf ACH50 (< 1.5)
    res_large = arch_verify.check_mep_and_building_science(
        drain_pipe_d_in=3.0,
        drain_slope_in_per_ft=0.125,
        hvac_trunk_drop_in=12.0,
        ach50=1.2,
        high_performance=True,
    )
    assert res_large["ok"] is True
    assert res_large["required_drain_slope_in_per_ft"] == 0.125

    # Drain slope failures: <= 2.5 in with 0.125 fails; >= 3.0 in with 0.10 fails
    assert arch_verify.check_mep_and_building_science(drain_pipe_d_in=2.0, drain_slope_in_per_ft=0.125)["ok"] is False
    assert arch_verify.check_mep_and_building_science(drain_pipe_d_in=2.5, drain_slope_in_per_ft=0.20)["ok"] is False
    assert arch_verify.check_mep_and_building_science(drain_pipe_d_in=4.0, drain_slope_in_per_ft=0.10)["ok"] is False

    # HVAC trunk drop outside [8, 12] in
    assert arch_verify.check_mep_and_building_science(hvac_trunk_drop_in=7.5)["ok"] is False
    assert arch_verify.check_mep_and_building_science(hvac_trunk_drop_in=12.5)["ok"] is False

    # NEC panel workspace 30x36x78 failures
    assert arch_verify.check_mep_and_building_science(nec_width_in=29.5)["ok"] is False
    assert arch_verify.check_mep_and_building_science(nec_depth_in=35.0)["ok"] is False
    assert arch_verify.check_mep_and_building_science(nec_height_in=77.0)["ok"] is False

    # ACH50 boundary: >= limit fails (strictly < limit required)
    assert arch_verify.check_mep_and_building_science(ach50=3.0, high_performance=False)["ok"] is False
    assert arch_verify.check_mep_and_building_science(ach50=3.5, high_performance=False)["ok"] is False
    assert arch_verify.check_mep_and_building_science(ach50=1.5, high_performance=True)["ok"] is False
    assert arch_verify.check_mep_and_building_science(ach50=2.0, high_performance=True)["ok"] is False

    # ASHRAE 62.2 continuous & kitchen/bath spot CFM failures
    low_cont = arch_verify.check_mep_and_building_science(
        floor_area_sqft=2400.0,
        bedrooms=4,
        continuous_cfm=60.0,  # requires 24 + 37.5 = 61.5 CFM
    )
    assert low_cont["ok"] is False
    assert low_cont["required_ashrae_62_2_cfm"] == 61.5

    assert arch_verify.check_mep_and_building_science(kitchen_spot_cfm=95.0)["ok"] is False
    assert arch_verify.check_mep_and_building_science(bath_spot_cfm=45.0)["ok"] is False
