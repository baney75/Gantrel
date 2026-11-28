"""Deterministic Mechanical, Structural & Tolerance Stack-Up Verifier.

Pure Python standard library + math only (zero network, zero subprocess).
Covers:
  - 1D Worst-Case (WC) and Root-Sum-Square (RSS) tolerance stack-up.
  - Fastener tightening torque T = K * F * d and thread engagement depth
    (>= 1.0*d steel, >= 1.5*d aluminum, >= 2.0*d plastic).
  - Bolt hole edge distance (>= 1.5*d) and pitch spacing (>= 3.0*d).
  - Rectangular cantilever / simply-supported beam bending stress & safety factor.
  - Thin-walled cylindrical pressure vessel hoop stress (P*r/t) & axial stress (P*r/(2*t)).
"""
from __future__ import annotations

import math
from typing import Any


def check_tolerance_stackup(
    nominals_mm: list[float],
    tolerances_mm: list[float],
    signs: list[int],
    min_required_gap_mm: float = 0.0,
) -> dict[str, Any]:
    """Compute nominal gap, worst-case (WC) min/max gap, and RSS +/-3sigma gap."""
    nom = sum(s * n for s, n in zip(signs, nominals_mm))
    wc_tol = sum(abs(t) for t in tolerances_mm)
    rss_tol = math.sqrt(sum(t * t for t in tolerances_mm))
    wc_min = nom - wc_tol
    rss_min = nom - rss_tol
    return {
        "nominal_mm": round(nom, 4),
        "wc_tol_mm": round(wc_tol, 4),
        "wc_min_mm": round(wc_min, 4),
        "wc_max_mm": round(nom + wc_tol, 4),
        "rss_tol_mm": round(rss_tol, 4),
        "rss_min_mm": round(rss_min, 4),
        "wc_ok": wc_min + 1e-6 >= min_required_gap_mm,
        "rss_ok": rss_min + 1e-6 >= min_required_gap_mm,
    }


def check_fastener_joint(
    *,
    nominal_d_mm: float,
    preload_n: float | None = None,
    nut_factor_k: float = 0.2,
    substrate: str = "steel",
    engagement_mm: float | None = None,
    edge_dist_mm: float | None = None,
    pitch_mm: float | None = None,
) -> dict[str, Any]:
    """Verify fastener torque (N-m), minimum thread engagement, edge distance, and bolt spacing."""
    errors: list[str] = []
    torque_nm = None
    if preload_n is not None:
        torque_nm = nut_factor_k * preload_n * (nominal_d_mm / 1000.0)
    mult = {"steel": 1.0, "cast_iron": 1.25, "aluminum": 1.5, "aluminium": 1.5, "plastic": 2.0}.get(
        substrate.strip().lower(), 1.5
    )
    min_eng = mult * nominal_d_mm
    if engagement_mm is not None and engagement_mm + 1e-6 < min_eng:
        errors.append(f"thread engagement {engagement_mm:.2f} mm < {min_eng:.2f} mm ({mult}x d in {substrate})")
    min_edge = 1.5 * nominal_d_mm
    if edge_dist_mm is not None and edge_dist_mm + 1e-6 < min_edge:
        errors.append(f"edge distance {edge_dist_mm:.2f} mm < 1.5*d ({min_edge:.2f} mm)")
    min_pitch = 3.0 * nominal_d_mm
    if pitch_mm is not None and pitch_mm + 1e-6 < min_pitch:
        errors.append(f"bolt spacing {pitch_mm:.2f} mm < 3.0*d ({min_pitch:.2f} mm)")
    return {
        "ok": not errors,
        "torque_nm": round(torque_nm, 4) if torque_nm is not None else None,
        "min_engagement_mm": round(min_eng, 4),
        "min_edge_dist_mm": round(min_edge, 4),
        "min_pitch_mm": round(min_pitch, 4),
        "errors": errors,
    }


def check_rectangular_beam_bending(
    *,
    moment_n_mm: float,
    width_mm: float,
    height_mm: float,
    yield_mpa: float,
    min_sf: float = 2.0,
) -> dict[str, Any]:
    """Compute section modulus Z = b*h^2/6, bending stress sigma = M/Z (MPa), and safety factor."""
    z_mm3 = (width_mm * height_mm * height_mm) / 6.0
    sigma_mpa = moment_n_mm / z_mm3
    sf = yield_mpa / sigma_mpa
    errors: list[str] = []
    if sf + 1e-6 < min_sf:
        errors.append(f"safety factor {sf:.2f} < required {min_sf:.2f}")
    return {
        "ok": not errors,
        "section_modulus_mm3": round(z_mm3, 4),
        "bending_stress_mpa": round(sigma_mpa, 4),
        "safety_factor": round(sf, 4),
        "errors": errors,
    }


def check_thin_cylinder_pressure(
    *,
    pressure_mpa: float,
    inner_radius_mm: float,
    wall_mm: float,
    yield_mpa: float,
    min_sf: float = 2.0,
) -> dict[str, Any]:
    """Check thin-walled pressure vessel (r/t >= 10), hoop stress P*r/t, axial stress P*r/(2*t)."""
    ratio = inner_radius_mm / wall_mm
    hoop = (pressure_mpa * inner_radius_mm) / wall_mm
    axial = hoop / 2.0
    sf = yield_mpa / hoop
    errors: list[str] = []
    if ratio < 10.0:
        errors.append(f"r/t = {ratio:.2f} < 10 (thick-walled Lame equations required)")
    if sf + 1e-6 < min_sf:
        errors.append(f"hoop safety factor {sf:.2f} < required {min_sf:.2f}")
    return {
        "ok": not errors,
        "is_thin_walled": ratio >= 10.0,
        "hoop_stress_mpa": round(hoop, 4),
        "axial_stress_mpa": round(axial, 4),
        "safety_factor": round(sf, 4),
        "errors": errors,
    }
