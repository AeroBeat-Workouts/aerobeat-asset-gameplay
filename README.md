# AeroBeat Gameplay Assets

Canonical, cross-engine gameplay art for AeroBeat. This repository owns editable Blender sources, deterministic generation/export/validation tooling, engine-neutral GLBs, versioned manifests, mix-and-match set definitions, and Blender-rendered review evidence. It contains **no engine runtime code**, PlayCanvas/Godot integration, importer metadata, external assets, fonts, textures, or network-fetched content.

## Boundaries

- `source/<role>/<variant>/` — one editable `.blend` per independently swappable asset.
- `manifests/<role>/<variant>.v1.json` — strict source/release identity and measured export facts.
- `sets/default-v1.json` — independently maps each semantic role to one variant.
- `release/raw/0.0.1/` — immutable original runtime payload, retained byte-for-byte.
- `release/raw/0.0.2/` — immutable corrected runtime predecessor; retained byte-for-byte.
- `release/raw/0.0.3/` — immutable visibility predecessor retained byte-for-byte.
- `release/raw/0.0.4/` — deterministic bidirectional-arrow successor: the complete seven-asset shape with a closed, non-coplanar, opaque `outline-v1` styled on both `+Z` and `-Z`; never sources or tools.
- `review/<version>/` — Blender-rendered visual evidence, calculated containment/contrast metadata, and hashes outside runtime releases; `review/0.0.1/` through `review/0.0.3/` remain unchanged.
- `tools/` — locally authored Blender/Python generation, export, review, and strict validation scripts.

After a release validates, do not mutate it. Corrections require a new release version.

## Commands

Requires Blender `4.0.2` and Python 3.

```bash
blender --background --factory-startup --python tools/generate.py -- --output-root . --release 0.0.4
python3 tools/validate.py --root . --release 0.0.4
python3 tools/reproducibility.py --root . --release 0.0.4
python3 tools/test_subprocess_contract.py --root .
python3 tools/validate.py --root . --release 0.0.4 --finalize
```

Generation requires explicit supported successor `0.0.4`, preserves six unchanged source snapshots, re-authors only the arrow source, exports the complete seven separate `.glb` files, writes measured manifests/proof, and renders review evidence. The arrow is three closed, nested, depth-separated opaque solids: a white outer frame at `Z=±0.09`, charcoal separator at `Z=±0.088`, and tintable core at `Z=±0.086`. Both camera-accessible faces therefore retain the same untinted white/charcoal treatment with no coplanar overlapping caps. Every arrow material is alpha `1.0`, explicit `OPAQUE`, back-face culled, depth-tested, and depth-writing. Eight screen directions are rotations about local Z for a `+Z` runtime camera, with no renderer Y flip. The unchanged track remains alpha `0.52`, translucent blue glass, depth-tested, depth-write-off, and ordered after grid surfaces but before walls. Validation parses GLB headers, JSON/BIN chunks, checks closed two-manifold arrow geometry, rejects positive-area coplanar cap overlap, verifies both-face depth structure and eight direction semantics, checks exact inventory/hashes/names/bounds/pivots/budgets/material contracts/dependencies/license/predecessor immutability, and verifies `+Z`/`-Z` bright-background review containment and analytic contrast before clean Blender source/GLB smoke operations. Every subprocess uses one fail-closed contract. Reproducibility compares both temporary builds with the immutable primary.

## Coordinates and consumption

Right-handed, **+Y up**, gameplay/local forward **−Z**. Assets are authored at identity rotation and unit scale with the specification-defined pivot. Consumers may independently mix variants through a set manifest and own runtime placement, role colors, direction rotation, timing tint, interval scaling, transparent sorting, outline passes, lane/row visuals, instancing, and world text. `guard/shield-v1` is one canonical model that consumers instance twice.

## Rights

All geometry, materials, scripts, and renders are original locally authored AeroBeat/Gambit Games work made only from procedural primitives. No third-party content is included. Licensed under CC BY-NC 4.0; see `LICENSE.md`.
