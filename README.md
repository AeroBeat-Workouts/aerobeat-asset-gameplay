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
- `release/raw/0.0.5/` — immutable wall-footprint predecessor retained byte-for-byte.
- `release/raw/0.0.6/` — deterministic marker-visibility successor: the complete seven-asset shape with only `athlete-marker/sphere-v1` re-authored; never sources or tools.
- `review/<version>/` — Blender-rendered visual evidence, calculated containment/contrast/wall-grid metadata, and hashes outside runtime releases; `review/0.0.1/` through `review/0.0.5/` remain unchanged.
- `tools/` — locally authored Blender/Python generation, export, review, and strict validation scripts.

After a release validates, do not mutate it. Corrections require a new release version.

## Commands

Requires Blender `4.0.2` and Python 3.

```bash
blender --background --factory-startup --python tools/generate.py -- --output-root . --release 0.0.6
python3 tools/validate.py --root . --release 0.0.6
python3 tools/reproducibility.py --root . --release 0.0.6
python3 tools/test_subprocess_contract.py --root .
python3 tools/validate.py --root . --release 0.0.6 --finalize
```

Generation requires explicit supported successor `0.0.6`, preserves directional arrow, circle, guard, bomb, wall, and track source snapshots, GLBs, and per-asset manifests byte-for-byte from `0.0.5`, and re-authors only the marker source. The marker remains one canonical `0.18 × 0.18 × 0.18` sphere for nose and both wrists. Its single closed, non-overlapping surface is partitioned into `mat/tint_base`, stable `mat/white`, and stable `mat/charcoal`; only the tint core advertises `runtimeTintable:true`. All three analytic materials are explicit alpha-1 `OPAQUE`, back-face culled, depth-tested, and depth-writing, and the GLB carries deterministic unit radial normals. Review evidence covers the actual predecessor/current marker on dark, bright, and blue fields plus every `±X/±Y/±Z` camera direction on both bright and dark fields. The unchanged exact wall remains `0.94 × 0.94 × 1.00`; the confirmed-good unchanged arrow retains its closed bidirectional opaque structure. Validation parses GLB headers and JSON/BIN chunks; checks exact dimensions, marker topology/material partition/normals/all-direction visibility/no-coplanar contract, inventory/hashes/names/bounds/budgets/materials/dependencies/license, immutable raw/review `0.0.1–0.0.5`, exact six-role predecessor byte identity, and review containment/contrast before clean Blender source/GLB smoke operations. Every subprocess uses one fail-closed contract. Reproducibility compares two independent temporary builds with the immutable primary.

The finalized `0.0.5` raw release contains exactly 17 files / 45,819 bytes with tree digest `24f6bb3b86657716ed03958a32dee5c9db3904aa980cb0a839aacac0590cc860`, inventory SHA-256 `4984cca24b8121bc6657153304726f1f7ef05d878ca5220f3c3e2b6f2457a102`, and proof SHA-256 `4aac2274a9803a05e9ff533c02958cf1c5def66e0af1bf2fae3cc4479319f350`. Its wall GLB is 3,692 bytes with SHA-256 `1227bfbb7d5379b33f1468c1a0d7fffad07c9390654b54033f079ba602a84a37`. Review `0.0.5` contains 13 RGB `1600 × 900` PNGs plus five JSON evidence files.

The finalized `0.0.6` raw release contains exactly 17 files / 49,337 bytes with tree digest `d46ef42fdb0b2b743acbc0fabf87e7ae8a24bb5f7a8af729b43d09bba09306e3`, inventory SHA-256 `4f45b1bf59c309b5d691d9bc0c03d737c9139d24963bec85c7055f82de1137d1`, and proof SHA-256 `d2c34e428b4db758db8cd06eac9dfb832f1b5b8a6b6545a0ea6da6bc20853899`. Its marker GLB is 5,496 bytes / 168 triangles with SHA-256 `bd7a1523eb62c6ba0cb0f1f19c69b8b2cecc7edc31d05b1cad55138ab86da145`. Review `0.0.6` contains 23 RGB `1600 × 900` PNGs plus five JSON evidence files.

## Coordinates and consumption

Right-handed, **+Y up**, gameplay/local forward **−Z**. Assets are authored at identity rotation and unit scale with the specification-defined pivot. Consumers may independently mix variants through a set manifest and own runtime placement, role colors, direction rotation, timing tint, interval scaling, transparent sorting, outline passes, lane/row visuals, instancing, and world text. `guard/shield-v1` is one canonical model that consumers instance twice.

## Rights

All geometry, materials, scripts, and renders are original locally authored AeroBeat/Gambit Games work made only from procedural primitives. No third-party content is included. Licensed under CC BY-NC 4.0; see `LICENSE.md`.
