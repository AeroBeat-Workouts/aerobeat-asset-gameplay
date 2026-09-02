# Initial gameplay asset visual QA failure

## Exact Observed Failure

Independent QA of public commit `673fc75dec250392b79565dfd186a26261513df4` failed visual conformance while all mechanical validation passed.

Observed in actual Blender renders:

- `review/0.0.1/directional-arrow--outline-v1.png`, `guard--shield-v1.png`, and `any-note--circle-v1.png` show predominantly black perimeter silhouettes. White is visible mainly as a detached/top-side highlight rather than the required continuous white perimeter around the front-facing silhouette.
- `review/0.0.1/neutral-board.png` is unlabeled and crops the wall, directional arrow, and track, preventing complete neutral comparison.
- `review/0.0.1/gameplay-context.png` does not keep the arrow or the three athlete-marker spheres inside the camera frame and therefore does not evidence all intended states.
- The individual wall render crops the wall; the track render is too narrow/small for useful material/depth review.

Direct parent inspection confirmed the outline and framing symptoms. `python3 tools/validate.py --root . --release 0.0.1` passed all seven mechanical asset checks.

## Expected Behavior

The approved specification and Task 1 boards require:

- a continuous visible white perimeter/rim around the intended directional-arrow, any-note, and shield silhouettes from the gameplay-facing view;
- complete, readable, unambiguous review framing for every asset;
- a neutral board showing all seven roles without clipping;
- a gameplay-context view visibly containing the directional arrow, circle, two identical shield instances, bomb, wall, track, and three athlete spheres.

## Execution Path

1. `tools/generate.py::build_geometry` creates arrow/circle/shield as three nested extruded solids (`white`, `charcoal`, role color) separated by very small Z offsets.
2. `make_asset` flattens each role into one mesh with material indices.
3. `review` reconstructs those meshes, positions them using fixed world coordinates, and selects fixed perspective cameras.
4. The nested depth/scale construction and oblique review camera expose the white layer mainly as a side/top highlight while the charcoal layer dominates the perimeter.
5. The neutral/context/individual fixed placements derive from raw world dimensions without calculating camera-frame containment or composing labels, so large wall/track geometry and edge-positioned objects leave the frame.
6. Mechanical validation verifies hashes, GLB structure, names, AABBs, budgets, imports, and reproducibility but has no visual silhouette/framing assertion.

## Most Likely Root Cause

The outline was implemented as nested complete solids with tiny depth offsets rather than an explicit front-facing white ring/perimeter geometry. Perspective and occlusion therefore make the white layer read as a raised side strip instead of a continuous front rim. This is directly supported by `build_geometry` lines 130–141: each role layers full extrusions at scales `1`, `0.91`, and `0.80/0.79`, with the darker and colored solids slightly closer to the negative-Z review camera.

Review framing has a separate deterministic-layout root cause: `review` uses hard-coded placements/cameras and `distance=max(dimensions)*2.2+1.2`. It does not fit object bounds into the frame, reserve a board grid, or verify final projected extents.

## Alternative Hypotheses

1. **Lighting alone makes white appear dark** — less likely. White is clearly visible on only selected side/top surfaces while the perimeter remains black, matching geometry/occlusion ordering rather than global exposure.
2. **The camera views the wrong asset side** — possible contributor. Cameras are placed on negative Z, consistent with the intended visible face `-Z`; reversing the camera might hide rather than repair the explicit front contract.
3. **Color management suppresses white** — contradicted by bright white highlights elsewhere in the same renders.
4. **Image corruption or scaling** — contradicted by native `1600 × 900` inspection and reproduced review hashes.

## Why Previous Fixes Failed

No prior 3D visual fix was attempted. The initial implementation optimized for exact dimensions, low triangle counts, deterministic GLB bytes, and manifest/release correctness. Mechanical validators passed, but they treated the presence of `mat/white` as proof of a readable outline and did not inspect projected coverage. The approved 2D boards were used as semantic input but not as a visual acceptance comparison against the final Blender renders.

## Unknowns

- Whether a front coplanar/narrow ring, shallow rim extrusion, or bevel-highlight combination will best preserve the white perimeter in both Blender, PlayCanvas, and Godot. A prototype render from the exact gameplay-facing camera will distinguish these options.
- Whether labels should be authored as Blender text or composed after rendering. Since fonts are forbidden from asset payloads, the safest review-only approach may be locally generated annotations outside GLB/release content.

## Minimal Reproduction

1. Open `review/0.0.1/directional-arrow--outline-v1.png` or `guard--shield-v1.png` at native resolution.
2. Observe the black perimeter with white restricted to an upper/side strip.
3. Open `neutral-board.png`; observe the cropped left wall/right arrow/track and lack of role labels.
4. Open `gameplay-context.png`; observe that the arrow and marker spheres are outside the frame.

Mechanical validation still returns `VALID 7 assets`, demonstrating that current validators do not cover the visual failure.

## Proposed Verification

Before accepting a repair:

- render front and three-quarter views with a continuous white ring visible around every arrow/circle/shield front silhouette;
- compute or manually inspect projected bounds so each individual object and every neutral-board cell has margin on all sides;
- ensure the context render visibly contains exactly two identical shield instances and all three marker spheres plus every other applicable role;
- compare native renders to the approved Task 1 boards;
- rerun GLB/bounds/budget/import/reproducibility checks;
- preserve `release/raw/0.0.1` byte-for-byte and create `release/raw/0.0.2` for corrected assets.

## Recommended Fix

Create a successor asset release `0.0.2`; never regenerate or mutate finalized `0.0.1`. Parameterize the generator for a new release version while retaining deterministic authority. Replace nested full-solid outline layering for arrow/circle/shield with explicit front-facing ring geometry (outer polygon/disc minus inner silhouette) plus a bounded dark separation/bevel and role-colored inset, keeping exact dimensions/pivots/budgets. Fit each review camera from measured world bounds and compose a labeled neutral grid with reserved margins. Reframe context and individual wall/track renders from calculated bounds. Extend validation with projected-frame containment and required context instance/role counts.

## Debugging Record

Problem: First real 3D asset package mechanically validates but fails visual conformance.
Observed symptom: White perimeter reads as black with detached top highlight; multiple review renders crop or omit required roles.
Root cause: Nested complete solids with tiny depth offsets do not form an explicit visible front ring; hard-coded cameras/placements do not fit projected bounds.
Evidence: Native render inspection; `build_geometry` layering and `review` fixed-camera code; mechanical validation passes unchanged.
Failed approaches: Initial implementation relied on material presence and file-level validation rather than projected visual acceptance.
Corrective action: Preserve immutable 0.0.1; create 0.0.2 with explicit front ring geometry and bounds-fitted/labeled review layouts.
Verification test: Native visual comparison, projected-frame containment, required-role/instance evidence, strict GLB/import/hash/reproducibility validation.
Related files/components: `tools/generate.py`, `tools/validate.py`, `review/0.0.1/`, `release/raw/0.0.1/`, arrow/circle/shield geometry.
Remaining uncertainty: Best ring/bevel depth for identical appearance in both target engines must be validated after runtime integration.
