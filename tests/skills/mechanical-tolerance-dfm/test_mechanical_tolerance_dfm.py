"""Deterministic contract and engineering math tests for skills/runtime/mechanical-tolerance-dfm."""

from __future__ import annotations

import ast
import math
import re
import sys
from pathlib import Path

import pytest

from gantrel_printer.plan import mech_verify

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "runtime" / "mechanical-tolerance-dfm" / "SKILL.md"
VERIFIER = ROOT / "src" / "gantrel_printer" / "plan" / "mech_verify.py"

FORBIDDEN_IMPORTS = {"socket", "urllib", "http", "requests", "adapters", "subprocess"}
DROPPED_REPOS = ("MP-AI-20", "DDC_Skills", "ShopPrentice")


def test_frontmatter_sections_style_and_sources():
    text = SKILL.read_text(encoding="utf-8")
    assert re.match(r"^---\nname: mechanical-tolerance-dfm\ndescription: .+\n---\n", text)
    for section in ("## Goal", "## Inputs", "## Steps", "## Rules and checks", "## Sources"):
        assert section in text, f"missing {section}"
    assert chr(0x2014) not in text and chr(0x2013) not in text
    assert not re.search(r"[\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069]", text)
    for dropped in DROPPED_REPOS:
        assert dropped not in text, f"dropped repo citation found: {dropped}"


def test_mech_verify_pure_stdlib_imports():
    source = VERIFIER.read_text(encoding="utf-8")
    assert chr(0x2014) not in source and chr(0x2013) not in source
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative imports are not allowed in pure stdlib verifier"
            if node.module:
                imported_roots.add(node.module.split(".")[0])
    assert imported_roots.isdisjoint(FORBIDDEN_IMPORTS), f"forbidden imports: {imported_roots & FORBIDDEN_IMPORTS}"
    allowed = sys.stdlib_module_names | {"__future__"}
    assert imported_roots <= allowed, f"non-stdlib imports: {imported_roots - allowed}"


def test_check_tolerance_stackup_wc_and_rss_branches():
    # Both WC and RSS pass
    res_pass = mech_verify.check_tolerance_stackup(
        nominals_mm=[10.0, 8.0],
        tolerances_mm=[0.3, 0.4],
        signs=[1, -1],
        min_required_gap_mm=0.0,
    )
    assert res_pass["nominal_mm"] == 2.0
    assert res_pass["wc_tol_mm"] == 0.7
    assert res_pass["wc_min_mm"] == 1.3
    assert res_pass["wc_max_mm"] == 2.7
    assert res_pass["rss_tol_mm"] == 0.5
    assert res_pass["rss_min_mm"] == 1.5
    assert res_pass["wc_ok"] is True
    assert res_pass["rss_ok"] is True

    # WC fails while RSS passes (nominal gap 0.6, WC tol 0.7, RSS tol 0.5)
    res_wc_fail = mech_verify.check_tolerance_stackup(
        nominals_mm=[10.6, 10.0],
        tolerances_mm=[0.3, 0.4],
        signs=[1, -1],
        min_required_gap_mm=0.0,
    )
    assert res_wc_fail["nominal_mm"] == 0.6
    assert res_wc_fail["wc_min_mm"] == -0.1
    assert res_wc_fail["rss_min_mm"] == 0.1
    assert res_wc_fail["wc_ok"] is False
    assert res_wc_fail["rss_ok"] is True

    # Both WC and RSS fail (nominal gap 0.4 < rss_tol 0.5)
    res_both_fail = mech_verify.check_tolerance_stackup(
        nominals_mm=[10.4, 10.0],
        tolerances_mm=[0.3, 0.4],
        signs=[1, -1],
        min_required_gap_mm=0.0,
    )
    assert res_both_fail["wc_ok"] is False
    assert res_both_fail["rss_ok"] is False

    # Custom positive minimum required gap
    res_req_gap = mech_verify.check_tolerance_stackup(
        nominals_mm=[10.0, 8.0],
        tolerances_mm=[0.3, 0.4],
        signs=[1, -1],
        min_required_gap_mm=1.4,
    )
    assert res_req_gap["wc_ok"] is False
    assert res_req_gap["rss_ok"] is True


def test_check_fastener_joint_substrates_torque_edge_and_pitch():
    # Torque calculation and passing all checks in steel
    res_steel_ok = mech_verify.check_fastener_joint(
        nominal_d_mm=10.0,
        preload_n=10000.0,
        nut_factor_k=0.20,
        substrate="steel",
        engagement_mm=10.0,
        edge_dist_mm=15.0,
        pitch_mm=30.0,
    )
    assert res_steel_ok["ok"] is True
    assert res_steel_ok["torque_nm"] == 20.0
    assert res_steel_ok["min_engagement_mm"] == 10.0
    assert res_steel_ok["min_edge_dist_mm"] == 15.0
    assert res_steel_ok["min_pitch_mm"] == 30.0
    assert res_steel_ok["errors"] == []

    # No preload -> torque_nm is None
    res_no_preload = mech_verify.check_fastener_joint(nominal_d_mm=8.0, substrate="steel")
    assert res_no_preload["ok"] is True
    assert res_no_preload["torque_nm"] is None

    # Substrate multipliers: steel (1.0), cast_iron (1.25), aluminum (1.5), plastic (2.0)
    substrate_cases = [
        ("steel", 1.0),
        ("cast_iron", 1.25),
        ("aluminum", 1.5),
        ("plastic", 2.0),
    ]
    d = 8.0
    for substrate, mult in substrate_cases:
        expected_min = mult * d
        ok_res = mech_verify.check_fastener_joint(
            nominal_d_mm=d,
            substrate=substrate,
            engagement_mm=expected_min,
        )
        assert ok_res["ok"] is True, substrate
        assert ok_res["min_engagement_mm"] == expected_min

        fail_res = mech_verify.check_fastener_joint(
            nominal_d_mm=d,
            substrate=substrate,
            engagement_mm=expected_min - 0.5,
        )
        assert fail_res["ok"] is False, substrate
        assert len(fail_res["errors"]) == 1
        assert "thread engagement" in fail_res["errors"][0]

    # Edge distance fail only
    res_edge_fail = mech_verify.check_fastener_joint(
        nominal_d_mm=10.0,
        substrate="steel",
        engagement_mm=12.0,
        edge_dist_mm=14.0,
        pitch_mm=32.0,
    )
    assert res_edge_fail["ok"] is False
    assert len(res_edge_fail["errors"]) == 1
    assert "edge distance" in res_edge_fail["errors"][0]

    # Pitch spacing fail only
    res_pitch_fail = mech_verify.check_fastener_joint(
        nominal_d_mm=10.0,
        substrate="steel",
        engagement_mm=12.0,
        edge_dist_mm=16.0,
        pitch_mm=28.0,
    )
    assert res_pitch_fail["ok"] is False
    assert len(res_pitch_fail["errors"]) == 1
    assert "bolt spacing" in res_pitch_fail["errors"][0]

    # Combined engagement, edge, and pitch failures
    res_all_fail = mech_verify.check_fastener_joint(
        nominal_d_mm=10.0,
        preload_n=5000.0,
        nut_factor_k=0.18,
        substrate="plastic",
        engagement_mm=15.0,
        edge_dist_mm=12.0,
        pitch_mm=25.0,
    )
    assert res_all_fail["ok"] is False
    assert res_all_fail["torque_nm"] == 9.0
    assert len(res_all_fail["errors"]) == 3


def test_check_rectangular_beam_bending_pass_and_fail():
    # Pass: Z = 10 * 20^2 / 6 = 666.6667 mm^3, sigma = 50000 / Z = 75 MPa, SF = 250 / 75 = 3.3333
    res_pass = mech_verify.check_rectangular_beam_bending(
        moment_n_mm=50000.0,
        width_mm=10.0,
        height_mm=20.0,
        yield_mpa=250.0,
        min_sf=2.0,
    )
    assert res_pass["ok"] is True
    assert math.isclose(res_pass["section_modulus_mm3"], 4000.0 / 6.0, rel_tol=1e-4)
    assert math.isclose(res_pass["bending_stress_mpa"], 75.0, rel_tol=1e-4)
    assert math.isclose(res_pass["safety_factor"], 250.0 / 75.0, rel_tol=1e-4)
    assert res_pass["errors"] == []

    # Fail: M = 100000 N*mm -> sigma = 150 MPa -> SF = 1.6667 < 2.0
    res_fail = mech_verify.check_rectangular_beam_bending(
        moment_n_mm=100000.0,
        width_mm=10.0,
        height_mm=20.0,
        yield_mpa=250.0,
        min_sf=2.0,
    )
    assert res_fail["ok"] is False
    assert math.isclose(res_fail["bending_stress_mpa"], 150.0, rel_tol=1e-4)
    assert math.isclose(res_fail["safety_factor"], 250.0 / 150.0, rel_tol=1e-4)
    assert len(res_fail["errors"]) == 1
    assert "safety factor" in res_fail["errors"][0]


def test_check_thin_cylinder_pressure_pass_and_failure_branches():
    # Pass: r/t = 20 >= 10, hoop = 2*100/5 = 40 MPa, axial = 20 MPa, SF = 200/40 = 5.0
    res_pass = mech_verify.check_thin_cylinder_pressure(
        pressure_mpa=2.0,
        inner_radius_mm=100.0,
        wall_mm=5.0,
        yield_mpa=200.0,
        min_sf=2.0,
    )
    assert res_pass["ok"] is True
    assert res_pass["is_thin_walled"] is True
    assert res_pass["hoop_stress_mpa"] == 40.0
    assert res_pass["axial_stress_mpa"] == 20.0
    assert res_pass["safety_factor"] == 5.0
    assert res_pass["errors"] == []

    # Fail r/t < 10 (thick-walled), even though hoop SF passes
    res_thick = mech_verify.check_thin_cylinder_pressure(
        pressure_mpa=2.0,
        inner_radius_mm=40.0,
        wall_mm=5.0,
        yield_mpa=200.0,
        min_sf=2.0,
    )
    assert res_thick["ok"] is False
    assert res_thick["is_thin_walled"] is False
    assert len(res_thick["errors"]) == 1
    assert "r/t" in res_thick["errors"][0]

    # Fail SF < min_sf while r/t >= 10
    res_low_sf = mech_verify.check_thin_cylinder_pressure(
        pressure_mpa=6.0,
        inner_radius_mm=100.0,
        wall_mm=5.0,
        yield_mpa=200.0,
        min_sf=2.0,
    )
    assert res_low_sf["ok"] is False
    assert res_low_sf["is_thin_walled"] is True
    assert res_low_sf["hoop_stress_mpa"] == 120.0
    assert res_low_sf["axial_stress_mpa"] == 60.0
    assert math.isclose(res_low_sf["safety_factor"], 200.0 / 120.0, rel_tol=1e-4)
    assert len(res_low_sf["errors"]) == 1
    assert "safety factor" in res_low_sf["errors"][0]

    # Fail both r/t < 10 and SF < min_sf
    res_both = mech_verify.check_thin_cylinder_pressure(
        pressure_mpa=15.0,
        inner_radius_mm=40.0,
        wall_mm=5.0,
        yield_mpa=200.0,
        min_sf=2.0,
    )
    assert res_both["ok"] is False
    assert res_both["is_thin_walled"] is False
    assert len(res_both["errors"]) == 2


def test_check_fastener_joint_substrate_normalization_and_unknown_error():
    d = 10.0
    normalized_cases = [
        ("  Steel ", 1.0),
        ("cast-iron", 1.25),
        ("Cast Iron", 1.25),
        ("CAST_IRON", 1.25),
        ("aluminium", 1.5),
        ("  Aluminum  ", 1.5),
        ("polymer", 2.0),
        ("  POLYMER ", 2.0),
        ("Plastic", 2.0),
    ]
    for substrate, mult in normalized_cases:
        res = mech_verify.check_fastener_joint(
            nominal_d_mm=d,
            substrate=substrate,
            engagement_mm=mult * d,
        )
        assert res["ok"] is True, substrate
        assert res["min_engagement_mm"] == mult * d

    for bad_substrate in ("titanium", "brass", "wood", ""):
        with pytest.raises(ValueError, match=f"unsupported substrate: {bad_substrate!r}"):
            mech_verify.check_fastener_joint(nominal_d_mm=d, substrate=bad_substrate)


def test_check_rectangular_beam_bending_negative_zero_and_invalid_inputs():
    # Negative (hogging cantilever) moment uses abs(moment_n_mm)
    res_neg_pass = mech_verify.check_rectangular_beam_bending(
        moment_n_mm=-50000.0,
        width_mm=10.0,
        height_mm=20.0,
        yield_mpa=250.0,
        min_sf=2.0,
    )
    assert res_neg_pass["ok"] is True
    assert math.isclose(res_neg_pass["bending_stress_mpa"], 75.0, rel_tol=1e-4)
    assert math.isclose(res_neg_pass["safety_factor"], 250.0 / 75.0, rel_tol=1e-4)
    assert res_neg_pass["errors"] == []

    res_neg_fail = mech_verify.check_rectangular_beam_bending(
        moment_n_mm=-100000.0,
        width_mm=10.0,
        height_mm=20.0,
        yield_mpa=250.0,
        min_sf=2.0,
    )
    assert res_neg_fail["ok"] is False
    assert math.isclose(res_neg_fail["bending_stress_mpa"], 150.0, rel_tol=1e-4)
    assert len(res_neg_fail["errors"]) == 1

    # Zero moment gives 0 stress and inf safety factor (no ZeroDivisionError)
    for zero_m in (0.0, -0.0):
        res_zero = mech_verify.check_rectangular_beam_bending(
            moment_n_mm=zero_m,
            width_mm=10.0,
            height_mm=20.0,
            yield_mpa=250.0,
            min_sf=2.0,
        )
        assert res_zero["ok"] is True
        assert res_zero["bending_stress_mpa"] == 0.0
        assert math.isinf(res_zero["safety_factor"]) and res_zero["safety_factor"] > 0
        assert res_zero["errors"] == []

    # Guard non-positive geometry and yield
    invalid_kwargs = [
        dict(moment_n_mm=1000.0, width_mm=0.0, height_mm=20.0, yield_mpa=250.0),
        dict(moment_n_mm=1000.0, width_mm=-10.0, height_mm=20.0, yield_mpa=250.0),
        dict(moment_n_mm=1000.0, width_mm=10.0, height_mm=0.0, yield_mpa=250.0),
        dict(moment_n_mm=1000.0, width_mm=10.0, height_mm=-20.0, yield_mpa=250.0),
        dict(moment_n_mm=1000.0, width_mm=10.0, height_mm=20.0, yield_mpa=0.0),
        dict(moment_n_mm=1000.0, width_mm=10.0, height_mm=20.0, yield_mpa=-250.0),
    ]
    for kwargs in invalid_kwargs:
        with pytest.raises(ValueError):
            mech_verify.check_rectangular_beam_bending(**kwargs)


def test_check_thin_cylinder_pressure_zero_boundary_and_invalid_inputs():
    # Zero pressure gives 0 stress and inf safety factor on thin-walled cylinder
    res_zero = mech_verify.check_thin_cylinder_pressure(
        pressure_mpa=0.0,
        inner_radius_mm=100.0,
        wall_mm=5.0,
        yield_mpa=200.0,
        min_sf=2.0,
    )
    assert res_zero["ok"] is True
    assert res_zero["is_thin_walled"] is True
    assert res_zero["hoop_stress_mpa"] == 0.0
    assert res_zero["axial_stress_mpa"] == 0.0
    assert math.isinf(res_zero["safety_factor"]) and res_zero["safety_factor"] > 0
    assert res_zero["errors"] == []

    # Zero pressure on thick-walled cylinder fails only r/t check (not SF)
    res_zero_thick = mech_verify.check_thin_cylinder_pressure(
        pressure_mpa=0.0,
        inner_radius_mm=40.0,
        wall_mm=5.0,
        yield_mpa=200.0,
        min_sf=2.0,
    )
    assert res_zero_thick["ok"] is False
    assert res_zero_thick["is_thin_walled"] is False
    assert math.isinf(res_zero_thick["safety_factor"])
    assert len(res_zero_thick["errors"]) == 1
    assert "r/t" in res_zero_thick["errors"][0]

    # Exact decimal r/t = 10.0 pairs where IEEE 754 r/t is slightly below 10.0
    for r, t in ((2.8, 0.28), (1.4, 0.14), (0.7, 0.07)):
        res_boundary = mech_verify.check_thin_cylinder_pressure(
            pressure_mpa=1.0,
            inner_radius_mm=r,
            wall_mm=t,
            yield_mpa=200.0,
            min_sf=2.0,
        )
        assert res_boundary["ok"] is True, (r, t)
        assert res_boundary["is_thin_walled"] is True, (r, t)
        assert res_boundary["errors"] == []

    # Slightly below 10.0 still fails
    res_below = mech_verify.check_thin_cylinder_pressure(
        pressure_mpa=1.0,
        inner_radius_mm=2.79,
        wall_mm=0.28,
        yield_mpa=200.0,
        min_sf=2.0,
    )
    assert res_below["ok"] is False
    assert res_below["is_thin_walled"] is False
    assert len(res_below["errors"]) == 1
    assert "r/t" in res_below["errors"][0]

    # Guard non-positive geometry/yield and negative pressure
    invalid_kwargs = [
        dict(pressure_mpa=2.0, inner_radius_mm=0.0, wall_mm=5.0, yield_mpa=200.0),
        dict(pressure_mpa=2.0, inner_radius_mm=-10.0, wall_mm=5.0, yield_mpa=200.0),
        dict(pressure_mpa=2.0, inner_radius_mm=100.0, wall_mm=0.0, yield_mpa=200.0),
        dict(pressure_mpa=2.0, inner_radius_mm=100.0, wall_mm=-5.0, yield_mpa=200.0),
        dict(pressure_mpa=2.0, inner_radius_mm=100.0, wall_mm=5.0, yield_mpa=0.0),
        dict(pressure_mpa=2.0, inner_radius_mm=100.0, wall_mm=5.0, yield_mpa=-200.0),
        dict(pressure_mpa=-0.5, inner_radius_mm=100.0, wall_mm=5.0, yield_mpa=200.0),
    ]
    for kwargs in invalid_kwargs:
        with pytest.raises(ValueError):
            mech_verify.check_thin_cylinder_pressure(**kwargs)


def test_check_tolerance_stackup_mismatched_lengths_raises():
    mismatched_cases = [
        ([10.0, 8.0], [0.3], [1, -1]),
        ([10.0, 8.0], [0.3, 0.4], [1]),
        ([10.0], [0.3, 0.4], [1, -1]),
        ([10.0, 8.0], [0.3, 0.4, 0.1], [1, -1]),
    ]
    for nominals, tolerances, signs in mismatched_cases:
        with pytest.raises(ValueError):
            mech_verify.check_tolerance_stackup(
                nominals_mm=nominals,
                tolerances_mm=tolerances,
                signs=signs,
            )
