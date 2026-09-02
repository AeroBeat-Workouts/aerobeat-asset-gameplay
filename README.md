# AeroBeat Gameplay Assets

Canonical, cross-engine gameplay art for AeroBeat. This repository owns editable Blender sources, deterministic generation/export/validation tooling, engine-neutral GLBs, versioned manifests, mix-and-match set definitions, and Blender-rendered review evidence. It contains **no engine runtime code**, PlayCanvas/Godot integration, importer metadata, external assets, fonts, textures, or network-fetched content.

## Boundaries

- `source/<role>/<variant>/` — one editable `.blend` per independently swappable asset.
- `manifests/<role>/<variant>.v1.json` — strict source/release identity and measured export facts.
- `sets/default-v1.json` — independently maps each semantic role to one variant.
- `release/raw/0.0.1/` — immutable original runtime payload, retained byte-for-byte.
- `release/raw/0.0.2/` — immutable corrected runtime payload: separate GLBs, manifests, set, inventory, and proof only; never sources or tools.
- `review/<version>/` — Blender-rendered visual evidence, calculated containment metadata, and hashes outside runtime releases; `review/0.0.1/` remains unchanged.
- `tools/` — locally authored Blender/Python generation, export, review, and strict validation scripts.

After a release validates, do not mutate it. Corrections require a new release version.

## Commands

Requires Blender `4.0.2` and Python 3.

```bash
blender --background --factory-startup --python tools/generate.py -- --output-root . --release 0.0.2
python3 tools/validate.py --root . --release 0.0.2
python3 tools/reproducibility.py --root . --release 0.0.2
python3 tools/validate.py --root . --release 0.0.2 --finalize
```

Generation requires an explicit supported release, authors each `.blend`, exports its separate `.glb`, writes measured manifests/proof, and renders review evidence. Validation parses GLB headers and JSON chunks, checks inventory/hashes/names/bounds/pivots/budgets/dependencies, verifies calculated projected containment and required review-context counts, then smoke-imports every GLB into clean Blender. Reproducibility builds that explicit release twice in temporary roots and compares every release byte.

## Coordinates and consumption

Right-handed, **+Y up**, gameplay/local forward **−Z**. Assets are authored at identity rotation and unit scale with the specification-defined pivot. Consumers may independently mix variants through a set manifest and own runtime placement, role colors, direction rotation, timing tint, interval scaling, transparent sorting, outline passes, lane/row visuals, instancing, and world text. `guard/shield-v1` is one canonical model that consumers instance twice.

## Rights

All geometry, materials, scripts, and renders are original locally authored AeroBeat/Gambit Games work made only from procedural primitives. No third-party content is included. Licensed under CC BY-NC 4.0; see `LICENSE.md`.
