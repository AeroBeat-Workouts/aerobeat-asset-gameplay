# Bidirectional arrow cap validation diagnosis

## Exact Observed Failure

`python3 tools/validate.py --root . --release 0.0.4` failed at `assert_closed_nonoverlapping_mesh()` with:

```text
AssertionError: .../release/raw/0.0.4/directional-arrow/outline-v1.glb: coplanar overlapping caps at z=-0.09
```

A targeted read-only probe identified the first positive-area pair on the white `-Z` annulus at primitive 0 triangles 12 and 21. Their calculated intersection area is `0.00005760000100135665` square units.

## Expected Behavior

The successor arrow must be closed and must have no positive-area coplanar cap overlap. Adjacent triangles may share vertices or boundary edges, but their interiors must be disjoint.

## Execution Path

The generator builds the concave seven-vertex outer arrow loop, derives inner loops by uniform radial scaling, passes corresponding loops to `closed_frame()`, writes the resulting triangles into the GLB, and the strict validator groups constant-Z cap triangles and calculates pairwise intersection area.

## Most Likely Root Cause

Uniform radial scaling is not a valid geometric offset for this concave arrow. At the shoulder/notch vertices, adjacent annulus quads intrude into one another. The validator correctly detected positive-area overlap; this is not merely duplicate-edge tolerance. Evidence is the intersecting pair around outer `(0.16, 0.05)` and scaled-inner `(0.1408, 0.044)` shoulder coordinates.

## Alternative Hypotheses

1. **Triangle-clipping numerical error (lower likelihood):** the reported area is much larger than the `1e-9` threshold and corresponds to the concave shoulder wedge, not tiny floating-point noise.
2. **Incorrect cap winding (contributing but not causal):** the two triangles have opposite signed winding, but the clipping function normalizes the clip polygon; shared-boundary-only triangles would still have zero interior area.
3. **Duplicate triangles from material primitives (contradicted):** both reported triangles are within primitive 0, so cross-material duplication is not the cause.

## Why Previous Fixes Failed

The first successor implementation solved the predecessor's duplicated full rear caps by replacing them with nested closed frames, but it reused radial scaling from the legacy single-face ring. That assumption treated nested loops as valid offsets even at concave shoulders.

## Unknowns

The exact hand-authored inner shoulder coordinates that maximize visual uniformity are not yet fixed. A fresh generation plus the structural validator resolves this.

## Minimal Reproduction

Generate `0.0.4`, then run strict validation. The first overlap appears at `z=-0.09` between white annulus triangles 12 and 21. Convex ring roles do not exhibit this concave-shoulder case.

## Proposed Verification

Replace the arrow's scaled inner loops with explicit nested arrow loops whose concave shoulder moves inward/upward. Regenerate once in a disposable temporary root first and require: closed two-manifold edges, zero positive-area same-plane triangle intersections, exact `0.78 × 0.78 × 0.18` dimensions, and both-face renders retaining white/charcoal/tint separation.

## Recommended Fix

Keep the three depth-separated closed solids, but hand-author the separator and inset arrow loops rather than deriving them by radial scale. Validate the temporary output before changing the already-created canonical `0.0.4` candidate; because the canonical target is unfinalized and failed its first strict gate, remove/rebuild that failed candidate only after the temporary geometry passes.

## Debugging Record

```text
Problem: Bidirectional arrow white annulus fails non-overlap validation.
Observed symptom: Positive-area coplanar intersection at z=-0.09.
Root cause: Radial scaling of a concave arrow is not a valid inset/offset and creates overlapping shoulder wedges.
Evidence: Primitive 0 triangles 12/21 overlap by 0.00005760000100135665 around the right concave shoulder.
Failed approaches: Nested closed frames with uniformly scaled inner loops.
Corrective action: Use explicit nested arrow loops with inward/upward concave shoulders.
Verification test: Disposable generation plus closed-manifold and pairwise cap-intersection validation, then full strict chain.
Related files/components: tools/generate.py, tools/validate.py, directional-arrow/outline-v1 GLB/source.
Remaining uncertainty: Final explicit inner-loop proportions pending visual/structural regeneration.
```

## Disposable probe follow-up

The explicit-loop probe passed the new cap-overlap stage and advanced to a separate immutability failure: `any-note: geometry/material GLB changed outside approved scope`. Root cause is that unchanged roles were reserialized with the generator identity advanced from v2 to v3, changing otherwise identical GLB JSON bytes. The corrective action is to copy each unchanged role's exact predecessor GLB into the successor release and author only the arrow GLB. This is both narrower and aligned with the requirement that all non-arrow asset bytes remain unchanged. The probe directory copied read-only finalized predecessors, so its first cleanup attempt failed; permissions were restored only inside that disposable `/tmp` directory and it was then removed completely. Canonical predecessor permissions/bytes were untouched.

The first subprocess-contract run then failed before exercising fake Blender because `tools/test_subprocess_contract.py` still invoked validator/reproducibility with retired release `0.0.3` and expected the retired generator marker. Argparse rejected that release, so the adversarial harness correctly treated the output as the wrong failure. The smallest fix is advancing only those three hard-coded test identities to supported `0.0.4` and its 12-PNG/4-metadata marker; the fail-closed contract implementation itself is unchanged.
