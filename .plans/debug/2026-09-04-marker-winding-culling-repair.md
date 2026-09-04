# Marker winding/culling defect diagnosis

## Exact Observed Failure

Immutable release `0.0.6` marker `release/raw/0.0.6/athlete-marker/sphere-v1.glb` has 168/168 triangles with negative `cross(b-a,c-a) dot centroid`; independently reproduced range is `-0.000139488119914183` through `-0.00005337978711546069`. All 504 face-normal-to-referenced-explicit-NORMAL comparisons are negative (`-0.9794479653887043` through `-0.9485757794242599`). The source `.blend` likewise has 168/168 inward polygon normals, polygon-normal/center range `-0.08815032104030252` through `-0.08537181559950113`, vertex-normal/radial range `-1.0000000298023224` through `-0.9995670765638351`, and all three source materials have `use_backface_culling=False`.

These are direct observations. The rendering consequence is inferred from standard glTF CCW-front semantics plus the file's `doubleSided:false` and explicit `cull:back` contract: exterior faces are back-facing and culled.

## Expected Behavior

The marker must retain its exact semantic design and dimensions while every triangle is outward CCW: geometric face normal dot triangle centroid must be safely positive, and each normalized geometric face normal must positively agree with every referenced explicit outward unit radial vertex NORMAL. The editable Blender source must have outward polygon/vertex normals and backface culling enabled. GLB smoke and visual review must exercise the actual winding/NORMAL/culling contract.

## Execution Path

1. `tools/generate.py:uv_sphere()` creates sphere positions and indices.
2. Its top, middle, and bottom face orders currently produce inward geometric normals.
3. `make_asset()` transfers those indices unchanged into the Blender mesh and smooths it, yielding inward source polygon and vertex normals.
4. `write_glb()` writes those polygon indices but independently synthesizes outward radial `NORMAL` values, creating a geometry/NORMAL contradiction.
5. GLB materials declare `doubleSided:false` and `cull:back`.
6. `import_review_mesh()` and `tools/smoke_import.py` reconstruct only positions/faces, ignore embedded NORMAL agreement, and leave Blender material culling disabled.
7. `assert_marker_geometry()` checks radial NORMAL values, topology, partition, and centroid-side material presence, but not winding or geometric/NORMAL agreement.
8. Therefore official validation and attractive no-cull review images pass despite a runtime-invalid marker exterior.

## Most Likely Root Cause

`uv_sphere()` uses reversed triangle order for the sphere's coordinate convention. Direct GLB and Blender-source measurements prove that every face is consistently inward, while `write_glb()` separately emits outward radial normals. The missing strict assertions and no-cull review/smoke path allowed the defect to escape.

## Alternative Hypotheses

1. **Highest secondary likelihood: glTF handedness or node transform flips orientation.** Contradicted by glTF's right-handed contract and the GLB's identity node without transform fields.
2. **Renderer intentionally disables culling.** Contradicted by `doubleSided:false` and explicit `cull:back`; engine-specific tolerance cannot satisfy the engine-neutral asset contract.
3. **Only shading normals are wrong.** Contradicted by direct negative geometric cross-product/centroid values for all 168 triangles.
4. **Review camera placement causes apparent disappearance.** Contradicted by the all-face mathematical defect; camera placement only hid it because source/review materials did not cull.

## Why Previous Fixes Failed

The `0.0.6` work improved marker material structure and supplied explicit radial normals, but assumed the inherited sphere face order was outward. Existing validation treated radial vertex normals and closed topology as sufficient. Existing smoke/review reconstruction ignored the NORMAL accessor and did not enable backface culling, so it tested a more permissive rendering mode than the declared GLB contract.

## Unknowns

No root-cause unknown remains. Exact successor byte hashes and positive numeric ranges are unknown until an isolated temporary build succeeds. Native rendered appearance under culling must also be inspected after preflight.

## Minimal Reproduction

Parse the `0.0.6` GLB POSITION, NORMAL, and index accessors. For every triangle, calculate `cross(b-a,c-a) dot ((a+b+c)/3)`. All 168 values are negative. Normalize that cross product and dot it with each referenced NORMAL; all 504 values are negative. Opening the source `.blend` independently shows inward polygon/vertex normals and culling disabled.

## Proposed Verification

Before canonical generation, build `0.0.7` in fresh temporary roots and require:

- exactly 168 strictly positive winding values above a fixed epsilon;
- all 504 geometric-face/NORMAL dots strictly positive and near radial agreement;
- exact outward Blender polygon/vertex normals;
- source and reconstructed review materials with backface culling enabled;
- an inward-wound GLB mutation rejected by the same validator path;
- strict/final validation, clean source/GLB smoke, two-build byte reproducibility, and unchanged predecessor/non-marker identities.

## Recommended Fix

Reverse only the marker sphere face order at generation (or correct `uv_sphere()` globally only if every consumer is audited; marker-local reversal is safer because other roles are immutable). Enable source material backface culling, import and verify embedded NORMAL values in review/smoke, enable backface culling on reconstructed materials, and add fail-closed GLB/source assertions plus an inward-mutation regression test. Advance tooling/docs/manifests/set/proof/inventory to append-only `0.0.7`, pin all raw/review predecessors through `0.0.6`, and preserve six non-marker assets byte-for-byte from `0.0.6`.

Potential regressions: material partition ordering, exact 168-triangle/AABB contract, review image composition, and non-marker byte identity. All are covered by existing and strengthened gates.

## Debugging Record

```text
Problem: Marker exterior is culled under its declared glTF material contract.
Observed symptom: All 168 GLB/source faces are inward while explicit GLB normals are outward; source/review culling is disabled.
Root cause: Marker sphere triangle order is reversed, and validators/review/smoke omitted winding/NORMAL/culling assertions.
Evidence: Negative GLB cross-dot-centroid and face/NORMAL ranges; negative Blender polygon/vertex normal ranges; doubleSided:false versus use_backface_culling=False.
Failed approaches: 0.0.6 relied on radial NORMAL values, topology, and no-cull renders without geometric orientation verification.
Corrective action: Marker-local face reversal; culling-enabled source/review/smoke; strict winding/NORMAL/source assertions and inward-mutation test.
Verification test: Fresh-root 0.0.7 preflight, positive 168/168 winding and 504/504 agreement, source outward normals/culling, mutation rejection, complete deterministic gates.
Related files/components: tools/generate.py, tools/validate.py, tools/smoke_import.py, tools/smoke_source.py, tools/reproducibility.py, tools/test_subprocess_contract.py, marker manifests/review evidence.
Remaining uncertainty: Final successor byte hashes and native rendered evidence until isolated generation.
```
