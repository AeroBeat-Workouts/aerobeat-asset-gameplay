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
- `release/raw/0.0.7/` — immutable marker winding/culling predecessor: the complete seven-asset shape with only `athlete-marker/sphere-v1` re-authored.
- `release/raw/0.0.8/` — immutable Aero Rounded predecessor: three rounded/two-sided outlined cue identities plus four byte-identical `0.0.7` roles.
- `release/raw/0.0.9/` — immutable uniform-arrow repair successor: the directional arrow uses one analytic signed-offset family; the other six GLBs remain byte-identical to `0.0.8`.
- `0.0.10` is the prepared uniform-wall successor only. Until independent source QA/audit authorizes the one-shot builder, no canonical `release/raw/0.0.10/` or `review/0.0.10/` may exist.
- `review/<version>/` — Blender-rendered visual evidence, calculated containment/contrast/wall-grid metadata, and hashes outside runtime releases; `review/0.0.1/` through `review/0.0.9/` are immutable after finalization.
- `tools/` — locally authored Blender/Python generation, export, review, and strict validation scripts.

After a release validates, do not mutate it. Corrections require a new release version.

## Commands

Requires Blender `4.0.2` and Python 3.

```bash
# Immutable predecessor remains independently valid.
python3 tools/validate.py --root . --release 0.0.7
python3 tools/test_subprocess_contract.py --root .

# Prepared 0.0.9 candidate validation; CANDIDATE is an isolated disposable root.
python3 tools/validate_rounded_candidate.py --authority-root . --candidate-root "$CANDIDATE" --canonical --smoke
python3 tools/test_uniform_arrow.py --authority-root . --candidate-root "$CANDIDATE"
python3 tools/test_rounded_adversarial.py --candidate-root "$CANDIDATE"
python3 tools/test_rounded_release_preflight.py --root . --candidate-root "$CANDIDATE"
python3 tools/test_visible_window_budget.py

# Generates two isolated 0.0.9 candidates, compares all 17 raw and 73 review files,
# verifies the semantic arrow fingerprint, preserves predecessors, and removes temps.
python3 tools/reproducibility_rounded.py --root .

# The one-shot canonical driver is armed release tooling, not a rebuild command.
# The prior authorization was consumed by the recorded argparse failure; do not invoke it
# without a new explicit audited authorization. Preparation and QA create no canonical target.
```

## Aero Rounded successor

The mutable source tree and manifests retain the approved Alternative B identities `directional-arrow/rounded-outline-v1`, `any-note/outlined-circle-v1`, and the sole canonical two-instance guard `guard/outlined-shield-v1`. Canonical `release/raw/0.0.8` and `review/0.0.8` were built exactly once from approved source commit `ea776074ef3731c3090c3816f161c4ea95c22ddb` / tree `b354d02f0b8efbbcf8851d8600d01f8dda543985` after independent QA/audit authorization. The one-shot driver generated in an isolated staging root so the approved source snapshots remained unchanged, copied bomb/wall/track/athlete-marker from immutable `0.0.7`, validated before promotion, and refuses every existing canonical or recovery-staging path.

Each changed cue is one closed connected geometric two-manifold with outward consistent winding, explicit per-corner normals, three 30-degree axial bevel segments per face, and an opaque two-sided projected `charcoal → white → charcoal → fill` surface. The outer charcoal keyline includes the face bevel: circle projected radii remain exactly `0.350 / 0.336 / 0.284 / 0.264`. Only arrow/any `note_fill` advertises `runtimeTintable:true`; guard `guard_fill`, `outline_white`, and `outline_charcoal` are fixed. Because the `0.086` band stack crosses the medial axis of the specified small convex outer fillets, arrow/guard independently erode their seven-anchor polygons and re-round each surviving/collapsed join; straight runs retain exact nominal widths and joins may widen but never narrow (within tessellation chord tolerance). The arrow shaft half-width is `.175`, yielding a `.178` fill shaft. Its corrected deterministic readability bounds are `≥35%` colored fill and `≥48%` interior after the white stroke; the circle remains exactly concentric.

The exact closed-shell count is `T(N)=28N−4`: arrow `N=69`, `1,928 ≤ 2,432`; circle `N=64`, `1,788 ≤ 2,176`; guard `N=42`, `1,172 ≤ 1,536`. The renderer-facing canonical 4×3 visible-window oracle models eight arrows, two circles, and two guard beats (four shield instances): 14 cue instances, 23,688 triangles, and 42 primitive draw calls, bounded at 25,000/48. Candidate validation checks GLB chunks, no external dependencies, exact AABBs/counts/material roles, cap ordering and widths, circle circularity/radii, geometric manifold/Euler/connectedness, opposite edge winding, positive volume, explicit normal agreement, immutable predecessor Git trees, and exact four-role source/GLB identity. Adversarial tests reverse winding and corrupt tint/culling/dependency metadata; clean Blender smoke opens all three sources and GLBs.

### Staged uniform-arrow repair proof

The mutable directional-arrow source repair originated at `ff34f05f376e57d425430afc2520c0512a53ab73` / tree `339dd8031184d11bf20272a40353c022df71d8b4`. Prepared successor `0.0.9` generation inputs are pinned independently at commit `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / tree `fe3938e85227d6ea045e8da7330e48cb749c6360`; the authority scope is exact `tools/generate.py`, `source/`, `manifests/`, `sets/`, and `LICENSE.md`. The generator accepts only `0.0.9`, stages predecessor raw `0.0.8`, requires its exact source commit/tree identity in proof, and strips nondeterministic ancillary PNG metadata so all 73 review files reproduce byte-for-byte. The arrow contract remains exclusively `fill-first-analytic-rounded-signed-offsets` with levels `0 / 0.020 / 0.072 / 0.086` and no radius clamps or independently re-rounded joins. The superseded arrow morphology contract is rejected; guard retains its separate approved morphology contract.

Blender `4.0.2` may embed nondeterministic save/container metadata, so raw `.blend` byte equality is neither claimed nor used to compare the staged and isolated arrow source. `tools/blender_scene_fingerprint.py` instead serializes scene, collection, object transform/visibility/parenting, mesh vertex/edge/loop/polygon/triangle/material-slot and custom-normal presence, material/node graph, world, action, and custom-property semantics into canonical JSON. Blender-recalculated load-time vertex/loop normal values alone are excluded because repeated opens demonstrate scheduling-dependent low-bit drift; authored coordinates and custom-normal presence stay exact, while generated GLB normal bytes stay exact. Tests require an exact SHA-256/document match for staged versus each isolated source. Generated evidence is stricter: every file in both isolated `release/raw/0.0.9` and `review/0.0.9` inventories must match byte-for-byte, including the arrow GLB, inventory/proof manifests, normalized PNGs, and review hashes.

`tools/test_uniform_arrow.py` uses both minimum- and maximum-width probes for every straight/concave/convex/tip feature instead of selecting a best nominal probe. Every probe runs across eight rotations, three contrast-checked fill colors, three scales, and DPR `1/2/3`. Deterministic coverage sampling is capped at `0.00025` world units and every measured band uses the fixed `0.002` tolerance, seven times narrower than the narrowest `0.014` band. Immutable `0.0.8` and all three targeted shoulder-bulge raster fixtures must fail. This originated as staged repair evidence: raw/review `0.0.1`–`0.0.8` remain immutable, and finalized `0.0.9` records the authorized canonical result.

Prepared `0.0.9` authority was established with two independent isolated generations matching all 17 raw files and all 73 review files byte-for-byte. The one freshly authorized canonical builder invocation then reproduced those exact audited bytes from final audit authority commit/tree `80378c51b167c329f4c0df4a81510fcd4fe28e6b` / `27f0caafa3928476b917631f9e3319f6c0b3aa89` with generation count `1`. Final raw is 17 files / 429,209 bytes with tree digest `979a202bf06d99ebc53588668d67e9d50df7bcd14e9b0d4e69c6dd73b09f9a00`, inventory SHA-256 `95ec22c1657d4931e42327e0544b86f782075288a3330a4d23b0fed07dce65fa`, and proof SHA-256 `e1726ca2bc3a0980cc86ba6184bf7da57079f7ee1e42e24094c47196a3dbace9`. Final review is 73 files / 77,797,749 bytes with tree digest `009d21bd09b9015a3f7f9629b96122e3f462875c9a5a3ef87aab578c872b9abc` and hashes-manifest SHA-256 `8a7155bbd9a7878eaac37cb1a51eddc21bfb8ab861bf16e65b6d6b0b6b43d282`. Arrow GLB is 152,916 bytes / `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4`; staged and canonical arrow scenes share semantic fingerprint `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11`. Proof source identity is exactly prepared commit/tree `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / `fe3938e85227d6ea045e8da7330e48cb749c6360`. Canonical raw/review directories are finalized read-only at directory/file modes `0555` / `0444`; all 16 predecessor Git trees remain exact.

### Prepared uniform-wall successor

`0.0.10` re-authors only `wall/red-glass-v1`. The physical dark rails and wedges came from the predecessor's separate 96-triangle `mat/red_edge` cage at alpha `0.82` over its 12-triangle alpha-`0.24` body. The prepared source is one closed 12-triangle / eight-welded-vertex box, one `mat/red_glass` primitive, one alpha `0.24`, exact `0.94 × 0.94 × 1.0` bounds and centered pivot. It has no edge cage, secondary material, texture, external dependency, runtime override, or transparent depth write. Its true geometric boundary retains the silhouette while removing high-opacity internal/top/bottom/side rails across interval scaling.

The candidate generator copies the other six GLBs and release manifests byte-for-byte from immutable `0.0.9`. Review evidence adds fifteen wall views spanning five camera directions and dark/bright/blue backgrounds, plus the existing gameplay-context and one/three-cell wall-grid proofs. `tools/validate_uniform_wall_candidate.py` requires one primitive/material, exact explicit-normal topology/bounds/alpha, closed welded topology, wall-only release proof, six-role byte identity, 17 raw files, and 83 review PNGs with hash binding. `tools/test_uniform_wall.py` rejects a second primitive, edge material, alpha `0.82`, transparent depth write, and the immutable `0.0.9` edge-cage wall. `tools/reproducibility_uniform_wall.py` is candidate-only and requires two clean isolated raw/review trees to match byte-for-byte plus three identical semantic Blender source fingerprints.

No canonical `0.0.10` build is authorized by source preparation or candidate QA. The exact source authority commit/tree, audited candidate hashes, and one-shot builder authorization must be recorded before the canonical invocation.

The finalized `0.0.5` raw release contains exactly 17 files / 45,819 bytes with tree digest `24f6bb3b86657716ed03958a32dee5c9db3904aa980cb0a839aacac0590cc860`, inventory SHA-256 `4984cca24b8121bc6657153304726f1f7ef05d878ca5220f3c3e2b6f2457a102`, and proof SHA-256 `4aac2274a9803a05e9ff533c02958cf1c5def66e0af1bf2fae3cc4479319f350`. Its wall GLB is 3,692 bytes with SHA-256 `1227bfbb7d5379b33f1468c1a0d7fffad07c9390654b54033f079ba602a84a37`. Review `0.0.5` contains 13 RGB `1600 × 900` PNGs plus five JSON evidence files.

The finalized `0.0.6` raw release contains exactly 17 files / 49,337 bytes with tree digest `d46ef42fdb0b2b743acbc0fabf87e7ae8a24bb5f7a8af729b43d09bba09306e3`, inventory SHA-256 `4f45b1bf59c309b5d691d9bc0c03d737c9139d24963bec85c7055f82de1137d1`, and proof SHA-256 `d2c34e428b4db758db8cd06eac9dfb832f1b5b8a6b6545a0ea6da6bc20853899`. Its rejected marker GLB is 5,496 bytes / 168 inward-wound triangles with SHA-256 `bd7a1523eb62c6ba0cb0f1f19c69b8b2cecc7edc31d05b1cad55138ab86da145`. Review `0.0.6` contains 23 RGB `1600 × 900` PNGs plus five JSON evidence files and remains immutable.

The finalized `0.0.7` raw release contains exactly 17 files / 49,515 bytes with tree digest `d7ed901aaff35295d25a1d79ca5caa243c3ade848b1a2dc22d664f4d1f3b8f28`, inventory SHA-256 `ba3f40ad3b178da9845a74c89d3a89115d13fa5bd86b291bf41031df70eabbf4`, and proof SHA-256 `ebeb42ffaa351bcdbd7ae8120b62762d16d8957acd8a4b1286b324ffa5e6cfdb`. Its marker GLB is 5,496 bytes / 168 outward-CCW triangles with SHA-256 `b2316b8ec013e9d9087a0bd6d9e5dcef643a34132f9c51fc2526c68d317f7530`; geometric winding dot-centroid values range from `0.00005337978711546069` to `0.000139488119914183`, and 504 geometric-face/explicit-NORMAL dots range from `0.9485757794242599` to `0.9794479653887043`. Review `0.0.7` contains 23 culling-enabled RGB `1600 × 900` PNGs plus five JSON evidence files.

The finalized `0.0.8` raw release contains exactly 17 files / 429,026 bytes with tree digest `0c2dcf8f00183ac9b33efa1c59c3d2a217687903127b86eb325372671279c549`, inventory SHA-256 `ac30d6b70cbae96115a7c97f5ad02b3da21fde7fb77f69083f1090e268bab5ac`, and proof SHA-256 `ba8a52cf747ec5ab58dcd024c90f813a5c477541892f71da698ead6a65ca4758`. Review `0.0.8` contains 68 RGB `1600 × 900` PNGs plus five JSON evidence files: 73 files / 77,758,435 bytes with tree digest `a9ef1d2c98623c0f75bdb680388be6503664b99ff39b3c67ddf85cdaaefae2c1` and hashes-manifest SHA-256 `37ac9db1d94e8425ea8ba235f0c3cf465e3a49f3cb349f3b9e0b8ea39b4d630b`. Both trees are finalized read-only; corrections require a new version.

## Coordinates and consumption

Right-handed, **+Y up**, gameplay/local forward **−Z**. Assets are authored at identity rotation and unit scale with the specification-defined pivot. Consumers may independently mix variants through a set manifest and own runtime placement, role colors, direction rotation, timing tint, interval scaling, transparent sorting, outline passes, lane/row visuals, instancing, and world text. `guard/outlined-shield-v1` is the `0.0.8` canonical model that consumers instance twice; immutable releases through `0.0.7` retain `guard/shield-v1`.

## Rights

All geometry, materials, scripts, and renders are original locally authored AeroBeat/Gambit Games work made only from procedural primitives. No third-party content is included. Licensed under CC BY-NC 4.0; see `LICENSE.md`.
