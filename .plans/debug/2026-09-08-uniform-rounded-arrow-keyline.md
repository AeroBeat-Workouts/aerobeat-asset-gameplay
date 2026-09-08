# Uniform rounded directional-arrow keyline diagnosis

## Exact Observed Failure

Derrick's physical review of securely served web raw `0.0.43` reports that the directional arrow's inner charcoal keyline is visibly uneven at the concave shoulders and near the tips. The immutable gameplay asset embedded there is raw `0.0.8`.

Independent geometric measurement of `release/raw/0.0.8/directional-arrow/rounded-outline-v1.glb` reproduces the variation. Minimum/maximum nearest-boundary widths are:

| band | nominal | minimum | maximum | spread |
|---|---:|---:|---:|---:|
| outer charcoal | 0.014 | 0.013931742 | 0.025597973 | 0.011666231 |
| white | 0.052 | 0.051999920 | 0.078095418 | 0.026095499 |
| inner charcoal | 0.020 | 0.019999996 | 0.032463000 | 0.012463004 |

The maxima occur around the shoulder/neck transition samples (for example white at approximately `(+/-0.114858, 0.115142)` and inner charcoal near `(+/-0.193073, 0.153463)`). This is direct geometric evidence, independent of lighting or antialiasing. Immutable raw/review `0.0.1` through `0.0.8` remain untouched.

## Expected Behavior

The arrow must preserve its DDR-style proportions, `0.78 x 0.78 x 0.18` dimensions, two-sided opaque connected manifold, and face hierarchy `charcoal -> white -> charcoal -> note_fill`, while every exterior/interior boundary is a genuine signed offset of one rounded contour family. Nominal level differences must be `0.014 / 0.052 / 0.020`; rotations, colors, scales, and DPRs must not create a locally swollen shoulder/tip keyline. Colored fill remains at least 35% and total interior after the white stroke at least 48%. Circle, guard, bomb, wall, track, athlete marker, immutable releases, and immutable reviews must remain byte-identical.

## Execution Path

1. `build_rounded_cue("directional-arrow")` asks `solve_arrow_loops()` for bevel and material boundaries.
2. `solve_arrow_loops()` starts from one seven-anchor outer polygon.
3. `filleted_loops()` independently insets that sharp anchor polygon at every level.
4. It computes every new radius as `max(semantic_floor, outer_radius - offset)` without using the corner's signed turn.
5. `sample_filleted_polygon()` therefore re-rounds each level with a different clamped curve rather than evaluating signed-distance levels of one rounded source contour.
6. `cue_shell()` connects corresponding samples and exports the resulting charcoal/white/charcoal/fill partitions.
7. `validate_rounded_candidate.py` checks only a lower bound on sparse inner-point-to-outer-segment distance. Widening is explicitly accepted and there is no raster-width oracle, so the locally swollen shoulders/tips pass.

## Most Likely Root Cause

The current construction is not a signed offset of a rounded contour. It offsets the seven sharp anchor lines and then independently invents/clamps corner radii. The same `radius - offset` expression is used at convex and concave turns even though signed curvature requires opposite radius evolution. Once offsets exceed the small outer radii, semantic floors deliberately widen joins. That was appropriate for the earlier non-narrowing/readability repair, but it cannot guarantee uniform visual keylines.

Evidence is both source-level and measured: lines 213-223 of `tools/generate.py` apply independent clamped re-rounding, while the immutable GLB shows up to `0.026095499` world-unit white-band spread and `0.012463004` inner-charcoal spread concentrated at the reported features.

## Alternative Hypotheses

1. **Lighting/antialiasing alone** — unlikely. The geometry itself contains the same localized widening before rasterization.
2. **Renderer rotation or Y flip** — contradicted by the same object-space widths and the renderer's authored rotation-only direction mapping.
3. **Circle/guard material hierarchy** — unrelated. The report names the arrow, and the circle is analytic/concentric; changing other assets would add risk without evidence.
4. **Insufficient colored fill** — contradicted by the accepted 35.588% current fill measurement. Readability area is separate from width uniformity.

## Why Previous Fixes Failed

The prior morphological repair correctly eliminated narrowing, restored shaft/tip readability, and reconciled the 35%/48% area contracts. It intentionally allowed joins to widen and validated minima only. Consequently it fixed missing/narrow bands but preserved exactly the width inflation now visible in physical pixels. The stalled replacement child made no repository, asset, process, or commit effect, so there is no later attempted implementation to preserve or retry.

## Unknowns

The exact raster tolerance that remains stable at the smallest supported projected size must be established by the new deterministic raster oracle. Geometry can require tight signed-level agreement; raster checks must allow only quantization-bounded variation across colors, rotations, scales, and DPRs.

## Minimal Reproduction

Load the immutable `0.0.8` arrow GLB, reconstruct the four planar material boundaries, and measure nearest polyline distance at every boundary vertex/midpoint. The table above results. A red-before width-spread oracle with bounds materially below `0.0116 / 0.0261 / 0.0124` rejects the current arrow.

## Proposed Verification

1. Add a red-before fixture proving immutable `0.0.8` fails uniform-width spread at concave and convex feature windows.
2. Generate only disposable candidates from a fill-first rounded contour whose outward signed levels are exactly `0 / 0.020 / 0.072 / 0.086`; derive bevel levels from that same family.
3. Require geometric level widths at straight, concave, convex, tip, and rotated samples.
4. Render deterministic orthographic masks over multiple note colors, directions, scales, and DPR-equivalent resolutions; measure run widths around the same feature classes.
5. Require two disposable builds to reproduce, source and GLB Blender smoke to pass, and manifold/material/pixel contracts to pass.
6. Hash every immutable raw/review tree before and after and byte-compare every non-arrow staged source/manifest.

## Recommended Fix

Define the rounded fill contour first with exact `0.178` shaft width and a `0.045` tip radius. Construct inner-charcoal, outer-white, silhouette, and bevel contours as analytic outward signed offsets of that same rounded seven-anchor family. Choose a positive fill concave radius large enough that the outermost signed offset remains valid, avoiding medial-axis collapse and all semantic radius clamps. Solve only the fill head/tip anchors needed to retain the exact `+/-0.39` outer bounds. Keep the existing 69 samples and shell topology, so the `1,928`-triangle two-sided manifold/material contract remains stable.

## Debugging Record

```text
Problem: Screenshot-visible uneven directional-arrow inner charcoal keyline.
Observed symptom: Immutable 0.0.8 geometric band spreads are 0.011666 outer charcoal, 0.026095 white, and 0.012463 inner charcoal, concentrated at shoulders/tips.
Root cause: Each inset sharp-anchor polygon is independently re-rounded with unsigned radius subtraction and semantic floors; boundaries are not signed-distance levels of one rounded contour.
Evidence: tools/generate.py filleted_loops() construction plus measured immutable GLB widths and feature coordinates.
Failed approaches: Prior non-narrowing morphology intentionally allowed widening; stalled child made zero effects.
Corrective action: Fill-first analytic rounded contour with one outward signed-offset family at levels 0/.020/.072/.086 and matching bevel levels.
Verification test: Red-before immutable oracle, green-after geometric/raster feature matrix, reproducibility, Blender smoke, manifold/material checks, and immutable-tree hashes.
Related files/components: tools/generate.py, new uniform-arrow oracle, staged arrow .blend/manifest, this report.
Remaining uncertainty: Quantization-only raster tolerance, to be fixed by deterministic multi-resolution evidence.
```

## Repair result

The fill-first construction landed exactly as proposed. The fill anchors use shaft half-width `0.089`, bottom `-0.304`, neck Y `0.020`, solved head X `0.3370345104`, and solved tip Y `0.3191711694`. Fill radii are `0.045` tail, `0.095` concave neck, `0.020` convex head shoulder, and `0.045` tip. Outward signed levels `0 / 0.020 / 0.072 / 0.086` generate fill, inner-white boundary, outer-white boundary, and silhouette; all convex radii increase and concave radii decrease by the exact signed level. The outermost concave radius remains positive at `0.009`, so no clamp, collapse, or invented join occurs. Solved candidate bounds remain exact `[-0.39,-0.39,-0.09]..[0.39,0.39,0.09]`.

The red-before/green-after oracle measures:

| band | immutable 0.0.8 min..max / spread | staged candidate min..max / spread |
|---|---|---|
| outer charcoal | `0.013931742..0.025597973 / 0.011666231` | `0.013880243..0.014000078 / 0.000119835` |
| white | `0.051999920..0.078095418 / 0.026095499` | `0.051555088..0.052000000 / 0.000444912` |
| inner charcoal | `0.019999996..0.034352750 / 0.014352754` | `0.019828869..0.020000097 / 0.000171228` |

The small candidate undershoot is the bounded chord error of the retained 69-sample tessellation; every band remains within `0.00050` of its analytic signed level. Spread is reduced by `98.97%` outer-charcoal, `98.30%` white, and `98.81%` inner-charcoal. Colored fill is `0.4541180171 >= 0.35`; total interior is `0.5693474204 >= 0.48`; straight fill shaft remains exact `0.178`; fill tip remains `0.045`.

`tools/test_uniform_arrow.py` proves immutable red-before rejection and candidate green-after across straight shaft, concave shoulder, convex shoulder, and tip windows; eight rotations, three fill colors, three scales, and DPR `1/2/3`; `2,592` deterministic four-sample antialiased raster checks; and three targeted shoulder-bulge adversaries. The existing 14 rounded adversaries also pass.

Candidate topology remains 69 samples / 1,928 triangles, Euler `2`, one connected closed two-manifold, positive signed volume `0.0633066764`, opposite edge winding, and minimum explicit-normal dot `0.999999999996`. All three rounded staged sources and candidate GLBs pass Blender `4.0.2` smoke; circle and guard retain their existing `1,788 / 1,172` triangles and geometry/material validation. Two disposable generations reproduce all 17 runtime candidate files byte-for-byte; each also produces 73 review evidence files. Blender `.blend` and rendered PNG container bytes remain outside determinism claims, consistent with the established repository contract.

Staged arrow source SHA-256 is `8d3dd7fbc940de442b57bbadd5f471ed95c85195fcbce04b0664bd59386127c2` (`561,492` bytes); staged manifest SHA-256 is `98cb5aab2719892e3a018a57869fce364961ff0d66b40d01e0f4e05447ed8c7a`; isolated candidate GLB SHA-256 is `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4` (`152,916` bytes). Only the staged arrow `.blend`/manifest change among source/manifest asset identities. Six non-arrow candidate GLBs are byte-identical to immutable `0.0.8`; circle, guard, bomb, wall, track, and athlete-marker staged assets remain unchanged.

Immutable raw/review `0.0.1` through `0.0.8` pass a before/after 16-tree path/size/SHA inventory comparison. Canonical `0.0.8` remains exact: raw Git tree `e26ec4e8278860c60568bd2a89983cd09555ee75`, 17 files / 429,026 bytes, inventory `ac30d6b70cbae96115a7c97f5ad02b3da21fde7fb77f69083f1090e268bab5ac`, proof `ba8a52cf747ec5ab58dcd024c90f813a5c477541892f71da698ead6a65ca4758`; review Git tree `df080ea57c99bb50697f14e891edad7f53dbda2a`, 73 files / 77,758,435 bytes. No canonical build driver ran and no permanent successor path was created.
