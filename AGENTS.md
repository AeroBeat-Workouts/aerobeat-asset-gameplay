# AGENTS.md

## Scope

This repository owns only canonical, engine-neutral AeroBeat gameplay art: editable Blender sources, deterministic generation/export/validation tools, per-asset manifests, mix-and-match sets, immutable raw releases, and review renders. Do not add engine runtime code, importer metadata, textures, fonts, downloaded content, or third-party assets.

## Canonical contract

- Blender is pinned to exactly `4.0.2`; Python tools use only the standard library except Blender-only `bpy`/`mathutils`.
- Coordinates are right-handed, +Y up, local forward -Z. Sources use identity object rotation and scale.
- Every role/variant is independently swappable and has one `.blend`, one `.glb`, and one strict v1 manifest.
- `guard/shield-v1` is the sole shield model. Runtime consumers must instance it twice for guard beats; never author left/right variants.
- Materials are analytic. Do not add images, textures, fonts, normal maps, or external dependencies.
- Preserve exact dimensions, pivots, collision-free bounds, triangle budgets, role names, filenames, rights, and provenance in the visual spec and manifests.

## Workflow

Generate and validate from the repository root:

```bash
blender --background --factory-startup --python tools/generate.py -- --output-root . --release 0.0.6
python3 tools/validate.py --root . --release 0.0.6
python3 tools/reproducibility.py --root . --release 0.0.6
python3 tools/test_subprocess_contract.py --root .
python3 tools/validate.py --root . --release 0.0.6 --finalize
```

Generation requires the explicit supported successor `0.0.6`, preserves directional arrow, circle, guard, bomb, wall, and track source snapshots, GLBs, and per-asset manifests byte-for-byte from `0.0.5`, re-authors only `athlete-marker/sphere-v1`, and fails closed if its release or review target already exists. The marker remains one canonical `0.18`-unit sphere for nose and both wrists, with one closed partitioned surface, an explicitly runtime-tintable core, stable white/charcoal structural materials, deterministic radial normals, and alpha-1 OPAQUE depth-writing semantics visible from every cardinal camera direction. Blender may print an uncaught Python traceback and still exit zero, so all Blender-backed subprocesses must use `tools/subprocess_contract.py`: combined output, rc 0, no fatal signature, one exact operation/identity marker, and explicit postconditions. Finalized `release/raw/0.0.1` through `0.0.6` and matching review trees are immutable and must never be regenerated, deleted, or rewritten. Review PNGs belong under `review/`, never under `release/`.

## Release rule

`release/raw/<version>/` may contain only separate GLBs, copied per-asset manifests, the copied set, and top-level inventory/proof JSON. A release is immutable after final validation. Do not commit or publish until strict validation, clean Blender smoke imports, and the two-temporary-build byte comparison pass.
