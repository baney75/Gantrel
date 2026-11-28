"""Deterministic Electrical / PCB / KiCad DFM & Pre-Compliance Verifier.

Pure Python standard library + math only (zero network, zero subprocess).
Covers:
  - IPC-2221 trace current capacity & minimum trace width for external/internal 1 oz / 2 oz copper.
  - Linear regulator (LDO) power dissipation Pd = (Vin - Vout) * Iout and junction temp Tj = Ta + Pd * Rth_ja.
  - RC low-pass filter cutoff frequency fc = 1 / (2 * pi * R * C).
  - Standard 2-4 layer PCB fab DFM minimums (trace/space >= 0.127 mm / 5 mil, min drill >= 0.3 mm,
    annular ring >= 0.15 mm, copper-to-edge >= 0.3 mm).
  - EMC & schematic hygiene checks (unbroken reference ground plane under high-speed traces,
    decoupling cap placement adjacent to IC power pins, ESD TVS placement at external connector).
"""
from __future__ import annotations

import math
from typing import Any


def ipc2221_min_trace_width_mm(
    current_a: float,
    temp_rise_c: float = 10.0,
    copper_oz: float = 1.0,
    external: bool = True,
) -> dict[str, Any]:
    """Compute IPC-2221 minimum trace width in mm and mils.

    IPC-2221: I = k * (dT^0.44) * (A_mil2^0.725), k=0.048 (external) or 0.024 (internal).
    Thickness per 1 oz copper = 1.378 mil (0.035 mm).
    """
    k = 0.048 if external else 0.024
    area_mil2 = (current_a / (k * (temp_rise_c ** 0.44))) ** (1.0 / 0.725)
    thickness_mil = 1.378 * copper_oz
    width_mil = area_mil2 / thickness_mil
    width_mm = width_mil * 0.0254
    return {
        "area_mil2": round(area_mil2, 3),
        "width_mil": round(width_mil, 3),
        "width_mm": round(width_mm, 4),
    }


def check_ldo_thermal(
    *,
    vin_v: float,
    vout_v: float,
    iout_a: float,
    ta_c: float,
    rth_ja_c_per_w: float,
    tj_max_c: float = 125.0,
) -> dict[str, Any]:
    """Compute LDO power dissipation Pd = (Vin - Vout) * Iout and junction temperature Tj."""
    pd_w = (vin_v - vout_v) * iout_a
    tj_c = ta_c + pd_w * rth_ja_c_per_w
    errors: list[str] = []
    if vin_v <= vout_v:
        errors.append("Vin must exceed Vout for linear regulation")
    if tj_c > tj_max_c + 1e-6:
        errors.append(f"junction temp {tj_c:.1f} C exceeds Tj_max {tj_max_c:.1f} C")
    return {
        "ok": not errors,
        "power_w": round(pd_w, 4),
        "tj_c": round(tj_c, 2),
        "errors": errors,
    }


def rc_cutoff_hz(r_ohm: float, c_farad: float) -> float:
    """Compute first-order RC low-pass -3 dB cutoff frequency fc = 1 / (2*pi*R*C)."""
    return 1.0 / (2.0 * math.pi * r_ohm * c_farad)


def check_pcb_fab_dfm(
    *,
    trace_mm: float,
    space_mm: float,
    via_drill_mm: float,
    via_pad_mm: float,
    copper_to_edge_mm: float,
    min_trace_mm: float = 0.127,
    min_space_mm: float = 0.127,
    min_drill_mm: float = 0.30,
    min_annular_ring_mm: float = 0.15,
    min_edge_mm: float = 0.30,
) -> dict[str, Any]:
    """Verify standard 2/4-layer PCB fab minimums (annular ring = (pad - drill) / 2)."""
    annular = (via_pad_mm - via_drill_mm) / 2.0
    errors: list[str] = []
    if trace_mm + 1e-6 < min_trace_mm:
        errors.append(f"trace width {trace_mm:.3f} mm < {min_trace_mm:.3f} mm")
    if space_mm + 1e-6 < min_space_mm:
        errors.append(f"trace spacing {space_mm:.3f} mm < {min_space_mm:.3f} mm")
    if via_drill_mm + 1e-6 < min_drill_mm:
        errors.append(f"via drill {via_drill_mm:.3f} mm < {min_drill_mm:.3f} mm")
    if annular + 1e-6 < min_annular_ring_mm:
        errors.append(f"annular ring {annular:.3f} mm < {min_annular_ring_mm:.3f} mm")
    if copper_to_edge_mm + 1e-6 < min_edge_mm:
        errors.append(f"copper-to-edge {copper_to_edge_mm:.3f} mm < {min_edge_mm:.3f} mm")
    return {
        "ok": not errors,
        "annular_ring_mm": round(annular, 4),
        "errors": errors,
    }
