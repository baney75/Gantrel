---
name: parametric-cad-dfm
description: Author watertight, print-ready parametric OpenSCAD CAD geometry with verified ISO 286 and FDM-SLA clearances, ISO 273 screw holes, CNC Kitchen heat-set insert bosses, slotted datum accommodation, FDM press-fit primitives, 45-degree overhangs, teardrop horizontal holes with roof offset, support-free 2-step counterbores, Manifold boolean hygiene, and architectural scale wall floors. Use when designing off-catalog parts, mechanical housings, brackets, mating assemblies, or repairing non-manifold CAD geometry.
---

# parametric-cad-dfm

## Goal

Produce concise, deterministic, watertight 2-manifold OpenSCAD code that compiles cleanly with `openscad --backend=manifold`, seats flat on `z = 0`, matches every requested dimension and fit, and keeps unsupported overhangs past 45 degrees at or under 5% of surface area.

## Inputs

- Part dimensions in millimeters (`1 m = 1000 mm`, `1 in = 25.4 mm`).
- Process (default FDM, 0.4 mm nozzle) and requested fit, screw, heat-set insert, load, or architectural scale `1:S`.

## Steps

1. Output ONLY one closed `openscad` code fence (under 25 lines). Write **ZERO comments** (NO `//`, NO `#`, NO prose outside the fence) so output never truncates.
2. Start with `$fn = 64; eps = 0.1;` then define ONLY the numeric variables needed for this part (untyped: `sx = 40;`; NEVER `real`, `float`, `int`, `let`, `const`).
3. Follow strict OpenSCAD syntax:
   - NEVER assign geometry to variables (WRONG: `plate = cube(...);` or `plate = { ... };`).
   - NEVER emit a stray `cube(...)` or `cylinder(...)` outside the main `difference()` or `union()`.
   - Use `cube([sx, sy, sz]);` (NEVER `box(...)`) and `cylinder(d=D, h=H);`.
   - Center a box at `(0, 0)` on `z = 0`: `translate([-sx/2, -sy/2, 0]) cube([sx, sy, sz]);`.
4. Apply Manifold 2-manifold rules:
   - Through-hole cutters protrude past BOTH faces: `translate([x, y, -eps]) cylinder(d=hole_d, h=sz + 2*eps);`.
   - Blind holes / heat-set bosses use ONE `difference()`: outer height MUST equal `floor_h + depth` (NEVER just `depth` or `floor_h`), and bore starts at `z = floor_h` with height `depth + eps`.
   - Fused `union()` stacked parts (base height `base_h` + upper part height `top_h` -> total height `base_h + top_h`): overlap upper part into base by `eps`: `translate([-tx/2, -ty/2, base_h - eps]) cube([tx, ty, top_h + eps]);`.
   - To fix an inverted `polyhedron()`, keep `points` identical and strictly reverse EVERY face list right-to-left (`[a, b, c, d]` -> `[d, c, b, a]`; `[a, b, c]` -> `[c, b, a]`) so `signed_volume > 0`.

## Rules and checks

### FDM and SLA radial clearances (`hole_d = pin_d + 2 * radial`)

| Fit class | ISO 286 intent | FDM radial / side | FDM `hole_d` | SLA (Tough/Durable) radial |
| --- | --- | --- | --- | --- |
| Press fit | H7/p6 | `0.05 to 0.15 mm` (`0.125`) | `pin_d + 0.25` | `-0.0375 to +0.0125 mm` |
| Snug / snap fit | H7/h6, H7/k6 | `0.15 to 0.25 mm` (`0.20`) | `pin_d + 0.40` | `0.00 to 0.05 mm` (snap `0.15`) |
| Sliding / slip fit | H7/g6, H8/f7 | `0.20 to 0.30 mm` (`0.25`) | `pin_d + 0.50` | `0.0625 to 0.20 mm` |
| Free-rotating hinge | H9/d9 | `0.40 to 0.50 mm` (`0.45`) | `pin_d + 0.90` | `0.20 to 0.30 mm` |

### ISO 273 metric screw clearance holes (medium, FDM +0.2 mm)

| Screw | M2 | M2.5 | M3 | M4 | M5 | M6 |
| --- | --- | --- | --- | --- | --- | --- |
| ISO 273 medium ID | 2.4 | 2.9 | 3.4 | 4.5 | 5.5 | 6.6 |
| FDM CAD `hole_d` (mm) | `2.6` | `3.1` | `3.6` | `4.7` | `5.7` | `6.8` |

### Heat-set brass insert bosses (CNC Kitchen / Ruthex, straight blind hole, no top chamfer)

Use ONE `difference()`: outer `cylinder(d=hole_d + 2*wall, h=floor_h + depth);` minus `translate([0, 0, floor_h]) cylinder(d=hole_d, h=depth + eps);`.

| Insert | Length `L` | Finished ID | FDM `hole_d` | Blind `depth` (`L+1`) | Min radial `wall` |
| --- | --- | --- | --- | --- | --- |
| M2 | 3.0 mm | 3.2 mm | `3.3` | `4.0` | `1.5` (min 1.3) |
| M2.5 | 4.0 mm | 4.0 mm | `4.1` | `5.0` | `1.8` (min 1.6) |
| M3 | 5.7 mm | 4.0 mm | `4.1` | `6.7` | `1.8` (min 1.6) |
| M4 | 8.1 mm | 5.6 mm | `5.7` | `9.1` | `2.2` (min 2.1) |
| M5 | 9.5 mm | 6.4 mm | `6.5` | `10.5` | `2.8` (min 2.6) |
| M6 | 12.7 mm | 8.0 mm | `8.1` | `13.7` | `3.5` (min 3.3) |

### Verified OpenSCAD patterns (substitute requested numbers, ZERO comments)

1. **Plate with 4 holes on `px x py` square:**
```openscad
$fn = 64; eps = 0.1;
sx = 40; sy = 40; sz = 4; px = 30; py = 30; hole_d = 3.6;
difference() {
    translate([-sx/2, -sy/2, 0]) cube([sx, sy, sz]);
    for (x = [-px/2, px/2], y = [-py/2, py/2])
        translate([x, y, -eps]) cylinder(d=hole_d, h=sz + 2*eps);
}
```
2. **Blind heat-set boss (or blind bearing seat: replace outer `cylinder` with centered `cube`):**
```openscad
$fn = 64; eps = 0.1;
hole_d = 4.1; depth = 6.7; wall = 1.8; floor_h = 2.0;
difference() {
    cylinder(d=hole_d + 2*wall, h=floor_h + depth);
    translate([0, 0, floor_h]) cylinder(d=hole_d, h=depth + eps);
}
```
3. **2-part mating block + peg side-by-side on `z = 0` (zero clash):**
```openscad
$fn = 64; eps = 0.1;
pin_d = 10.0; hole_d = pin_d + 0.50;
translate([-20, 0, 0]) difference() {
    translate([-14, -14, 0]) cube([28, 28, 8]);
    translate([0, 0, -eps]) cylinder(d=hole_d, h=8 + 2*eps);
}
translate([20, 0, 0]) cylinder(d=pin_d, h=14);
```
4. **45-degree bottom chamfer (for hollow box, wrap `hull()` inside `difference()` and cut cavity at `z = floor_h`):**
```openscad
eps = 0.1; sx = 50; sy = 30; sz = 15; c = 1.5;
hull() {
    translate([-(sx-2*c)/2, -(sy-2*c)/2, 0]) cube([sx-2*c, sy-2*c, 0.01]);
    translate([-sx/2, -sy/2, c]) cube([sx, sy, sz - c]);
}
```
5. **45-degree teardrop horizontal hole (Y-axis starts at `y = sy/2 + eps` with `rotate([90,0,0])`; X-axis starts at `x = -sx/2 - eps` with `rotate([90,0,90])`; 90-deg roof point for ~4 mm bores, +0.4 mm roof offset above circle for ~10 mm bores):**
```openscad
$fn = 64; eps = 0.1; sx = 30; sy = 20; sz = 30; r = 4.1; zc = 15;
module teardrop_2d(rad) {
    union() { circle(r=rad); polygon([[-rad*cos(45), rad*sin(45)], [rad*cos(45), rad*sin(45)], [0, rad/sin(45)]]); }
}
difference() {
    translate([-sx/2, -sy/2, 0]) cube([sx, sy, sz]);
    translate([0, sy/2 + eps, zc]) rotate([90, 0, 0]) linear_extrude(height=sy + 2*eps) teardrop_2d(r);
}
```
6. **Architectural scale wall floor (`1:S`):** `t_model = max(t_real / S, 1.2)` mm FDM (use `1.6` mm); `max(t_real / S, 0.5)` mm SLA. Hollow shell: `difference() { translate([-sx/2,-sy/2,0]) cube([sx,sy,sz]); translate([-(sx/2-w),-(sy/2-w),floor_h]) cube([sx-2*w,sy-2*w,sz]); }`.
7. **L-bracket with gussets:** orient on its side (`width` along Z) inside `difference() { union() { cube([L,t,w]); cube([t,L,w]); for(z0=[0,w-gt]) translate([t-eps,t-eps,z0]) linear_extrude(height=gt) polygon([[0,0],[g,0],[0,g]]); } ... }`.
8. **Accommodation, press-fits & support-free counterbores:** use 1 round datum hole + radial outward slots (`travel = slot_length - fastener_d`); choose crush ribs (one-time), hex holes (`$fn=6`, reduced contact), or elastic grip fins (reusable) for press fits; cut inverted counterbores with a 2-step bridging recess (1 layer `0.2 mm` on long sides + 2 layers `0.4 mm` orthogonal) or use OrcaSlicer partially-bridged / sacrificial-layer; split angled mounts into modular flat-print braces and print a small interface fit-test coupon (<30 min) before multi-hour builds.

### Deterministic verification gate (Blocker = NO-SHIP)

Every output must pass: Manifold compile exit 0, 0 boundary edges, 0 multi-manifold edges, 0 interior faces, `signed_volume > 0`, exact body count, `min_z == 0`, `overhang_fraction <= 5%`, zero multi-body clash, and valid bounds at min/default/max parameters.

## Sources

- ISO 286 preferred limits and fits; ISO 273 metric fastener clearance holes.
- `@amypretzel` (2026-02-19): manufacturing accommodation, clearance, and design for adjustment (`x.com/amypretzel/status/2024530666679865810`).
- Travis Foss, *10 Smart 3D Printing Tips: Tolerances, Holes, and Slicer Tricks*, DigiKey Maker.io (2026-05-04), citing Rahix (`rahix.de/blog/design-for-3d-printing/`) and Slant 3D (`youtube.com/@Slant3D`).
- Boston University EPIC / Formlabs White Paper: *Engineering Fit: Optimizing Design for Functional 3D Printed Assemblies* (`bu.edu/epic/files/2025/05/SLA_Tolerances.pdf`).
- Hubs / Protolabs Network FDM Design Guide (`hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/`) and CNC Kitchen / Ruthex Heat-Set Threaded Insert Guidelines (`cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts`).
- Manifold Library (`github.com/elalish/manifold/wiki/Manifold-Library`) and OpenSCAD User Manual (`en.wikibooks.org/wiki/OpenSCAD_User_Manual/The_OpenSCAD_Language`).
- CADSmith (`arXiv:2603.26512`), MUSE (`arXiv:2605.28579`), and CIT-CAD (`arXiv:2609.07434`).
- Clean-room modeling and verification patterns informed by `seehiong/blender-mcp-bridge` (MIT) and `arjun988/blender-skills` (MIT).
