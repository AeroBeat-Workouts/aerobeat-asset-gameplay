# Uniform-wall candidate validator primitive mismatch

## Exact Observed Failure

The first focused candidate validation failed at `validate_uniform_wall_candidate.py:33` with `AssertionError: wall primitive contract`. Direct GLB inspection showed one primitive with shared attributes `{"NORMAL":1,"POSITION":0}`.

## Expected Behavior

The candidate must have one material primitive, one uniform alpha material, 12 geometric triangles, exact bounds, explicit outward face normals, and no edge-cage primitive.

## Execution Path

`generate.py` marks wall as the changed role. `write_glb()` therefore splits GLB corners per triangle and writes explicit flat `POSITION` and `NORMAL` attributes. The validator incorrectly expected only `POSITION`, then failed before geometry/material checks.

## Most Likely Root Cause

The validator encoded the predecessor's welded-position assumption rather than the changed-role exporter contract. Source lines 454–467 explicitly split every changed-role triangle corner and emit normals. The generated GLB has one primitive/material and no edge cage, so the extra attribute is correct rather than evidence of a second surface.

## Alternative Hypotheses

- A second edge primitive survived: contradicted by one primitive and one material.
- External Blender exporter altered the file: contradicted by the locally authored deterministic writer and exact document structure.
- Wall topology is no longer closed: not yet evaluated because validation failed before welded-position reconstruction.

## Why Previous Fixes Failed

This is the first validator implementation. Its assumption conflated GLB vertex identity with welded geometric identity.

## Unknowns

Closed-manifold edge counts must be computed after welding identical split positions, not from raw GLB indices.

## Minimal Reproduction

Run the focused validator against `/tmp/aerobeat-wall-prep2-rufv23g3`; it fails on the attribute set before other checks.

## Proposed Verification

Accept exact `POSITION`+`NORMAL`, require 36 corner positions/normals, weld identical coordinates to eight geometric vertices, remap triangle indices, then require every welded undirected edge exactly twice.

## Recommended Fix

Update only the focused validator to model the intentional changed-role export representation. Keep the one-primitive/one-material prohibition strict.

## Debugging Record

```text
Problem: Validator rejects correct explicit-normal wall GLB.
Observed symptom: primitive contract fails on NORMAL attribute.
Root cause: Validator assumed welded POSITION-only export; changed roles use split corners plus explicit normals.
Evidence: generate.py lines 454–467 and inspected one-primitive document.
Failed approaches: Initial raw-index manifold assumption.
Corrective action: Weld position coordinates for topology and validate exact POSITION/NORMAL split-corner structure.
Verification test: Focused candidate validator passes all subsequent geometry/material/evidence checks.
Related files/components: tools/generate.py, tools/validate_uniform_wall_candidate.py.
Remaining uncertainty: Subsequent checks have not yet executed.
```
