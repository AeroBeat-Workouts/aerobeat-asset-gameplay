# AeroBeat Gameplay Assets

Canonical, cross-engine gameplay art for AeroBeat. This repository owns editable Blender sources, deterministic generation/export/validation tooling, engine-neutral GLBs, versioned manifests, mix-and-match set definitions, and Blender-rendered review evidence. It contains **no engine runtime code**, PlayCanvas/Godot integration, importer metadata, external assets, fonts, textures, or network-fetched content.

## Boundaries

- `source/<role>/<variant>/` — one editable `.blend` per independently swappable asset.
- `manifests/<role>/<variant>.v1.json` — strict source/release identity and measured export facts.
- `sets/default-v1.json` — independently maps each semantic role to one variant.
- `release/raw/0.0.1/` — immutable original runtime payload, retained byte-for-byte.
- `release/raw/0.0.2/` — immutable corrected runtime predecessor; retained byte-for-byte.
- `release/raw/0.0.3/` — immutable visibility predecessor retained byte-for-byte.
- `release/raw/0.0.4/` — immutable bidirectional-arrow predecessor retained byte-for-byte.
- `release/raw/0.0.5/` — deterministic wall-footprint successor: the complete seven-asset shape with only `wall/red-glass-v1` re-authored to exact `0.94 × 0.94 × 1.00` source dimensions; never sources or tools.
- `review/<version>/` — Blender-rendered visual evidence, calculated containment/contrast/wall-grid metadata, and hashes outside runtime releases; `review/0.0.1/` through `review/0.0.4/` remain unchanged.
- `tools/` — locally authored Blender/Python generation, export, review, and strict validation scripts.

After a release validates, do not mutate it. Corrections require a new release version.

## Commands

Requires Blender `4.0.2` and Python 3.

```bash
blender --background --factory-startup --python tools/generate.py -- --output-root . --release 0.0.5
python3 tools/validate.py --root . --release 0.0.5
python3 tools/reproducibility.py --root . --release 0.0.5
python3 tools/test_subprocess_contract.py --root .
python3 tools/validate.py --root . --release 0.0.5 --finalize
```

Generation requires explicit supported successor `0.0.5`, preserves six non-wall source snapshots and GLBs byte-for-byte from `0.0.4`, re-authors only the wall source, exports the complete seven separate `.glb` files, writes measured manifests/proof, and renders review evidence. The wall is exactly `0.94 × 0.94 × 1.00`, centered at the origin in right-handed `+Y`-up/local `−Z`-forward coordinates. Its analytic red-glass body and red edge cage remain alpha blended, back-face culled, depth-tested, depth-write-off, and ordered after the track. Consumers keep unit X/Y scale and vary only Z from the authoritative obstacle interval; adjacent `1.0`-pitch cells retain an exact `0.06` gap with no overlap. The unchanged arrow remains closed, bidirectionally styled, opaque, and runtime-tintable only at its core; the unchanged track remains alpha `0.52` and ordered after grid surfaces but before walls. Validation parses GLB headers and JSON/BIN chunks; checks exact dimensions, centered pivot, closed wall body, analytic edge structure, cell-footprint/gap/Z-only reuse evidence, source/GLB identity, inventory/hashes/names/bounds/budgets/materials/dependencies/license, all predecessor trees, six-asset non-wall drift, and review containment/contrast before clean Blender source/GLB smoke operations. Every subprocess uses one fail-closed contract. Reproducibility compares two independent temporary builds with the immutable primary.

The finalized `0.0.5` raw release contains exactly 17 files / 45,819 bytes with tree digest `24f6bb3b86657716ed03958a32dee5c9db3904aa980cb0a839aacac0590cc860`, inventory SHA-256 `4984cca24b8121bc6657153304726f1f7ef05d878ca5220f3c3e2b6f2457a102`, and proof SHA-256 `4aac2274a9803a05e9ff533c02958cf1c5def66e0af1bf2fae3cc4479319f350`. Its wall GLB is 3,692 bytes with SHA-256 `1227bfbb7d5379b33f1468c1a0d7fffad07c9390654b54033f079ba602a84a37`. Review `0.0.5` contains 13 RGB `1600 × 900` PNGs plus five JSON evidence files.

## Coordinates and consumption

Right-handed, **+Y up**, gameplay/local forward **−Z**. Assets are authored at identity rotation and unit scale with the specification-defined pivot. Consumers may independently mix variants through a set manifest and own runtime placement, role colors, direction rotation, timing tint, interval scaling, transparent sorting, outline passes, lane/row visuals, instancing, and world text. `guard/shield-v1` is one canonical model that consumers instance twice.

## Rights

All geometry, materials, scripts, and renders are original locally authored AeroBeat/Gambit Games work made only from procedural primitives. No third-party content is included. Licensed under CC BY-NC 4.0; see `LICENSE.md`.
