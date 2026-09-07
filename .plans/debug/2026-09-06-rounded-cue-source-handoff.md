# Rounded gameplay cue creator-source handoff

**Date:** 2026-09-06
**Bead:** `aerobeat-web-assembly-7drd`
**State:** creator source ready for independent QA/audit; no asset `0.0.8` release/review tree exists

## Corrected budget derivation

For `N` corresponding perimeter samples, both caps contain six physical annuli (`12N`) and two fill polygons (`2N−4`); both three-segment bevels contribute `12N`; the central side contributes `2N`. Therefore `T(N)=28N−4`.

A filleted polygon corner using `s` arc segments contributes `s+1` distinct perimeter vertices because a straight tangent run separates adjacent corners. Deterministic counts and smallest 128-rounded ceilings retaining at least 20% headroom are:

| Cue | Arc segments | N | Exact triangles | Ceiling |
|---|---:|---:|---:|---:|
| Arrow | 62 | 69 | 1,928 | 2,432 |
| Circle | closed 64-sample analytic circle | 64 | 1,788 | 2,176 |
| Guard | 35 | 42 | 1,172 | 1,536 |

All ceilings are below the hard 4,096-triangle per-cue limit. The renderer-facing canonical 4×3 visible-window oracle uses eight arrows, two any-notes, and two guard beats (four shield instances): 12 target records, 14 cue instances, 23,688 triangles, and 42 primitive draw calls, bounded by 25,000 triangles / 48 calls.

## Geometry and material resolution

The conventional axial bevel begins at silhouette offset `0` and reaches its planar cap at `.012` for arrow/circle or `.010` for guard. Material boundaries remain silhouette-relative `.014/.066/.086`, preserving the circle's required projected radii `.350/.336/.284/.264`. The outer charcoal keyline therefore wraps the full bevel and continues `.002` on the arrow/circle planar cap or `.004` on the guard cap. Cross-section order is exactly `outline_charcoal → outline_white → outline_charcoal → fill` on both `+Z` and `−Z`; the central side is charcoal.

The `.086` stack crosses the medial axis of the specified small convex polygon fillets. Arrow and guard therefore construct every boundary from an independently eroded seven-anchor polygon and apply semantic tangent re-rounds after collapsed negative-radius features are removed. The outer silhouette/radii remain unchanged; surviving straight runs retain exact `.014/.052/.020` normal widths, while high-curvature joins may widen but never narrow within `.00015` tessellation distance tolerance. Arrow shaft half-width `.175` yields exact `.178` fill width. Its colored fill is `35.59%` of the outer face and the interior readability footprint after white is `49.06%`, exceeding corrected transparent bounds `35%/42%`; its fill tip remains radius `.045`. The analytic circle remains exactly concentric and does not use this topology transition.

Changed GLBs split corners only at export for explicit hard normals; geometric-position welding proves one connected closed genus-zero manifold. Editable Blender sources retain one welded mesh. Every material is analytic alpha-1 `OPAQUE`, back-culled, depth-tested, and depth-writing. Arrow/any `note_fill` alone is runtime tintable; guard fill and all structural bands are fixed.

## Mutable creator outputs

- `source/directional-arrow/rounded-outline-v1/rounded-outline-v1.blend`
- `source/any-note/outlined-circle-v1/outlined-circle-v1.blend`
- `source/guard/outlined-shield-v1/outlined-shield-v1.blend`
- matching strict manifests under `manifests/`
- staged `sets/default-v1.json`
- generator, smoke validators, rounded candidate validator, adversarial suite, reproducibility runner, and visible-window oracle under `tools/`

Bomb, wall, track, and athlete-marker selected editable sources and generated candidate GLBs are byte-identical to `0.0.7`. All immutable raw/review paths `0.0.1–0.0.7` remain untouched.

## Validation evidence

- immutable `0.0.7` strict validator: PASS, including clean Blender smoke
- subprocess/adversarial baseline suite: PASS
- disposable rounded candidate: PASS at exact `1928/1788/1172` triangles, Euler `2`, positive volume, opposite directed-edge pairing, explicit-normal minimum dot effectively `1.0`, exact materials and no external dependencies
- 13 rounded adversarial mutations/checks: PASS (reversed/count-drift triangles, structural tint, double-sided material, dependency, naive negative radius, self-intersection, narrowed straight/join band, join widening acceptance, disconnected fill, tip radius, area, symmetry)
- source/GLB clean Blender smoke: PASS for all three changed identities
- renderer-visible-window oracle: PASS (`23,688/25,000`, `42/48`)
- two independent disposable raw candidates: byte-identical; canonical release absent
- 68 disposable `1600×900` Blender renders: required `+Z`, `−Z`, `+X`, and both three-quarter camera sides on dark/bright/blue for each changed cue, plus package boards and existing marker evidence

CSS-size/DPR actual-pixel checks are renderer/integration QA rather than an engine-neutral Blender-source capability and remain for independent QA. No evidence image is committed.

## Proposed release contents after independent authorization

Exactly 17 files: seven selected GLBs, seven copied per-asset release manifests, `sets/default-v1.json`, `inventory.v1.json`, and `proof.v1.json`. Changed identities are the three rounded cues; unchanged identities are bomb, wall, track, and athlete-marker. Neither creator nor auditor should create the immutable release before QA/audit authorization.
