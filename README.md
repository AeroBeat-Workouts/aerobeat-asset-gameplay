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
- `release/raw/0.0.6/` — immutable rejected marker evidence with inward-wound faces; never regenerate or repair it in place.
- `release/raw/0.0.7/` — append-only marker winding/culling successor: the complete seven-asset shape with only `athlete-marker/sphere-v1` re-authored.
- `review/<version>/` — Blender-rendered visual evidence, calculated containment/contrast/wall-grid metadata, and hashes outside runtime releases; `review/0.0.1/` through `review/0.0.6/` remain unchanged.
- `tools/` — locally authored Blender/Python generation, export, review, and strict validation scripts.

After a release validates, do not mutate it. Corrections require a new release version.

## Commands

Requires Blender `4.0.2` and Python 3.

```bash
# Immutable published baseline remains independently valid.
python3 tools/validate.py --root . --release 0.0.7
python3 tools/test_subprocess_contract.py --root .

# Staged rounded successor: generates only disposable temporary candidates.
python3 tools/reproducibility_rounded.py --root .
python3 tools/test_visible_window_budget.py
# Against a disposable candidate root produced by tools/generate.py:
python3 tools/validate_rounded_candidate.py --authority-root . --candidate-root /tmp/<candidate>
python3 tools/test_rounded_adversarial.py --candidate-root /tmp/<candidate>
```

## Staged Aero Rounded successor sources

The mutable source tree and manifests stage Alternative B identities `directional-arrow/rounded-outline-v1`, `any-note/outlined-circle-v1`, and the sole canonical two-instance guard `guard/outlined-shield-v1`. They do **not** constitute a release: canonical `release/raw/0.0.8` and `review/0.0.8` must remain absent until independent QA/audit authorization. `tools/generate.py` supports explicit successor `0.0.8` only in a disposable output root, copies bomb/wall/track/athlete-marker from immutable `0.0.7`, and generates 68 temporary actual-GLB review renders spanning both camera faces, side and three-quarter views on dark/bright/blue fields.

Each changed cue is one closed connected geometric two-manifold with outward consistent winding, explicit per-corner normals, three 30-degree axial bevel segments per face, and an opaque two-sided projected `charcoal → white → charcoal → fill` surface. The outer charcoal keyline includes the face bevel: circle projected radii remain exactly `0.350 / 0.336 / 0.284 / 0.264`. Only arrow/any `note_fill` advertises `runtimeTintable:true`; guard `guard_fill`, `outline_white`, and `outline_charcoal` are fixed. Because the `0.086` band stack crosses the medial axis of the specified small convex outer fillets, polygon cues use an explicit continuous medial-axis re-round while retaining at least 90% sampled corresponding width (within the `0.0015` chord tolerance).

The exact closed-shell count is `T(N)=28N−4`: arrow `N=69`, `1,928 ≤ 2,432`; circle `N=64`, `1,788 ≤ 2,176`; guard `N=42`, `1,172 ≤ 1,536`. The renderer-facing canonical 4×3 visible-window oracle models eight arrows, two circles, and two guard beats (four shield instances): 14 cue instances, 23,688 triangles, and 42 primitive draw calls, bounded at 25,000/48. Candidate validation checks GLB chunks, no external dependencies, exact AABBs/counts/material roles, cap ordering and widths, circle circularity/radii, geometric manifold/Euler/connectedness, opposite edge winding, positive volume, explicit normal agreement, immutable predecessor Git trees, and exact four-role source/GLB identity. Adversarial tests reverse winding and corrupt tint/culling/dependency metadata; clean Blender smoke opens all three sources and GLBs.

The finalized `0.0.5` raw release contains exactly 17 files / 45,819 bytes with tree digest `24f6bb3b86657716ed03958a32dee5c9db3904aa980cb0a839aacac0590cc860`, inventory SHA-256 `4984cca24b8121bc6657153304726f1f7ef05d878ca5220f3c3e2b6f2457a102`, and proof SHA-256 `4aac2274a9803a05e9ff533c02958cf1c5def66e0af1bf2fae3cc4479319f350`. Its wall GLB is 3,692 bytes with SHA-256 `1227bfbb7d5379b33f1468c1a0d7fffad07c9390654b54033f079ba602a84a37`. Review `0.0.5` contains 13 RGB `1600 × 900` PNGs plus five JSON evidence files.

The finalized `0.0.6` raw release contains exactly 17 files / 49,337 bytes with tree digest `d46ef42fdb0b2b743acbc0fabf87e7ae8a24bb5f7a8af729b43d09bba09306e3`, inventory SHA-256 `4f45b1bf59c309b5d691d9bc0c03d737c9139d24963bec85c7055f82de1137d1`, and proof SHA-256 `d2c34e428b4db758db8cd06eac9dfb832f1b5b8a6b6545a0ea6da6bc20853899`. Its rejected marker GLB is 5,496 bytes / 168 inward-wound triangles with SHA-256 `bd7a1523eb62c6ba0cb0f1f19c69b8b2cecc7edc31d05b1cad55138ab86da145`. Review `0.0.6` contains 23 RGB `1600 × 900` PNGs plus five JSON evidence files and remains immutable.

The finalized `0.0.7` raw release contains exactly 17 files / 49,515 bytes with tree digest `d7ed901aaff35295d25a1d79ca5caa243c3ade848b1a2dc22d664f4d1f3b8f28`, inventory SHA-256 `ba3f40ad3b178da9845a74c89d3a89115d13fa5bd86b291bf41031df70eabbf4`, and proof SHA-256 `ebeb42ffaa351bcdbd7ae8120b62762d16d8957acd8a4b1286b324ffa5e6cfdb`. Its marker GLB is 5,496 bytes / 168 outward-CCW triangles with SHA-256 `b2316b8ec013e9d9087a0bd6d9e5dcef643a34132f9c51fc2526c68d317f7530`; geometric winding dot-centroid values range from `0.00005337978711546069` to `0.000139488119914183`, and 504 geometric-face/explicit-NORMAL dots range from `0.9485757794242599` to `0.9794479653887043`. Review `0.0.7` contains 23 culling-enabled RGB `1600 × 900` PNGs plus five JSON evidence files.

## Coordinates and consumption

Right-handed, **+Y up**, gameplay/local forward **−Z**. Assets are authored at identity rotation and unit scale with the specification-defined pivot. Consumers may independently mix variants through a set manifest and own runtime placement, role colors, direction rotation, timing tint, interval scaling, transparent sorting, outline passes, lane/row visuals, instancing, and world text. `guard/outlined-shield-v1` is the staged canonical model that consumers instance twice; immutable releases through `0.0.7` retain `guard/shield-v1`.

## Rights

All geometry, materials, scripts, and renders are original locally authored AeroBeat/Gambit Games work made only from procedural primitives. No third-party content is included. Licensed under CC BY-NC 4.0; see `LICENSE.md`.
