"""Deterministic contract and math verification tests for skills/runtime/dfm-accommodation."""

from __future__ import annotations

import ast
import math
import re
from pathlib import Path

import pytest

from gantrel_printer.plan import dfm_verify

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "runtime" / "dfm-accommodation" / "SKILL.md"
DFM_VERIFY_PATH = ROOT / "src" / "gantrel_printer" / "plan" / "dfm_verify.py"

DROPPED_REPOS = ("MP-AI-20", "DDC_Skills", "ShopPrentice")
FORBIDDEN_IMPORTS = {"socket", "urllib", "http", "requests", "adapters", "subprocess"}


def test_frontmatter_sections_style_and_clean_sources():
    text = SKILL.read_text(encoding="utf-8")
    assert re.match(r"^---\nname: dfm-accommodation\ndescription: .+\n---\n", text)
    for section in ("## Goal", "## Inputs", "## Steps", "## Rules and checks", "## Sources"):
        assert section in text, f"missing {section}"
    # Gantrel skill style rule: no em/en dashes or invisible Unicode control chars
    assert chr(0x2014) not in text and chr(0x2013) not in text
    assert not re.search(r"[\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069]", text)
    for repo in DROPPED_REPOS:
        assert repo not in text, f"unexpected citation to dropped repo {repo}"


def test_dfm_verify_pure_stdlib_imports():
    tree = ast.parse(DFM_VERIFY_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(FORBIDDEN_IMPORTS), imported & FORBIDDEN_IMPORTS


def test_check_slotted_hole():
    # Passing without washer/backing
    res = dfm_verify.check_slotted_hole(12.0, 5.5, 6.0)
    assert res["ok"] is True
    assert math.isclose(res["travel_mm"], 6.5, abs_tol=1e-4)
    assert res["errors"] == []

    # Passing with washer and adequate backing (exact boundary)
    res_ok_washer = dfm_verify.check_slotted_hole(
        10.0, 4.0, 6.0, washer_od_mm=12.0, backing_width_mm=12.0
    )
    assert res_ok_washer["ok"] is True
    assert res_ok_washer["travel_mm"] == 6.0
    assert res_ok_washer["errors"] == []

    # Failing: slot_length <= fastener_d
    res_short = dfm_verify.check_slotted_hole(5.0, 5.5, 2.0)
    assert res_short["ok"] is False
    assert any("slot_length" in e for e in res_short["errors"])
    assert any("slot travel" in e for e in res_short["errors"])

    # Failing: slot_length > fastener_d but travel < required_travel
    res_low_travel = dfm_verify.check_slotted_hole(8.0, 5.0, 4.0)
    assert res_low_travel["ok"] is False
    assert res_low_travel["travel_mm"] == 3.0
    assert len(res_low_travel["errors"]) == 1
    assert "slot travel" in res_low_travel["errors"][0]

    # Failing: backing_width < washer_od
    res_narrow = dfm_verify.check_slotted_hole(
        12.0, 5.0, 6.0, washer_od_mm=15.0, backing_width_mm=12.0
    )
    assert res_narrow["ok"] is False
    assert len(res_narrow["errors"]) == 1
    assert "backing width" in res_narrow["errors"][0]


def test_check_round_slot_datum_pattern():
    # Passing: 1 round datum + radial slots (0, 90, 45, and wrap-around near 0/180)
    good_holes = [
        {"x": 0.0, "y": 0.0, "kind": "round"},
        {"x": 50.0, "y": 0.0, "kind": "slot", "slot_angle_deg": 0.0},
        {"x": 0.0, "y": 40.0, "kind": "slot", "slot_angle_deg": 90.0},
        {"x": 30.0, "y": 30.0, "kind": "slot", "slot_angle_deg": 45.0},
        {"x": -50.0, "y": 0.0, "kind": "slot", "slot_angle_deg": 178.0},
    ]
    res = dfm_verify.check_round_slot_datum_pattern(good_holes)
    assert res["ok"] is True
    assert res["datum"] == (0.0, 0.0)
    assert res["round_count"] == 1
    assert res["slot_count"] == 4
    assert res["errors"] == []

    # Failing: 0 round holes
    res_zero = dfm_verify.check_round_slot_datum_pattern(
        [{"x": 10.0, "y": 0.0, "kind": "slot", "slot_angle_deg": 0.0}]
    )
    assert res_zero["ok"] is False
    assert res_zero["datum"] is None
    assert any("expected exactly 1 round datum hole" in e for e in res_zero["errors"])

    # Failing: 2 round holes
    res_two = dfm_verify.check_round_slot_datum_pattern(
        [
            {"x": 0.0, "y": 0.0, "kind": "round"},
            {"x": 20.0, "y": 0.0, "kind": "round"},
        ]
    )
    assert res_two["ok"] is False
    assert res_two["datum"] is None
    assert any("got 2" in e for e in res_two["errors"])

    # Failing: unknown hole kind
    res_unknown = dfm_verify.check_round_slot_datum_pattern(
        [
            {"x": 0.0, "y": 0.0, "kind": "round"},
            {"x": 20.0, "y": 0.0, "kind": "oval"},
        ]
    )
    assert res_unknown["ok"] is False
    assert any("unknown hole kind" in e for e in res_unknown["errors"])

    # Failing: slot coincides with datum
    res_coincide = dfm_verify.check_round_slot_datum_pattern(
        [
            {"x": 5.0, "y": 5.0, "kind": "round"},
            {"x": 5.0, "y": 5.0, "kind": "slot", "slot_angle_deg": 0.0},
        ]
    )
    assert res_coincide["ok"] is False
    assert any("coincides with datum" in e for e in res_coincide["errors"])

    # Failing: slot missing slot_angle_deg or None
    res_missing_ang = dfm_verify.check_round_slot_datum_pattern(
        [
            {"x": 0.0, "y": 0.0, "kind": "round"},
            {"x": 20.0, "y": 0.0, "kind": "slot"},
            {"x": 0.0, "y": 20.0, "kind": "slot", "slot_angle_deg": None},
        ]
    )
    assert res_missing_ang["ok"] is False
    assert len(res_missing_ang["errors"]) == 2
    assert all("missing slot_angle_deg" in e for e in res_missing_ang["errors"])

    # Failing: slot axis deviates beyond tolerance
    res_bad_ang = dfm_verify.check_round_slot_datum_pattern(
        [
            {"x": 0.0, "y": 0.0, "kind": "round"},
            {"x": 40.0, "y": 0.0, "kind": "slot", "slot_angle_deg": 90.0},
        ],
        angle_tol_deg=5.0,
    )
    assert res_bad_ang["ok"] is False
    assert any("deviates" in e for e in res_bad_ang["errors"])


def test_recommended_teardrop_roof_offset():
    small = dfm_verify.recommended_teardrop_roof_offset(4.0)
    assert small == {"roof_angle_deg": 90.0, "roof_offset_mm": 0.0, "regime": "small_point"}

    boundary = dfm_verify.recommended_teardrop_roof_offset(6.0)
    assert boundary == {"roof_angle_deg": 90.0, "roof_offset_mm": 0.0, "regime": "small_point"}

    large = dfm_verify.recommended_teardrop_roof_offset(10.0)
    assert large == {"roof_angle_deg": 90.0, "roof_offset_mm": 0.4, "regime": "large_offset"}


def test_check_counterbore_bridging():
    # Passing at 0.2 mm and 0.3 mm layer heights
    ok_02 = dfm_verify.check_counterbore_bridging(0.2, 0.2, 0.4)
    assert ok_02["ok"] is True
    assert ok_02["expected_step1_mm"] == 0.2
    assert ok_02["expected_step2_mm"] == 0.4
    assert ok_02["errors"] == []

    ok_03 = dfm_verify.check_counterbore_bridging(0.3, 0.32, 0.58)
    assert ok_03["ok"] is True

    # Failing step1 only
    bad_s1 = dfm_verify.check_counterbore_bridging(0.2, 0.4, 0.4)
    assert bad_s1["ok"] is False
    assert len(bad_s1["errors"]) == 1
    assert "step1" in bad_s1["errors"][0]

    # Failing step2 only
    bad_s2 = dfm_verify.check_counterbore_bridging(0.2, 0.2, 0.6)
    assert bad_s2["ok"] is False
    assert len(bad_s2["errors"]) == 1
    assert "step2" in bad_s2["errors"][0]

    # Failing both
    bad_both = dfm_verify.check_counterbore_bridging(0.2, 0.0, 0.1)
    assert bad_both["ok"] is False
    assert len(bad_both["errors"]) == 2


def test_check_slicer_rules():
    # Clean passing run
    ok = dfm_verify.check_slicer_rules(0.4, 0.2, "gyroid", under_load=True, filament="PLA")
    assert ok["ok"] is True
    assert ok["recommended_layer_height_mm"] == 0.2
    assert ok["errors"] == []
    assert ok["warnings"] == []

    # Layer height exceeds 0.75 * nozzle_d -> error
    bad_lh = dfm_verify.check_slicer_rules(0.4, 0.35, "triangular")
    assert bad_lh["ok"] is False
    assert any("layer_height" in e for e in bad_lh["errors"])

    # Layer height deviates > 0.06 from 0.5 * nozzle_d -> warning, still ok
    warn_lh = dfm_verify.check_slicer_rules(0.4, 0.12, "cubic")
    assert warn_lh["ok"] is True
    assert any("deviates" in w for w in warn_lh["warnings"])

    # Grid infill -> error
    bad_grid = dfm_verify.check_slicer_rules(0.4, 0.2, "Grid")
    assert bad_grid["ok"] is False
    assert any("grid infill" in e for e in bad_grid["errors"])

    # Non-structural infill under load -> warning, still ok
    warn_load = dfm_verify.check_slicer_rules(0.4, 0.2, "rectilinear", under_load=True)
    assert warn_load["ok"] is True
    assert any("gyroid or triangular" in w for w in warn_load["warnings"])

    # Carbon-fiber filament without hardened nozzle -> error
    bad_cf = dfm_verify.check_slicer_rules(0.4, 0.2, "gyroid", filament="PLA-CF", hardened_nozzle=False)
    assert bad_cf["ok"] is False
    assert any("hardened steel nozzle" in e for e in bad_cf["errors"])

    ok_cf = dfm_verify.check_slicer_rules(0.4, 0.2, "gyroid", filament="PETG-CF", hardened_nozzle=True)
    assert ok_cf["ok"] is True

    # Fume-emitting polymers without ventilation -> error; PA-CF requires both
    bad_abs = dfm_verify.check_slicer_rules(0.4, 0.2, "gyroid", filament="ABS", ventilation=False)
    assert bad_abs["ok"] is False
    assert any("ventilation" in e for e in bad_abs["errors"])

    bad_pacf = dfm_verify.check_slicer_rules(
        0.4, 0.2, "gyroid", filament="PA-CF", hardened_nozzle=False, ventilation=False
    )
    assert bad_pacf["ok"] is False
    assert len(bad_pacf["errors"]) == 2

    ok_pacf = dfm_verify.check_slicer_rules(
        0.4, 0.2, "gyroid", filament="PA-CF", hardened_nozzle=True, ventilation=True
    )
    assert ok_pacf["ok"] is True

    # Foaming LW-PLA -> warning
    lw = dfm_verify.check_slicer_rules(0.4, 0.2, "gyroid", filament="LW-PLA")
    assert lw["ok"] is True
    assert any("LW-PLA" in w for w in lw["warnings"])


@pytest.mark.parametrize(
    ("filament", "needs_vent"),
    [
        ("CF-PETG", False),
        ("CF-PLA", False),
        ("CF-PA", True),
        ("PLA CF", False),
        ("PLACF", False),
        ("PA6-CF", True),
        ("PA12-CF", True),
    ],
)
def test_check_slicer_rules_cf_variants(filament: str, needs_vent: bool):
    bad = dfm_verify.check_slicer_rules(
        0.4,
        0.2,
        "gyroid",
        filament=filament,
        hardened_nozzle=False,
        ventilation=needs_vent,
    )
    assert bad["ok"] is False
    assert any("hardened steel nozzle" in e for e in bad["errors"])

    good = dfm_verify.check_slicer_rules(
        0.4,
        0.2,
        "gyroid",
        filament=filament,
        hardened_nozzle=True,
        ventilation=needs_vent,
    )
    assert good["ok"] is True
    assert good["errors"] == []


@pytest.mark.parametrize(
    "filament",
    ["PCTG", "Transparent PLA", "Opaque PETG", "Pastel PLA"],
)
def test_check_slicer_rules_no_fume_false_positives(filament: str):
    res = dfm_verify.check_slicer_rules(
        0.4,
        0.2,
        "gyroid",
        filament=filament,
        hardened_nozzle=False,
        ventilation=False,
    )
    assert res["ok"] is True
    assert res["errors"] == []


@pytest.mark.parametrize(
    "filament",
    ["PA6-CF", "PA12", "ABS", "ASA", "PC", "Nylon", "CF-PA"],
)
def test_check_slicer_rules_fume_polymers_require_ventilation(filament: str):
    res = dfm_verify.check_slicer_rules(
        0.4,
        0.2,
        "gyroid",
        filament=filament,
        hardened_nozzle=True,
        ventilation=False,
    )
    assert res["ok"] is False
    assert any("ventilation" in e for e in res["errors"])


def test_check_sheet_metal_dfm():
    # Passing without feature width and with adequate feature width
    ok = dfm_verify.check_sheet_metal_dfm(2.0, 2.0, 6.0)
    assert ok["ok"] is True
    assert ok["min_hole_to_bend_mm"] == 6.0
    assert ok["min_tab_width_mm"] == 2.0
    assert ok["errors"] == []

    ok_tab = dfm_verify.check_sheet_metal_dfm(1.5, 1.5, 5.0, min_feature_width_mm=1.5)
    assert ok_tab["ok"] is True

    # Failing hole-to-bend clearance (D < 2*T + R)
    bad_d = dfm_verify.check_sheet_metal_dfm(2.0, 2.0, 5.0)
    assert bad_d["ok"] is False
    assert any("hole/slot-to-bend" in e for e in bad_d["errors"])

    # Failing tab/slot width (W < T)
    bad_w = dfm_verify.check_sheet_metal_dfm(2.0, 2.0, 7.0, min_feature_width_mm=1.5)
    assert bad_w["ok"] is False
    assert any("tab/slot width" in e for e in bad_w["errors"])

    # Failing both
    bad_both = dfm_verify.check_sheet_metal_dfm(2.0, 2.0, 4.0, min_feature_width_mm=1.0)
    assert bad_both["ok"] is False
    assert len(bad_both["errors"]) == 2


def test_check_cnc_dfm():
    # Passing without tool_d_mm
    ok_no_tool = dfm_verify.check_cnc_dfm(18.0, 6.0)
    assert ok_no_tool["ok"] is True
    assert ok_no_tool["min_corner_radius_mm"] == 6.0
    assert ok_no_tool["max_slot_depth_mm"] is None
    assert ok_no_tool["errors"] == []

    # Passing with tool_d_mm and valid slot_depth_mm
    ok_tool = dfm_verify.check_cnc_dfm(12.0, 4.5, tool_d_mm=6.0, slot_depth_mm=24.0)
    assert ok_tool["ok"] is True
    assert ok_tool["max_slot_depth_mm"] == 24.0

    # Failing: sharp 90-deg corner (R <= 0)
    bad_sharp = dfm_verify.check_cnc_dfm(15.0, 0.0)
    assert bad_sharp["ok"] is False
    assert any("EDM" in e for e in bad_sharp["errors"])

    # Failing: 0 < R < depth/3
    bad_r = dfm_verify.check_cnc_dfm(18.0, 4.0)
    assert bad_r["ok"] is False
    assert any("depth/3" in e for e in bad_r["errors"])

    # Failing: slot_depth > 4 * tool_d
    bad_slot = dfm_verify.check_cnc_dfm(12.0, 4.0, tool_d_mm=4.0, slot_depth_mm=20.0)
    assert bad_slot["ok"] is False
    assert bad_slot["max_slot_depth_mm"] == 16.0
    assert any("milling slot depth" in e for e in bad_slot["errors"])


@pytest.mark.parametrize("bad_attachment", ["rigid", "glued", "fixed_round", "screwed_tight"])
def test_check_woodworking_dfm_cross_grain_failures(bad_attachment: str):
    res = dfm_verify.check_woodworking_dfm(200.0, kerf_mm=3.175, n_cuts=4, cross_grain_attachment=bad_attachment)
    assert res["ok"] is False
    assert math.isclose(res["total_kerf_loss_mm"], 12.7, abs_tol=1e-4)
    assert any("solid-wood panel" in e for e in res["errors"])


@pytest.mark.parametrize("bad_corner", ["sharp", "square", "90deg", "none"])
def test_check_woodworking_dfm_router_corner_failures(bad_corner: str):
    res = dfm_verify.check_woodworking_dfm(100.0, cnc_router_inside_corner=bad_corner)
    assert res["ok"] is False
    assert any("dog-bone or T-bone" in e for e in res["errors"])


def test_check_woodworking_dfm_passing_cases():
    # Wide panel with slotted attachment + dogbone corner
    ok_wide = dfm_verify.check_woodworking_dfm(
        300.0,
        kerf_mm=3.0,
        n_cuts=3,
        cross_grain_attachment="slotted",
        cnc_router_inside_corner="dogbone",
    )
    assert ok_wide["ok"] is True
    assert ok_wide["total_kerf_loss_mm"] == 9.0
    assert ok_wide["errors"] == []

    # Narrow panel (<150 mm) with rigid attachment + no router corner check
    ok_narrow = dfm_verify.check_woodworking_dfm(120.0, cross_grain_attachment="rigid")
    assert ok_narrow["ok"] is True
    assert ok_narrow["errors"] == []
