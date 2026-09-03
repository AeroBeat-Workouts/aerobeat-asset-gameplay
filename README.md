# AeroBeat Gameplay Assets

Canonical, cross-engine gameplay art for AeroBeat. This repository owns editable Blender sources, deterministic generation/export/validation tooling, engine-neutral GLBs, versioned manifests, mix-and-match set definitions, and Blender-rendered review evidence. It contains **no engine runtime code**, PlayCanvas/Godot integration, importer metadata, external assets, fonts, textures, or network-fetched content.

## Boundaries

- `source/<role>/<variant>/` — one editable `.blend` per independently swappable asset.
- `manifests/<role>/<variant>.v1.json` — strict source/release identity and measured export facts.
- `sets/default-v1.json` — independently maps each semantic role to one variant.
- `release/raw/0.0.1/` — immutable original runtime payload, retained byte-for-byte.
- `release/raw/0.0.2/` — immutable corrected runtime predecessor; retained byte-for-byte.
- `release/raw/0.0.3/` — immutable visibility successor: the complete seven-asset shape with opaque tintable arrows and a materially stronger blue-glass track; never sources or tools.
- `review/<version>/` — Blender-rendered visual evidence, calculated containment metadata, and hashes outside runtime releases; `review/0.0.1/` and `review/0.0.2/` remain unchanged.
- `tools/` — locally authored Blender/Python generation, export, review, and strict validation scripts.

After a release validates, do not mutate it. Corrections require a new release version.

## Commands

Requires Blender `4.0.2` and Python 3.

```bash
blender --background --factory-startup --python tools/generate.py -- --output-root . --release 0.0.3
python3 tools/validate.py --root . --release 0.0.3
python3 tools/reproducibility.py --root . --release 0.0.3
python3 tools/validate.py --root . --release 0.0.3 --finalize
```

Generation requires an explicit supported release, preserves the five unchanged source snapshots, authors only the arrow/track material successors, exports the complete seven separate `.glb` files, writes measured manifests/proof, and renders review evidence. The arrow core is neutral and runtime-tintable to red/yellow/green while every arrow material is alpha `1.0`, explicit `OPAQUE`, back-face culled, depth-tested, and depth-writing; its structural white outline remains untinted. Track body alpha is `0.52`, intentionally `2.6×` the predecessor's `0.20`: strong enough to read over bright ice while remaining translucent blue glass, depth-tested, depth-write-off, and ordered after grid surfaces but before walls. Validation parses GLB headers and JSON chunks, checks exact source/release inventory, hashes, names, bounds, pivots, budgets, material/depth/order contracts, dependencies, license integrity, and predecessor immutability, verifies calculated review containment/counts/labels, then smoke-imports every GLB into clean Blender. Reproducibility builds that explicit release twice in temporary roots and compares every release byte.

## Coordinates and consumption

Right-handed, **+Y up**, gameplay/local forward **−Z**. Assets are authored at identity rotation and unit scale with the specification-defined pivot. Consumers may independently mix variants through a set manifest and own runtime placement, role colors, direction rotation, timing tint, interval scaling, transparent sorting, outline passes, lane/row visuals, instancing, and world text. `guard/shield-v1` is one canonical model that consumers instance twice.

## Rights

All geometry, materials, scripts, and renders are original locally authored AeroBeat/Gambit Games work made only from procedural primitives. No third-party content is included. Licensed under CC BY-NC 4.0; see `LICENSE.md`.
