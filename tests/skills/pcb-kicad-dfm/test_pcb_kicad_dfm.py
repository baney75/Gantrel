"""Deterministic contract and PCB/KiCad DFM verifier tests for skills/runtime/pcb-kicad-dfm."""

from __future__ import annotations

import ast
import math
import re
import sys
from pathlib import Path

from gantrel_printer.plan import pcb_verify

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "runtime" / "pcb-kicad-dfm" / "SKILL.md"
VERIFIER = ROOT / "src" / "gantrel_printer" / "plan" / "pcb_verify.py"

FORBIDDEN_IMPORTS = {"socket", "urllib", "http", "requests", "adapters", "subprocess"}
DROPPED_REPOS = ("MP-AI-20", "DDC_Skills", "ShopPrentice")


def test_frontmatter_sections_style_and_sources():
    text = SKILL.read_text(encoding="utf-8")
    assert re.match(r"^---\nname: pcb-kicad-dfm\ndescription: .+\n---\n", text)
    for section in ("## Goal", "## Inputs", "## Steps", "## Rules and checks", "## Sources"):
        assert section in text, f"missing {section}"
    assert chr(0x2014) not in text and chr(0x2013) not in text
    assert not re.search(r"[\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069]", text)
    for dropped in DROPPED_REPOS:
        assert dropped not in text, f"dropped repo citation found: {dropped}"


def test_pcb_verify_pure_stdlib_imports():
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


def test_ipc2221_min_trace_width_external_vs_internal_ratio():
    ext = pcb_verify.ipc2221_min_trace_width_mm(current_a=2.0, temp_rise_c=10.0, copper_oz=1.0, external=True)
    internal = pcb_verify.ipc2221_min_trace_width_mm(current_a=2.0, temp_rise_c=10.0, copper_oz=1.0, external=False)
    expected_ratio = 2.0 ** (1.0 / 0.725)  # ~2.6015
    ratio = internal["width_mm"] / ext["width_mm"]
    assert math.isclose(ratio, expected_ratio, rel_tol=1e-2)
    assert math.isclose(ratio, 2.6, rel_tol=0.02)
    assert ext["width_mm"] > 0 and ext["width_mil"] > 0 and ext["area_mil2"] > 0

    # Doubling copper weight halves required trace width for the same current and temp rise
    ext_2oz = pcb_verify.ipc2221_min_trace_width_mm(current_a=2.0, temp_rise_c=10.0, copper_oz=2.0, external=True)
    assert math.isclose(ext_2oz["width_mm"] * 2.0, ext["width_mm"], rel_tol=1e-3)


def test_check_ldo_thermal_pass_and_failure_branches():
    # Pass: Pd = (5.0 - 3.3) * 0.5 = 0.85 W, Tj = 25 + 0.85 * 50 = 67.5 C <= 125 C
    res_pass = pcb_verify.check_ldo_thermal(
        vin_v=5.0,
        vout_v=3.3,
        iout_a=0.5,
        ta_c=25.0,
        rth_ja_c_per_w=50.0,
        tj_max_c=125.0,
    )
    assert res_pass["ok"] is True
    assert res_pass["power_w"] == 0.85
    assert res_pass["tj_c"] == 67.5
    assert res_pass["errors"] == []

    # Fail: Vin <= Vout (equal and below)
    for bad_vin in (3.3, 3.0):
        res_vin = pcb_verify.check_ldo_thermal(
            vin_v=bad_vin,
            vout_v=3.3,
            iout_a=0.2,
            ta_c=25.0,
            rth_ja_c_per_w=50.0,
        )
        assert res_vin["ok"] is False
        assert any("Vin must exceed Vout" in err for err in res_vin["errors"])

    # Fail: Tj > Tj_max (Pd = (12.0 - 3.3) * 0.5 = 4.35 W, Tj = 25 + 4.35 * 40 = 199.0 C)
    res_hot = pcb_verify.check_ldo_thermal(
        vin_v=12.0,
        vout_v=3.3,
        iout_a=0.5,
        ta_c=25.0,
        rth_ja_c_per_w=40.0,
        tj_max_c=125.0,
    )
    assert res_hot["ok"] is False
    assert res_hot["power_w"] == 4.35
    assert res_hot["tj_c"] == 199.0
    assert len(res_hot["errors"]) == 1
    assert "junction temp" in res_hot["errors"][0]


def test_rc_cutoff_hz():
    fc_1k_100n = pcb_verify.rc_cutoff_hz(1000.0, 100e-9)
    fc_10k_10n = pcb_verify.rc_cutoff_hz(10000.0, 10e-9)
    expected = 1.0 / (2.0 * math.pi * 1e-4)
    assert math.isclose(fc_1k_100n, expected, rel_tol=1e-9)
    assert math.isclose(fc_10k_10n, expected, rel_tol=1e-9)
    assert math.isclose(fc_1k_100n, 1591.5494, rel_tol=1e-4)


def test_check_pcb_fab_dfm_pass_and_every_threshold_fail():
    baseline = dict(
        trace_mm=0.15,
        space_mm=0.15,
        via_drill_mm=0.30,
        via_pad_mm=0.60,
        copper_to_edge_mm=0.35,
    )
    res_pass = pcb_verify.check_pcb_fab_dfm(**baseline)
    assert res_pass["ok"] is True
    assert res_pass["annular_ring_mm"] == 0.15
    assert res_pass["errors"] == []

    # 1. trace_mm below minimum (0.127 mm)
    res_trace = pcb_verify.check_pcb_fab_dfm(**{**baseline, "trace_mm": 0.10})
    assert res_trace["ok"] is False
    assert len(res_trace["errors"]) == 1
    assert "trace width" in res_trace["errors"][0]

    # 2. space_mm below minimum (0.127 mm)
    res_space = pcb_verify.check_pcb_fab_dfm(**{**baseline, "space_mm": 0.10})
    assert res_space["ok"] is False
    assert len(res_space["errors"]) == 1
    assert "trace spacing" in res_space["errors"][0]

    # 3. via_drill_mm below minimum (0.30 mm), while annular ring passes ((0.60 - 0.25)/2 = 0.175)
    res_drill = pcb_verify.check_pcb_fab_dfm(**{**baseline, "via_drill_mm": 0.25})
    assert res_drill["ok"] is False
    assert len(res_drill["errors"]) == 1
    assert "via drill" in res_drill["errors"][0]

    # 4. annular ring below minimum (0.15 mm): (0.50 - 0.30)/2 = 0.10 mm
    res_annular = pcb_verify.check_pcb_fab_dfm(**{**baseline, "via_pad_mm": 0.50})
    assert res_annular["ok"] is False
    assert res_annular["annular_ring_mm"] == 0.10
    assert len(res_annular["errors"]) == 1
    assert "annular ring" in res_annular["errors"][0]

    # 5. copper_to_edge_mm below minimum (0.30 mm)
    res_edge = pcb_verify.check_pcb_fab_dfm(**{**baseline, "copper_to_edge_mm": 0.20})
    assert res_edge["ok"] is False
    assert len(res_edge["errors"]) == 1
    assert "copper-to-edge" in res_edge["errors"][0]

    # All 5 thresholds failing simultaneously
    res_all = pcb_verify.check_pcb_fab_dfm(
        trace_mm=0.08,
        space_mm=0.08,
        via_drill_mm=0.20,
        via_pad_mm=0.40,
        copper_to_edge_mm=0.15,
    )
    assert res_all["ok"] is False
    assert res_all["annular_ring_mm"] == 0.10
    assert len(res_all["errors"]) == 5
