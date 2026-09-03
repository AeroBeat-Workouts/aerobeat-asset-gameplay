# Visibility comparison board GLB import failure

## Exact Observed Failure

`blender --background --factory-startup --python tools/generate.py -- --output-root . --release 0.0.3` authored the seven source/release assets and first two review renders, then failed while constructing `visibility-comparison.png`.

The direct error was:

```text
ModuleNotFoundError: No module named 'numpy'
...
tools/generate.py, line 427, in review
  arrow=import_review_mesh(...)
tools/generate.py, line 369, in import_review_mesh
  bpy.ops.import_scene.gltf(filepath=str(path))
RuntimeError: Error: Python: Traceback ...
```

The failure occurs in Blender's bundled `io_scene_gltf2` importer before it reads the selected GLB mesh. Blender misleadingly exited with process status 0 after printing the uncaught Python traceback, so process status alone is not sufficient evidence of generation success.

## Expected Behavior

The generator must render one truthful side-by-side comparison board from the exact predecessor/current GLB bytes without requiring network access, third-party Python packages, or host modifications. It must finish all ten PNGs and review metadata before strict validation.

## Execution Path

1. `main()` generates seven sources, GLBs, manifests, the set, inventory, and proof.
2. `review()` renders the neutral and gameplay-context images.
3. The visibility-board path calls `import_review_mesh()` for each predecessor/current arrow and track cell.
4. `import_review_mesh()` invokes Blender's optional glTF add-on operator.
5. The add-on imports `numpy` from Blender's Python environment.
6. Blender 4.0.2 on this host has no bundled/available `numpy`, so import initialization fails before any GLB mesh is returned.
7. `visibility-comparison.png`, its layout entry, and final review hash metadata are therefore absent.

## Most Likely Root Cause

The generator introduced an avoidable dependency on Blender's glTF import add-on. That add-on depends on `numpy`, while this repository's declared tool contract permits only Python standard library plus Blender `bpy`/`mathutils` and does not install or vendor NumPy. The traceback identifies this exact import boundary, and earlier generator stages that use only repository code and Blender APIs succeed.

## Alternative Hypotheses

1. **Malformed generated GLB** — unlikely. The exception occurs while importing the add-on modules, before file parsing; existing deterministic GLB parsing did not report an error.
2. **Missing glTF add-on** — contradicted. The add-on is present and begins executing; its transitive NumPy import is missing.
3. **Bad predecessor path** — contradicted. No file-open/path error occurs, and the traceback never reaches GLB parsing.
4. **Review geometry/camera defect** — not yet testable because board construction stops before meshes exist.

## Why Previous Fixes Failed

No repair was attempted before this diagnosis. The implementation assumed Blender's built-in glTF operator was dependency-complete because prior smoke-import evidence existed. That assumption was not verified against the current factory-startup Blender Python environment.

## Unknowns

- Whether the completed board will need camera/layout adjustment after the import dependency is removed. Native image inspection and containment validation will resolve this.
- Why Blender returns shell status 0 for the uncaught script exception on this package build. The fix must verify required output inventory rather than relying only on exit status.

## Minimal Reproduction

Run Blender 4.0.2 factory-startup and execute `bpy.ops.import_scene.gltf(filepath=<valid local GLB>)`. Importer initialization raises `ModuleNotFoundError: No module named 'numpy'`. Generator paths that do not invoke `bpy.ops.import_scene.gltf` succeed.

## Proposed Verification

Replace only the review loader with a repository-owned minimal GLB reconstruction path using the existing standard-library GLB JSON/BIN parsing contract. It should reconstruct POSITION/indexed triangle primitives and analytic materials from the exact selected GLB bytes. Then regenerate in a clean absent `0.0.3` target and require all review files, exact board counts, GLB hashes, projected containment, strict validation, and native board inspection.

## Recommended Fix

Implement a minimal deterministic review-only GLB mesh reader in `tools/generate.py` instead of using Blender's optional importer. Reuse the repository's known minimal GLB shape: one buffer, POSITION accessor, indexed triangle primitives, and analytic glTF materials. This keeps the board truthful to exact release bytes, preserves the dependency allowlist, and avoids installing or fetching NumPy. Also ensure failed partial `0.0.3` output is removed only during this pre-finalization recovery; thereafter the generator's existing-target guard remains fail-closed.

## Debugging Record

Problem: Truthful 0.0.2-vs-0.0.3 GLB comparison board cannot be generated.
Observed symptom: Blender glTF importer raises `ModuleNotFoundError: No module named 'numpy'`; comparison/review metadata is incomplete.
Root cause: New review path depends on optional `io_scene_gltf2` NumPy support outside the repository's allowed tool contract.
Evidence: Exact traceback during importer module initialization; all pre-import generation stages succeed.
Failed approaches: Initial implementation assumed the Blender glTF operator was self-contained.
Corrective action: Parse this repository's minimal deterministic GLB format directly and reconstruct review meshes/materials with standard library plus `bpy`.
Verification test: Clean regeneration; exact ten-PNG review inventory; comparison counts/hashes/material labels/containment; strict validator and native inspection.
Related files/components: `tools/generate.py::import_review_mesh`, `review/0.0.3/`, `release/raw/0.0.3/`.
Remaining uncertainty: Final board readability/layout until regenerated and inspected.
