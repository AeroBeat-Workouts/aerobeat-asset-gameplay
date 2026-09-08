# Uniform rounded directional-arrow keyline diagnosis

## Exact Observed Failure

Derrick's physical review of securely served web raw `0.0.43` reports that the directional arrow's inner charcoal keyline is visibly uneven at the concave shoulders and near the tips. The immutable gameplay asset embedded there is raw `0.0.8`.

Independent geometric measurement of `release/raw/0.0.8/directional-arrow/rounded-outline-v1.glb` reproduces the variation. Minimum/maximum nearest-boundary widths are:

| band | nominal | minimum | maximum | spread |
|---|---:|---:|---:|---:|
| outer charcoal | 0.014 | 0.013931742 | 0.025597973 | 0.011666231 |
| white | 0.052 | 0.051999920 | 0.078095418 | 0.026095499 |
| inner charcoal | 0.020 | 0.019999996 | 0.032463000 | 0.012463004 |

The maxima occur around the shoulder/neck transition samples (for example white at approximately `(+/-0.114858, 0.115142)` and inner charcoal near `(+/-0.193073, 0.153463)`). This is direct geometric evidence, independent of lighting or antialiasing. Immutable raw/review `0.0.1` through `0.0.8` remain untouched.

## Expected Behavior

The arrow must preserve its DDR-style proportions, `0.78 x 0.78 x 0.18` dimensions, two-sided opaque connected manifold, and face hierarchy `charcoal -> white -> charcoal -> note_fill`, while every exterior/interior boundary is a genuine signed offset of one rounded contour family. Nominal level differences must be `0.014 / 0.052 / 0.020`; rotations, colors, scales, and DPRs must not create a locally swollen shoulder/tip keyline. Colored fill remains at least 35% and total interior after the white stroke at least 48%. Circle, guard, bomb, wall, track, athlete marker, immutable releases, and immutable reviews must remain byte-identical.

## Execution Path

1. `build_rounded_cue("directional-arrow")` asks `solve_arrow_loops()` for bevel and material boundaries.
2. `solve_arrow_loops()` starts from one seven-anchor outer polygon.
3. `filleted_loops()` independently insets that sharp anchor polygon at every level.
4. It computes every new radius as `max(semantic_floor, outer_radius - offset)` without using the corner's signed turn.
5. `sample_filleted_polygon()` therefore re-rounds each level with a different clamped curve rather than evaluating signed-distance levels of one rounded source contour.
6. `cue_shell()` connects corresponding samples and exports the resulting charcoal/white/charcoal/fill partitions.
7. `validate_rounded_candidate.py` checks only a lower bound on sparse inner-point-to-outer-segment distance. Widening is explicitly accepted and there is no raster-width oracle, so the locally swollen shoulders/tips pass.

## Most Likely Root Cause

The current construction is not a signed offset of a rounded contour. It offsets the seven sharp anchor lines and then independently invents/clamps corner radii. The same `radius - offset` expression is used at convex and concave turns even though signed curvature requires opposite radius evolution. Once offsets exceed the small outer radii, semantic floors deliberately widen joins. That was appropriate for the earlier non-narrowing/readability repair, but it cannot guarantee uniform visual keylines.

Evidence is both source-level and measured: lines 213-223 of `tools/generate.py` apply independent clamped re-rounding, while the immutable GLB shows up to `0.026095499` world-unit white-band spread and `0.012463004` inner-charcoal spread concentrated at the reported features.

## Alternative Hypotheses

1. **Lighting/antialiasing alone** — unlikely. The geometry itself contains the same localized widening before rasterization.
2. **Renderer rotation or Y flip** — contradicted by the same object-space widths and the renderer's authored rotation-only direction mapping.
3. **Circle/guard material hierarchy** — unrelated. The report names the arrow, and the circle is analytic/concentric; changing other assets would add risk without evidence.
4. **Insufficient colored fill** — contradicted by the accepted 35.588% current fill measurement. Readability area is separate from width uniformity.

## Why Previous Fixes Failed

The prior morphological repair correctly eliminated narrowing, restored shaft/tip readability, and reconciled the 35%/48% area contracts. It intentionally allowed joins to widen and validated minima only. Consequently it fixed missing/narrow bands but preserved exactly the width inflation now visible in physical pixels. The stalled replacement child made no repository, asset, process, or commit effect, so there is no later attempted implementation to preserve or retry.

## Unknowns

The exact raster tolerance that remains stable at the smallest supported projected size must be established by the new deterministic raster oracle. Geometry can require tight signed-level agreement; raster checks must allow only quantization-bounded variation across colors, rotations, scales, and DPRs.

## Minimal Reproduction

Load the immutable `0.0.8` arrow GLB, reconstruct the four planar material boundaries, and measure nearest polyline distance at every boundary vertex/midpoint. The table above results. A red-before width-spread oracle with bounds materially below `0.0116 / 0.0261 / 0.0124` rejects the current arrow.

## Proposed Verification

1. Add a red-before fixture proving immutable `0.0.8` fails uniform-width spread at concave and convex feature windows.
2. Generate only disposable candidates from a fill-first rounded contour whose outward signed levels are exactly `0 / 0.020 / 0.072 / 0.086`; derive bevel levels from that same family.
3. Require geometric level widths at straight, concave, convex, tip, and rotated samples.
4. Render deterministic orthographic masks over multiple note colors, directions, scales, and DPR-equivalent resolutions; measure run widths around the same feature classes.
5. Require two disposable builds to reproduce, source and GLB Blender smoke to pass, and manifold/material/pixel contracts to pass.
6. Hash every immutable raw/review tree before and after and byte-compare every non-arrow staged source/manifest.

## Recommended Fix

Define the rounded fill contour first with exact `0.178` shaft width and a `0.045` tip radius. Construct inner-charcoal, outer-white, silhouette, and bevel contours as analytic outward signed offsets of that same rounded seven-anchor family. Choose a positive fill concave radius large enough that the outermost signed offset remains valid, avoiding medial-axis collapse and all semantic radius clamps. Solve only the fill head/tip anchors needed to retain the exact `+/-0.39` outer bounds. Keep the existing 69 samples and shell topology, so the `1,928`-triangle two-sided manifold/material contract remains stable.

## Debugging Record

```text
Problem: Screenshot-visible uneven directional-arrow inner charcoal keyline.
Observed symptom: Immutable 0.0.8 geometric band spreads are 0.011666 outer charcoal, 0.026095 white, and 0.012463 inner charcoal, concentrated at shoulders/tips.
Root cause: Each inset sharp-anchor polygon is independently re-rounded with unsigned radius subtraction and semantic floors; boundaries are not signed-distance levels of one rounded contour.
Evidence: tools/generate.py filleted_loops() construction plus measured immutable GLB widths and feature coordinates.
Failed approaches: Prior non-narrowing morphology intentionally allowed widening; stalled child made zero effects.
Corrective action: Fill-first analytic rounded contour with one outward signed-offset family at levels 0/.020/.072/.086 and matching bevel levels.
Verification test: Red-before immutable oracle, green-after geometric/raster feature matrix, reproducibility, Blender smoke, manifold/material checks, and immutable-tree hashes.
Related files/components: tools/generate.py, new uniform-arrow oracle, staged arrow .blend/manifest, this report.
Remaining uncertainty: Quantization-only raster tolerance, to be fixed by deterministic multi-resolution evidence.
```

## Repair result

The fill-first construction landed exactly as proposed. The fill anchors use shaft half-width `0.089`, bottom `-0.304`, neck Y `0.020`, solved head X `0.3370345104`, and solved tip Y `0.3191711694`. Fill radii are `0.045` tail, `0.095` concave neck, `0.020` convex head shoulder, and `0.045` tip. Outward signed levels `0 / 0.020 / 0.072 / 0.086` generate fill, inner-white boundary, outer-white boundary, and silhouette; all convex radii increase and concave radii decrease by the exact signed level. The outermost concave radius remains positive at `0.009`, so no clamp, collapse, or invented join occurs. Solved candidate bounds remain exact `[-0.39,-0.39,-0.09]..[0.39,0.39,0.09]`.

The red-before/green-after oracle measures:

| band | immutable 0.0.8 min..max / spread | staged candidate min..max / spread |
|---|---|---|
| outer charcoal | `0.013931742..0.025597973 / 0.011666231` | `0.013880243..0.014000078 / 0.000119835` |
| white | `0.051999920..0.078095418 / 0.026095499` | `0.051555088..0.052000000 / 0.000444912` |
| inner charcoal | `0.019999996..0.034352750 / 0.014352754` | `0.019828869..0.020000097 / 0.000171228` |

The small candidate undershoot is the bounded chord error of the retained 69-sample tessellation; every band remains within `0.00050` of its analytic signed level. Spread is reduced by `98.97%` outer-charcoal, `98.30%` white, and `98.81%` inner-charcoal. Colored fill is `0.4541180171 >= 0.35`; total interior is `0.5693474204 >= 0.48`; straight fill shaft remains exact `0.178`; fill tip remains `0.045`.

`tools/test_uniform_arrow.py` proves immutable red-before rejection and candidate green-after across straight shaft, concave shoulder, convex shoulder, and tip windows; eight rotations, three fill colors, three scales, and DPR `1/2/3`; `2,592` deterministic four-sample antialiased raster checks; and three targeted shoulder-bulge adversaries. The existing 14 rounded adversaries also pass.

Candidate topology remains 69 samples / 1,928 triangles, Euler `2`, one connected closed two-manifold, positive signed volume `0.0633066764`, opposite edge winding, and minimum explicit-normal dot `0.999999999996`. All three rounded staged sources and candidate GLBs pass Blender `4.0.2` smoke; circle and guard retain their existing `1,788 / 1,172` triangles and geometry/material validation. Two disposable generations reproduce all 17 runtime candidate files byte-for-byte; each also produces 73 review evidence files. Blender `.blend` and rendered PNG container bytes remain outside determinism claims, consistent with the established repository contract.

Staged arrow source SHA-256 is `8d3dd7fbc940de442b57bbadd5f471ed95c85195fcbce04b0664bd59386127c2` (`561,492` bytes); staged manifest SHA-256 is `98cb5aab2719892e3a018a57869fce364961ff0d66b40d01e0f4e05447ed8c7a`; isolated candidate GLB SHA-256 is `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4` (`152,916` bytes). Only the staged arrow `.blend`/manifest change among source/manifest asset identities. Six non-arrow candidate GLBs are byte-identical to immutable `0.0.8`; circle, guard, bomb, wall, track, and athlete-marker staged assets remain unchanged.

Immutable raw/review `0.0.1` through `0.0.8` pass a before/after 16-tree path/size/SHA inventory comparison. Canonical `0.0.8` remains exact: raw Git tree `e26ec4e8278860c60568bd2a89983cd09555ee75`, 17 files / 429,026 bytes, inventory `ac30d6b70cbae96115a7c97f5ad02b3da21fde7fb77f69083f1090e268bab5ac`, proof `ba8a52cf747ec5ab58dcd024c90f813a5c477541892f71da698ead6a65ca4758`; review Git tree `df080ea57c99bb50697f14e891edad7f53dbda2a`, 73 files / 77,758,435 bytes. No canonical build driver ran and no permanent successor path was created.

## QA repair diagnosis (t6ty)

### Exact Observed Failure

Independent QA at source commit `ff34f05f376e57d425430afc2520c0512a53ab73` / tree `339dd8031184d11bf20272a40353c022df71d8b4` observed four blockers. The default uniform-arrow test rejects staged/generated `.blend` byte drift (`8d3dd7…` staged versus `694882…` isolated) even though dense geometry passes. Canonical candidate validation stops at `authorized generation inputs differ from approved authority`. If that check is bypassed, validator line 286 still requires `independent-inset-anchor-morphological-erosion` for the arrow. Finally, the raster oracle chooses the single probe nearest nominal per feature, classifies material labels independently of fill RGB, and permits up to `1.55*pitch+.0005` (`0.0256875` at the coarsest case), wider than the `0.014` outer band.

### Expected Behavior

Blender container metadata may vary without changing the authored scene. Staged and isolated sources therefore need an exact deterministic semantic scene fingerprint over scene/object/mesh/material/custom-property state, while generated runtime GLB and inventory bytes remain exact. Generation inputs must be pinned to the repaired authority above. Directional-arrow validation must require the fill-first signed-offset contract and reject its superseded morphology contract, while guard retains its independently approved morphology. Raster QA must exercise worst-case probes for every feature across every rotation/color/scale/DPR combination, use colors with explicit contrast, enforce a fixed world-space tolerance materially below `0.014`, and reject immutable and synthetic red fixtures.

### Execution Path

`generate.py` writes a semantically stable Blender scene but Blender serializes nondeterministic container metadata; `test_uniform_arrow.py` compares those raw bytes before inspecting semantics. `validate_rounded_candidate.py` still pins the original `ea7760…` generation authority and applies one morphology assertion to both arrow and guard. `raster_matrix()` then selects only the closest-to-target boundary point in each feature and accepts a pitch-scaled error larger than the narrowest band.

### Most Likely Root Cause

The proof layers were not revised with the geometry model. A byte-level source proxy, original-release authority pin, shared arrow/guard morphology assertion, and best-case pixel heuristic survived after the arrow changed to a fill-first signed-offset family. QA evidence directly identifies each stale assumption; the passing dense geometry and runtime reproducibility contradict a geometry-generation defect.

### Alternative Hypotheses

1. The staged source contains a semantic difference: possible until a scene fingerprint compares all relevant Blender semantics, but contradicted by identical generated GLB bytes and dense contour measurements.
2. The authority failure indicates dirty generation inputs: contradicted by the clean `ff34f05…` repair commit/tree; the validator literal still names the older approved commit.
3. The old morphology contract is harmless prose: contradicted by executable line 286.
4. Coarse raster tolerance is unavoidable: contradicted by deterministic subpixel coverage, which can bound world-space quantization well below `0.014`.

### Why Previous Fixes Failed

The first repair correctly changed geometry and added red/green measurements, but reused proof mechanisms designed for raw Blender byte identity, original `0.0.8` generation, morphology-only joins, and one representative raster sample. Those mechanisms either reject valid semantics or overstate raster coverage.

### Unknowns

The final semantic fingerprint and worst-case raster tolerance must be measured against two fresh Blender builds. The tolerance must remain above deterministic sampling/chord error yet below the `0.014` band and must reject the immutable/bulged fixtures.

### Minimal Reproduction

Generate one isolated candidate from `ff34f05…`; run `test_uniform_arrow.py` without `--skip-staged-match`, then run `validate_rounded_candidate.py --canonical --smoke`. Inspect line 286 and the `raster_matrix()` probe/tolerance logic. These reproduce all four blockers without mutating a canonical release.

### Proposed Verification

Compare canonical semantic fingerprint JSON/SHA for staged and two isolated arrow sources; byte-compare both generated raw inventories; require the exact repaired commit/tree authority; assert arrow signed-offset metadata and explicit old-contract rejection; run every min/max feature probe through all matrix dimensions with a fixed sub-band tolerance; require immutable `0.0.8` and each targeted bulge fixture to fail; then run all requested smoke, manifold, material, readability, adversarial, immutable, and reproducibility gates.

### Recommended Fix

Add a Blender-backed semantic scene fingerprint, replace raw staged-source equality with exact fingerprint equality, update the authority constants to `ff34f05…` / `339dd8…`, split arrow signed-offset and guard morphology validation with an explicit old-arrow rejection, and replace best-probe raster checking with min/max worst-case probes, meaningful color contrast assertions, deterministic fine subpixel coverage, and a fixed tolerance below `0.014`.

### Debugging Record

```text
Problem: Rounded-arrow proof authorities lag the repaired signed-offset source.
Observed symptom: Raw Blend mismatch, stale authority rejection, stale morphology assertion, and best-case raster tolerance up to 0.0256875.
Root cause: Proof mechanisms retained assumptions from the original rounded release and morphology repair.
Evidence: Exact wv25 QA FAIL comment plus current test/validator source at ff34f05.
Failed approaches: Raw Blender-byte source equality and representative-probe pitch-scaled raster acceptance.
Corrective action: Semantic scene fingerprint, repaired authority pin, signed-offset contract, and fixed-tolerance worst-case raster matrix.
Verification test: Default no-skip test, canonical smoke validation, two isolated builds, Blender smokes, adversarial/red fixtures, immutable inventories.
Related files/components: tools/test_uniform_arrow.py, tools/reproducibility_uniform_arrow.py, tools/validate_rounded_candidate.py, new Blender fingerprint tool, README/debug report.
Remaining uncertainty: Measured fingerprint SHA and tight raster tolerance, resolved by fresh builds.
```

## t6ty repair result

All four QA blockers are closed in staged tooling without changing any asset geometry or immutable raw/review tree.

1. **Semantic source determinism:** `tools/blender_scene_fingerprint.py` canonicalizes scene/collection/object transforms and ownership, exact mesh coordinates/topology/material assignment/custom-normal presence, materials and node graphs, worlds, actions, and custom properties. Blender-recalculated load-time vertex/loop normal values are deliberately excluded after repeated opens demonstrated low-bit scheduling drift; generated GLB normal bytes remain exact and are independently validated. The staged source and both isolated builds produce exact semantic fingerprint SHA-256 `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11`. Raw `.blend` hashes are not asserted. Both isolated 17-file runtime inventories match byte-for-byte; arrow GLB remains `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4`, repaired inventory is `367d5efee059144175c118df905b37cfe510a8b6ef42b727928d9494108c6e73`, and repaired proof is `ba0c00d5497a73a24281e5bad25b2c305b676e710c871434cf8b28b2b58190db`.
2. **Generation-input authority:** candidate validation now pins exact repaired authority commit `ff34f05f376e57d425430afc2520c0512a53ab73` / tree `339dd8031184d11bf20272a40353c022df71d8b4` and fails if `tools/generate.py`, `source/`, `manifests/`, `sets/`, or `LICENSE.md` differ.
3. **Signed-offset contract:** directional-arrow validation exclusively requires `fill-first-analytic-rounded-signed-offsets`, levels `[0,.020,.072,.086]`, and the no-clamp single-family join policy. A dedicated red fixture proves the superseded arrow morphology contract rejects. Guard retains its separate morphology assertion.
4. **Worst-case raster oracle:** each of three bands now contributes minimum and maximum probes for all four feature classes (`24` probes). Every probe runs through eight rotations, three explicitly contrast-checked RGB fills, three scales, and DPR `1/2/3`, for `5,184` green checks. Coverage step is at most `0.00025`; fixed acceptance tolerance is `0.002`, seven times below the `0.014` narrowest band. Immutable `0.0.8` fails both geometry and raster red-before checks, and each of three `0.004` shoulder-bulge fixtures fails both geometry and raster.

Final staged measurements remain outer charcoal `0.013880243..0.014000078`, white `0.051555088..0.052000000`, and inner charcoal `0.019828869..0.020000097`; raster range is `0.013750000..0.052177734`. Fill/interior readability remain `45.4118017% / 56.9347420%`. Topology remains 69 samples, 1,928 triangles, Euler 2, one closed connected two-manifold, signed volume `0.0633066764`, and minimum explicit-normal dot `0.999999999996`.

Passing gates: Python compile; default `test_uniform_arrow.py` with no skips; `validate_rounded_candidate.py --canonical --smoke`; two-isolated-build `reproducibility_uniform_arrow.py`; all three staged source and three candidate GLB Blender 4.0.2 smokes; 14 rounded adversaries plus three raster/geometry bulges and the old-contract red fixture; immutable `validate.py --release 0.0.7`; subprocess fatal-signature tests; visible-window budget; diff hygiene; and 16 immutable raw/review before/after inventories. No canonical driver ran, no permanent `0.0.9` exists, and raw/review `0.0.1`–`0.0.8` remain unchanged.

## Independent re-QA result (p6yf)

Independent re-QA at repair commit `04722ee9cb293a3c8103bf7629c7af9086ccb5f9` / tree `559fb6f160f83bca3f2f8d0951714b6f5f52297d` is **PASS**. The repaired proof commit descends from generation-input authority `ff34f05f376e57d425430afc2520c0512a53ab73` / tree `339dd8031184d11bf20272a40353c022df71d8b4`; `git diff --exit-code ff34f05 -- tools/generate.py source manifests sets LICENSE.md` is clean.

All four wv25 blockers are independently closed:

1. The staged source SHA-256 remains `8d3dd7fbc940de442b57bbadd5f471ed95c85195fcbce04b0664bd59386127c2`, while a fresh isolated Blender container has a deliberately different SHA-256 `11bcc5789594fe7b8ece5b24b6e360b9bf7ad5987fd2ddeff4c3b27eb774d263`. The stronger staged/isolated scene documents nevertheless match exactly at semantic fingerprint `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11`. The fingerprint covers scene/collection membership, object ownership/transforms/visibility/parenting/modifiers, exact mesh coordinates/topology/loops/polygons/triangulation/material slots/custom-normal presence, UV/color metadata, materials and node graphs, worlds, actions, and custom properties. Only Blender-recalculated load-normal values are excluded. Runtime determinism remains byte-exact: both reproducibility builds have identical 17-file raw inventories.
2. Canonical candidate validation accepts only the exact repaired generation authority above and passed with no authority bypass.
3. Directional-arrow validation requires `fill-first-analytic-rounded-signed-offsets`, levels `[0,.020,.072,.086]`, and the no-clamp single-family join policy. The explicit superseded `independent-inset-anchor-morphological-erosion` mutation was rejected; guard retains its separate morphology contract.
4. The no-skip default oracle exercised both minimum and maximum probes for every band/feature: `24 × 8 rotations × 3 contrast-checked RGB colors × 3 scales × 3 DPRs = 5,184` checks. Fixed tolerance was `0.002`, below the `0.014` narrowest band; immutable `0.0.8` and all three `0.004` bulge mutations rejected in both geometry and raster paths.

Fresh candidate measurements were outer charcoal `0.013880242760794824..0.014000077871569134`, white `0.05155508756992079..0.052000000000000005`, and inner charcoal `0.019828869049757298..0.020000096786326922`; raster range was `0.01375..0.052177734375`. Colored fill/interior readability were `0.454118017050853 / 0.5693474203797928`. Arrow topology was 69 samples / 1,928 triangles, Euler 2, one closed connected two-manifold, signed volume `0.06330667638182519`, and minimum explicit-normal dot `0.9999999999962325`.

Exact fresh runtime hashes were arrow GLB `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4`, inventory `367d5efee059144175c118df905b37cfe510a8b6ef42b727928d9494108c6e73`, and proof `ba0c00d5497a73a24281e5bad25b2c305b676e710c871434cf8b28b2b58190db`. `validate_rounded_candidate.py --canonical --smoke` passed all three source and three GLB Blender 4.0.2 smokes plus topology/material/readability/release/review gates. `reproducibility_uniform_arrow.py` passed two independent builds, exact 17-file raw byte comparison, 73 review evidence files per build, 16 immutable-tree checks, and the exact semantic fingerprint above. Supplemental PASS gates were Python compilation, `validate.py --release 0.0.7`, 14 rounded adversaries, three bulge adversaries, the old-contract red fixture, subprocess fatal-signature tests, and the visible-window budget (`12` records, `14` instances, `23,688` triangles, `42` draw calls).

Immutable canonical `0.0.8` remains raw Git tree `e26ec4e8278860c60568bd2a89983cd09555ee75` with inventory/proof `ac30d6b70cbae96115a7c97f5ad02b3da21fde7fb77f69083f1090e268bab5ac` / `ba8a52cf747ec5ab58dcd024c90f813a5c477541892f71da698ead6a65ca4758`, and review Git tree `df080ea57c99bb50697f14e891edad7f53dbda2a`. Independent before/after inventories for all 16 raw/review trees `0.0.1`–`0.0.8` matched exactly. No canonical build driver ran, no permanent `0.0.9` path was created, and all disposable candidate directories were removed.

## Final independent readiness audit (k284)

**PASS.** The audited linear asset chain is source repair `ff34f05f376e57d425430afc2520c0512a53ab73` / tree `339dd8031184d11bf20272a40353c022df71d8b4`, proof repair `04722ee9cb293a3c8103bf7629c7af9086ccb5f9` / tree `559fb6f160f83bca3f2f8d0951714b6f5f52297d`, and independent re-QA evidence `cdb7fa871761caef7eae6cbebf49c09a3925612f` / tree `5c20222d0334792fff45f85aa96e811099638ce3`. Local `main`, `origin/main`, and `HEAD` matched the re-QA evidence commit before this documentation-only audit; the three commits are direct descendants in the stated order and their scopes match the report.

Source inspection confirms that the directional arrow alone moved to one fill-first analytic rounded contour family. `signed_outset_filleted_loops()` shifts the same anchors and applies signed curvature evolution—convex radii increase and concave radii decrease—at exact levels `0 / 0.020 / 0.072 / 0.086`; every radius remains positive, and no clamp, collapsed join, independently re-rounded join, or old arrow morphology path participates. The staged manifest records that exact contract, the validator explicitly rejects the superseded morphology identity, and guard alone retains its separately approved morphological contract. Generation authority is exact: `git diff --exit-code ff34f05 -- tools/generate.py source manifests sets LICENSE.md` is clean at the audited tip, while the validator pins the full source commit/tree and the same scoped inputs.

The semantic fingerprint is an appropriate stronger source authority than raw Blender container equality. It canonicalizes scene/collection membership, object ownership/transforms/visibility/parenting/modifiers, exact mesh coordinates/edges/loops/polygons/triangulation/material slots, custom-normal presence, UV/color metadata, materials/node graphs, worlds, actions, and custom properties. Only Blender-recalculated load-time normal values are excluded after observed low-bit scheduling drift; authored geometry remains exact and generated GLB POSITION/NORMAL/runtime bytes are independently exact. A fresh default no-skip run reproduced staged/isolated fingerprint `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11` despite non-authoritative `.blend` container-byte variation.

Worst-case raster methodology is fail-closed for the reported defect: each of three bands contributes both minimum and maximum vertex/midpoint probes in shaft, concave-shoulder, convex-shoulder, and tip windows (`24` probes); all run through eight rotations, three RGB fills proven at least `0.20` distant from charcoal/white/background, three scales, and DPR `1/2/3`, for `5,184` checks. Deterministic coverage uses the requested raster phase with sampling capped at `0.00025` world units and fixed tolerance `0.002`, seven times below the narrowest `0.014` band. Immutable `0.0.8`, all three `0.004` shoulder-bulge mutations, and the old arrow morphology contract reject; the candidate passes outer-charcoal `0.013880242760794824..0.014000077871569134`, white `0.05155508756992079..0.052000000000000005`, inner-charcoal `0.019828869049757298..0.020000096786326922`, and raster `0.01375..0.052177734375`.

Fresh focused audit gates passed from one disposable candidate: generation; default `test_uniform_arrow.py` with no skip (`5,184` raster checks, three bulge adversaries, semantic fingerprint above); `validate_rounded_candidate.py --canonical --smoke` (all three changed source and GLB Blender `4.0.2` smokes, 17 raw files / `429,086` bytes, 73 review files); `test_rounded_adversarial.py` (`14` mutations); immutable `validate.py --release 0.0.7`; subprocess contract tests; visible-window budget (`12` records / `14` instances / `23,688` triangles / `42` draw calls); and an independent exact Git-tree check of all 16 raw/review predecessors. The disposable wrapper's tests all completed successfully; its first read-only cleanup attempt alone returned nonzero, after which permissions on only that disposable `/tmp` copy were restored and the copy was removed. No canonical path was touched.

Topology and runtime evidence remain exact: arrow `69` samples / `1,928` triangles, Euler `2`, one connected closed two-manifold, signed volume `0.06330667638182519`, minimum explicit-normal dot `0.9999999999962325`, fill/interior ratios `0.454118017050853 / 0.5693474203797928`, arrow GLB `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4`, candidate inventory `367d5efee059144175c118df905b37cfe510a8b6ef42b727928d9494108c6e73`, and proof `ba0c00d5497a73a24281e5bad25b2c305b676e710c871434cf8b28b2b58190db`. Six non-arrow candidate GLBs remain byte-identical to immutable `0.0.8`.

Canonical `0.0.8` remains exact: raw tree `e26ec4e8278860c60568bd2a89983cd09555ee75`, 17 files / `429,026` bytes, inventory `ac30d6b70cbae96115a7c97f5ad02b3da21fde7fb77f69083f1090e268bab5ac`, proof `ba8a52cf747ec5ab58dcd024c90f813a5c477541892f71da698ead6a65ca4758`; review tree `df080ea57c99bb50697f14e891edad7f53dbda2a`, 73 files / `77,758,435` bytes. Exact raw trees `0.0.1`–`0.0.8` are respectively `8e8879a750aa70715fd1ae45e62a447c8e9cd8b6`, `c2dedfd9c18a2260f53b7c013ec77a8dcb10c877`, `aa37bf534cc592a4057127876d567eadc3496f49`, `be36bbd03647bfb4654e0be1ed8b3f6446ced4ec`, `000653eace4b93f3c5d2eef11bd5c8255008b3de`, `53181edfdb560de2aeae01e9a05c212a9b93e438`, `846c41297230b5077ab1119880b729cc120e1098`, and `e26ec4e8278860c60568bd2a89983cd09555ee75`; exact review trees are `f0cd9a0a9fdbc7519db5a5f8515d61d479dc22c9`, `b4c68d81faba791ebe7361f9d5a8c1bf339b5e96`, `9122d32d6272854f6fc0f3a29b74997cee799bcf`, `8342d83194d8375886f371d6d57c6fcdda677a6f`, `a1781ce69ba81d660e4ffb24ae8b47d3873c63bb`, `f5652c80852153e746774579e4c1fb495ea360f3`, `8ca78c143d78743ff1dfce1b9fcadc5755a02530`, and `df080ea57c99bb50697f14e891edad7f53dbda2a`. No permanent raw/review `0.0.9` exists.

**Authorization:** this PASS authorizes exactly one later canonical gameplay-asset `release/raw/0.0.9` plus `review/0.0.9` build from the exact pushed documentation-only asset audit tip that contains this section. The builder must record and use that exact commit/tree as its sole final audit authority, retain `ff34f05…` / `339dd803…` as the scoped generation-input authority, require both `0.0.9` targets to be absent, run the canonical driver exactly once, and preserve all immutable predecessors and raw web evidence. This authorization does not authorize any web release, web version change, serving change, tag, GitHub Release, npm publication, or physical PASS.

## Failed canonical invocation diagnosis (dv1q / qj4w)

### Exact Observed Failure

The sole authorized command was `python3 tools/build_rounded_release.py --root . --release 0.0.9`. It exited `2` in `argparse` before `main()` could perform authority inspection, staging preparation, Blender startup, validation, or promotion. The exact parser contract was `parser.add_argument("--release", required=True, choices=[RELEASE])`, while imported `validate_rounded_candidate.RELEASE` was exactly `"0.0.8"`. Consequently argparse rejected `0.0.9` as an invalid choice (the accepted choices contained only `0.0.8`). Direct post-attempt checks found no `release/raw/0.0.9`, `review/0.0.9`, or `.canonical-0.0.9-staging` path. These are observed facts from the `dv1q` failure comment and the source at failed authority commit `7f6638e3dbd2ec16b686b14a1e9ba99cd636a2f0`; no rerun is permitted.

### Expected Behavior

Preparation tooling must accept exactly successor `0.0.9`, reject every other release before Blender or promotion, stage immutable predecessor raw `0.0.8`, and permit disposable candidate generation/validation only after clean generation inputs and absent authority/candidate targets are proven. This task prepares that authority but does not authorize or perform another canonical build.

### Execution Path

1. Python imported `RELEASE="0.0.8"` from `validate_rounded_candidate.py` into `build_rounded_release.py`.
2. `main()` constructed the `--release` parser with `choices=[RELEASE]`.
3. `parse_args()` compared requested `0.0.9` with the sole allowed value `0.0.8`.
4. Argparse emitted its usage/invalid-choice diagnostic and raised `SystemExit(2)`.
5. Execution never reached `generation_inputs_are_authorized()`, target/staging checks, `prepare()`, Blender, marker creation, validation, smoke, or promotion.

### Most Likely Root Cause

The release-preparation proof layer was never advanced after the source audit authorized `0.0.9`: `generate.py`, the candidate validator, canonical builder marker, reproducibility/oracle paths, and staged predecessor assumptions remained versioned for `0.0.8`. The first hard gate encountered was the builder's imported argparse choice, so the failure was deterministic and pre-generational rather than a Blender, geometry, source-authority, or filesystem defect.

### Alternative Hypotheses

1. Dirty generation inputs: contradicted because argparse exited before the Git-diff authority gate and the attempt recorded clean exact authority commit/tree.
2. Existing canonical or staging targets: contradicted both by execution order and post-attempt absence checks.
3. Blender failure: impossible on this path because Blender lookup/invocation occurs after parsing and was never reached.
4. Candidate anchor mismatch: impossible on this path because no candidate was generated and anchor comparison occurs after generation.

### Why Previous Fixes Failed

The preceding arrow repair and proof-hardening work intentionally remained disposable `0.0.8` tooling while canonical `0.0.9` authorization was reserved. The final audit authorized a successor but did not advance the executable release literals. The canonical invocation therefore correctly failed closed, but at an earlier gate than the authorization expected.

### Unknowns

The versioned `0.0.9` inventory, proof, raw/review tree digests, total bytes, and review hashes cannot be inferred from `0.0.8`; they must be derived from two independently generated isolated candidates after a clean `0.0.9` generation-input authority commit.

### Minimal Reproduction

At failed authority `7f6638e3…`, inspect the imported `RELEASE` and builder parser: `RELEASE` is `0.0.8`, and `choices=[RELEASE]`. Parsing argument vector `--release 0.0.9` necessarily exits `2`. Re-running the canonical driver is neither required nor permitted.

### Proposed Verification

First advance and commit only generation inputs for `0.0.9`. Then pin tooling to that commit/tree, require clean scoped inputs and absent raw/review/staging before Blender, and generate two isolated candidates. They must match byte-for-byte across all 17 raw and all 73 review files, match the staged arrow semantic fingerprint and exact geometry contract, carry correct `0.0.9` proof source identity, and yield the exact anchors later embedded into validation. Hostile wrong-version, dirty-input, and pre-existing-target/staging tests must reject before Blender or promotion.

### Recommended Fix

Advance `generate.py` to accept only `0.0.9` and use predecessor `0.0.8`; advance the staged manifests/set to `0.0.9`; commit this clean generation-input authority before changing validator/builder pins. In a second tooling/evidence commit, update exact release literals, generation marker, authority commit/tree, candidate paths, expected anchors, proof identity checks, reproducibility, and adversaries. Never invoke the canonical driver and never create permanent raw/review `0.0.9`.

### Debugging Record

```text
Problem: Authorized 0.0.9 canonical command failed before generation.
Observed symptom: build_rounded_release argparse exited 2 because requested 0.0.9 was outside sole choice 0.0.8; no target or staging path appeared.
Root cause: Release-preparation tooling remained explicitly pinned to 0.0.8 after audit authorization moved to successor 0.0.9.
Evidence: dv1q failure comment; build_rounded_release.py choices=[RELEASE]; validate_rounded_candidate.py RELEASE="0.0.8"; clean/absent postconditions.
Failed approaches: No implementation fix was attempted; the single invocation correctly failed closed and was consumed.
Corrective action: Commit 0.0.9 generation inputs first, then pin tooling/anchors from two isolated candidates.
Verification test: Pre-Blender hostile gates, two-build exact 17 raw/73 review comparison, fingerprint/geometry/proof identity, full isolated validation and immutable predecessor checks.
Related files/components: tools/generate.py, tools/build_rounded_release.py, tools/validate_rounded_candidate.py, reproducibility/oracle/adversarial tools, staged manifests/set.
Remaining uncertainty: Exact 0.0.9 candidate anchors until isolated generation completes.
```

## 0.0.9 release-preparation result (qj4w)

Preparation is **CODER PASS; QA remains open**. Generation inputs were committed first at exact commit `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / tree `fe3938e85227d6ea045e8da7330e48cb749c6360`. That authority advances the generator and staged source manifests/set from sole successor `0.0.8` to sole successor `0.0.9`, changes the predecessor staging source from raw `0.0.7` to immutable raw `0.0.8`, requires explicit source commit/tree proof identity, and normalizes rendered PNGs by removing nondeterministic ancillary metadata while preserving exact critical chunks/pixels. The latter closes an observed first two-build mismatch: IDAT chunks and file sizes were already identical, while Blender-authored `tEXt` path/time values differed; normalized reruns are exact for all review bytes.

Two fresh independently generated isolated candidates then matched byte-for-byte across all `17` raw and all `73` review files. Exact prepared anchors are:

- generation authority commit/tree: `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / `fe3938e85227d6ea045e8da7330e48cb749c6360`;
- source semantic fingerprint: `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11`, with exact document equality across staged and both isolated arrow scenes;
- raw: `17` files / `429,209` bytes / tree digest `979a202bf06d99ebc53588668d67e9d50df7bcd14e9b0d4e69c6dd73b09f9a00`;
- inventory/proof SHA-256: `95ec22c1657d4931e42327e0544b86f782075288a3330a4d23b0fed07dce65fa` / `e1726ca2bc3a0980cc86ba6184bf7da57079f7ee1e42e24094c47196a3dbace9`;
- proof `source_authority`: exact commit/tree above;
- review: `73` files / `77,797,749` bytes / tree digest `009d21bd09b9015a3f7f9629b96122e3f462875c9a5a3ef87aab578c872b9abc`;
- review hashes-manifest SHA-256: `8a7155bbd9a7878eaac37cb1a51eddc21bfb8ab861bf16e65b6d6b0b6b43d282`;
- arrow GLB: `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4` / `152,916` bytes.

Fresh candidate validation passed in canonical mode with Blender `4.0.2` source/GLB smoke against a disposable root: raw `17` / `429,209`, review `73` / `77,797,749`, arrow/circle/guard `1,928 / 1,788 / 1,172` triangles, Euler `2`, positive volumes, and minimum explicit-normal dots at least `0.9999999999962325`. The default uniform-arrow oracle passed `5,184` raster checks, all six non-arrow GLBs were byte-identical to immutable `0.0.8`, and exact band/readability/topology values remained unchanged. The `14` rounded mutations, three shoulder bulges, superseded contract, wrong release `0.0.8/0.0.10`, dirty generation inputs, existing raw/review/staging, altered proof/source anchor, subprocess fatal-signature, visible-window budget, immutable predecessor validation, and exact 16 Git-tree checks all reject/pass as intended before Blender or promotion where applicable. The maintained reproducibility command independently generated and removed another two temporary builds and repeated exact `17 + 73` byte equality and fingerprint identity.

The builder now imports exact `RELEASE=0.0.9`, exact generation marker, prepared authority commit/tree, and versioned raw/review expected anchors. It stages predecessor raw `0.0.8`; parser, clean-authority, existing-target/staging, post-generation anchor, full candidate validation, smoke, and promotion ordering remain fail closed. The canonical driver was never invoked during preparation. Permanent `release/raw/0.0.9`, `review/0.0.9`, and `.canonical-0.0.9-staging` remain absent, and all disposable candidates/fingerprints are removed after evidence collection.

## Independent release-authority QA (ab3a)

Independent QA is **PASS** at exact tooling/evidence commit `3e76d649575ee78043b054e9164238d74adabb09` / tree `af85865565807e69b7ad5f06f6cc81486e3acb3e`. The generation-input authority is exact commit `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / tree `fe3938e85227d6ea045e8da7330e48cb749c6360`; `git diff --exit-code f2ad27f9 -- tools/generate.py source manifests sets LICENSE.md` passed, and the later tooling commit changes none of those scoped inputs.

Two fresh isolated roots were prepared independently from immutable raw `0.0.8`, then generated directly with Blender `4.0.2` and the exact source commit/tree arguments. Every relative path, byte count, and SHA-256 matched across all `17` raw and all `73` review files. Both candidates independently reproduce raw `429,209` bytes / tree digest `979a202bf06d99ebc53588668d67e9d50df7bcd14e9b0d4e69c6dd73b09f9a00`, inventory `95ec22c1657d4931e42327e0544b86f782075288a3330a4d23b0fed07dce65fa`, proof `e1726ca2bc3a0980cc86ba6184bf7da57079f7ee1e42e24094c47196a3dbace9`, review `77,797,749` bytes / tree digest `009d21bd09b9015a3f7f9629b96122e3f462875c9a5a3ef87aab578c872b9abc`, and review hashes `8a7155bbd9a7878eaac37cb1a51eddc21bfb8ab861bf16e65b6d6b0b6b43d282`. Proof `source_authority` is exactly `f2ad27f9…` / `fe3938e8…`; the arrow GLB is `152,916` bytes / `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4`; all six non-arrow GLBs are byte-identical to immutable `0.0.8`; and staged/candidate scene documents match at semantic fingerprint `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11` without asserting nondeterministic `.blend` container bytes.

Both isolated candidates passed canonical validation plus source/GLB smoke. Exact cue results were arrow/circle/guard `1,928 / 1,788 / 1,172` triangles, Euler `2`, positive volumes `0.06330667638182519 / 0.06900413678292198 / 0.07443666445378194`, and minimum explicit-normal dots `0.9999999999962325 / 0.9999999999999819 / 0.9999999999990923`. The independent uniform-arrow geometry/pixel oracle passed `5,184` checks across all min/max feature probes, rotations, contrast colors, scales, and DPRs; candidate bands remained outer-charcoal `0.013880242760794824..0.014000077871569134`, white `0.05155508756992079..0.052000000000000005`, inner-charcoal `0.019828869049757298..0.020000096786326922`, raster `0.01375..0.052177734375`, and fill/interior `0.454118017050853 / 0.5693474203797928`. Immutable `0.0.8`, three shoulder bulges, and the superseded contract rejected; all `14` rounded mutations rejected.

Disposable builder preflight rejected wrong `0.0.8`/`0.0.10`, dirty generation input, existing raw target, existing review target, existing staging, and altered proof/source anchor with `0` Blender invocations and `0` promotions; preparation copied raw `0.0.8`, never `0.0.7`. Exactly one valid builder execution was then run in a disposable clone outside this canonical repository. It completed one generation, validation, smoke, and promotion, removed its staging root, and its complete `17 + 73` promoted path/byte inventories matched the first prepared candidate exactly. The canonical builder was never invoked here.

Supplemental PASS gates were Python compilation, immutable `validate.py --release 0.0.7`, subprocess fatal-signature tests, visible-window budget (`12` records / `14` instances / `23,688` triangles / `42` draw calls), exact authority/tooling split scope, and direct checks of all 16 predecessor Git trees. Raw and review `0.0.1`–`0.0.8` remain at the exact trees recorded above. Permanent canonical `release/raw/0.0.9`, `review/0.0.9`, and `.canonical-0.0.9-staging` are absent after QA.

**Disposition:** PASS and close `aerobeat-web-assembly-ab3a`. Leave `aerobeat-web-assembly-qj4w` open for the separate `8yf1` audit; this QA grants no canonical build, web release, tag, publication, serving change, or physical PASS.

## Final release-authority audit (8yf1)

**PASS.** The audited linear authority is generation inputs `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / tree `fe3938e85227d6ea045e8da7330e48cb749c6360`, tooling `3e76d649575ee78043b054e9164238d74adabb09` / tree `af85865565807e69b7ad5f06f6cc81486e3acb3e`, and independent QA evidence `af64acfe460b9b6cefc7426684907d425eb3d81c` / tree `70669f26c64dbefcb4925b9b4489edd2743cc858`. Commit ancestry is exact and `git diff --exit-code f2ad27f9 -- tools/generate.py source manifests sets LICENSE.md` remains clean. Source inspection confirms the arrow alone uses the fill-first analytic rounded signed-offset family at levels `0 / 0.020 / 0.072 / 0.086`, with positive signed-curvature radii and no clamp or independent re-round; guard alone retains its separate morphology contract. The validator binds the exact generation commit/tree, source semantic fingerprint, geometry/topology/material authority, proof identity, and all immutable predecessor Git trees.

A fresh maintained two-build run passed exact byte comparison for every `17` raw and `73` review file and reproduced semantic fingerprint `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11`. Exact prepared anchors independently remained raw `17` files / `429,209` bytes / tree digest `979a202bf06d99ebc53588668d67e9d50df7bcd14e9b0d4e69c6dd73b09f9a00`, inventory `95ec22c1657d4931e42327e0544b86f782075288a3330a4d23b0fed07dce65fa`, proof `e1726ca2bc3a0980cc86ba6184bf7da57079f7ee1e42e24094c47196a3dbace9`, review `73` files / `77,797,749` bytes / tree digest `009d21bd09b9015a3f7f9629b96122e3f462875c9a5a3ef87aab578c872b9abc`, review hashes `8a7155bbd9a7878eaac37cb1a51eddc21bfb8ab861bf16e65b6d6b0b6b43d282`, and arrow GLB `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4`. Proof `source_authority` is exactly `f2ad27f9…` / `fe3938e8…`.

One additional valid builder execution ran only in a fresh disposable clone at QA tip `af64acfe`; it performed exactly one generation and promotion, removed staging, and reproduced the same complete raw/review anchors and all prepared bytes. Against that disposable result, canonical validation plus Blender `4.0.2` source/GLB smoke passed; the default uniform-arrow oracle passed `5,184` checks and rejected immutable `0.0.8`, all three bulges, and the superseded contract; all `14` rounded adversaries rejected; and preflight rejected wrong `0.0.8`/`0.0.10`, dirty generation input, existing raw, existing review, existing staging, and altered proof/source authority before Blender or promotion (`0` invocations / `0` promotions). Python compilation, immutable `0.0.7` validation, subprocess adversaries, and visible-window budget (`12` records / `14` instances / `23,688` triangles / `42` draw calls) also passed.

All raw/review predecessor Git trees `0.0.1`–`0.0.8` recompute to the exact 16 recorded identities, including `0.0.8` raw `e26ec4e8278860c60568bd2a89983cd09555ee75` and review `df080ea57c99bb50697f14e891edad7f53dbda2a`. The canonical checkout remains clean of `release/raw/0.0.9`, `review/0.0.9`, and `.canonical-0.0.9-staging`; no canonical builder, web release, version, serve, route, tag, publication, or physical-PASS action occurred.

**Exact authorization:** this PASS authorizes exactly one fresh canonical invocation of `python3 tools/build_rounded_release.py --root . --release 0.0.9`, and no other generation invocation, from the exact pushed documentation-only asset audit commit/tree containing this section. At invocation time both canonical targets `release/raw/0.0.9` and `review/0.0.9` and staging target `.canonical-0.0.9-staging` must be absent; the builder must retain generation authority `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / `fe3938e85227d6ea045e8da7330e48cb749c6360` and preserve every predecessor. The earlier `dv1q` argparse invocation generated and promoted nothing, is separately consumed, and does not consume this one newly granted invocation. No web release, web build, serving change, tag, GitHub Release, npm publication, or physical PASS is authorized.

## Canonical 0.0.9 build result (ga90)

**BUILD PASS; ga90 remains open for independent audit 83dj.** The final audit authority was exact clean pushed commit/tree `80378c51b167c329f4c0df4a81510fcd4fe28e6b` / `27f0caafa3928476b917631f9e3319f6c0b3aa89`, with canonical raw, review, and staging targets absent. Generation-input authority remained exact `f2ad27f9c5dd067beca0ab8504565d781e49a9f6` / `fe3938e85227d6ea045e8da7330e48cb749c6360`; the scoped generation-input diff was clean. Blender was exactly `4.0.2`, Python compilation passed, immutable `0.0.7` validation passed, subprocess adversaries passed, visible-window budget passed at `12` records / `14` instances / `23,688` triangles / `42` draw calls, and all `16` predecessor Git trees matched before invocation.

The authorized command `python3 tools/build_rounded_release.py --root . --release 0.0.9` was invoked exactly once in the canonical checkout. It completed exactly one Blender generation and one promotion, emitted `CANONICAL_BUILD_OK` with `generation_count=1`, and removed `.canonical-0.0.9-staging`. It reproduced the audited anchors exactly: raw `17` files / `429,209` bytes / tree digest `979a202bf06d99ebc53588668d67e9d50df7bcd14e9b0d4e69c6dd73b09f9a00`; inventory/proof SHA-256 `95ec22c1657d4931e42327e0544b86f782075288a3330a4d23b0fed07dce65fa` / `e1726ca2bc3a0980cc86ba6184bf7da57079f7ee1e42e24094c47196a3dbace9`; review `73` files / `77,797,749` bytes / tree digest `009d21bd09b9015a3f7f9629b96122e3f462875c9a5a3ef87aab578c872b9abc`; review hashes SHA-256 `8a7155bbd9a7878eaac37cb1a51eddc21bfb8ab861bf16e65b6d6b0b6b43d282`; arrow GLB `152,916` bytes / SHA-256 `75435bc79c0278da5488ab05d1a97ac409cdab390e10483748c30a5aa67ad7e4`; proof source authority exact `f2ad27f9…` / `fe3938e8…`; semantic scene fingerprint `6ec9138f82933e7b94e4732f0b1ea038e85c5e80565ab404ce443c36a249ac11`.

Canonical validation plus Blender source/GLB smoke passed and finalized both trees at directory/file modes `0555` / `0444`. Geometry/material/topology results were arrow/circle/guard `1,928 / 1,788 / 1,172` triangles, Euler `2`, positive volumes `0.06330667638182519 / 0.06900413678292198 / 0.07443666445378194`, and minimum explicit-normal dots `0.9999999999962325 / 0.9999999999999819 / 0.9999999999990923`. The uniform-arrow oracle passed all `5,184` raster checks, three geometry bands across four feature classes, three bulge adversaries, exact fill/interior ratios `0.454118017050853 / 0.5693474203797928`, all six unchanged GLBs, and the semantic fingerprint. All `14` rounded adversaries rejected. Post-build release preflight rejected two wrong versions, three existing targets, dirty inputs, and altered source proof with `0` Blender invocations and `0` promotions. Exact anchor rechecks and all `16` predecessor Git trees passed after finalization.

No web build, version, serve, route, tag, GitHub Release, npm publication, or physical-PASS action occurred. The immutable canonical assets and this evidence are ready for the separate `83dj` audit.
