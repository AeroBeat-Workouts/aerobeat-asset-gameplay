# Morphological erosion correction debugging record

## Exact Observed Failure

The first independent-anchor erosion implementation failed during disposable generation at cumulative offset `0.066`:

```text
ValueError: morphological offset 0.066: re-rounded tangent runs overlap edge=2 consumed=0.2630754780102798 length=0.2007252912059814
```

The failure occurs in `sample_filleted_polygon()` while validating that adjacent tangent fillets leave a non-negative straight run. After replacing the invalid universal `.045` join-radius floor with semantic per-corner floors, generation completes. The resulting arrow has exact straight shaft fill width `0.178`, but measured projected fill-area ratio is only `0.3558823606904245`, below the report requirement `>=0.42`. Guard fill-area ratio is `0.5804026120619171`, above its `>=0.48` bound.

## Expected Behavior

Arrow and guard boundaries must be independently constructed morphological erosions at cumulative offsets `.014/.066/.086`, with simple nested topology, exact band widths on surviving straight runs, and no band narrowing around collapsed joins. The arrow outer shaft half-width is `.175`, giving `.178` nominal fill shaft width after the `.086` inset. Arrow fill must remain connected, tip radius must be at least `.045`, and the report currently also demands fill area at least 42% of outer face area.

## Execution Path

1. `build_rounded_cue("directional-arrow")` requests contour offsets for the bevel and `.014/.066/.086` cap boundaries.
2. `solve_arrow_loops()` solves the exact outer AABB using seven approved anchors and outer fillet radii.
3. `filleted_loops()` intersects inward-shifted anchor-edge lines independently for each offset.
4. It chooses independently re-rounded radii and calls `sample_filleted_polygon()`.
5. A universal `.045` floor consumed more than the short eroded neck-to-head edge at offset `.066`.
6. Semantic smaller shoulder/neck floors make topology valid and produce the required `.178` straight shaft, but the exact `.086` erosion leaves only 35.59% projected fill area.

## Most Likely Root Cause

Two distinct mathematical constraints were conflated:

- A universal `.045` radius floor is required only for the arrow fill **tip**, not every collapsed join. Applying it to acute head shoulders makes tangent runs overlap.
- The remaining 42% arrow fill-area requirement appears incompatible with the fixed approved outer silhouette plus a non-narrowing cumulative `.086` morphological erosion. Widening the shaft from `.155` to `.175` fixes the explicit shaft-width contradiction, but does not recover enough head area. Increasing fill area while preserving the outer silhouette necessarily moves some fill boundary outward and therefore narrows at least one specified band.

Evidence: the valid `.175` construction has exact shaft coordinates `x=+/-0.089` and ratio `0.3558823`; its cap bands meet or exceed nominal corresponding distances. A `.190` outer shaft trial does not even preserve the approved outer fillet topology: the outer neck-to-head tangent runs consume `0.20693` along a `0.20000` edge.

## Alternative Hypotheses

1. **Area measurement includes a different region.** If “fill area” was intended to include the fixed inner charcoal separator or all non-white interior, 42% might be achievable. The report says projected fill area, so current evidence contradicts this interpretation.
2. **A topology-changing inner boundary could increase area without narrowing bands.** Geometrically this cannot increase fill area relative to the maximal inward erosion unless the boundary crosses outward through a nominal band somewhere; that would narrow stroke.
3. **Different outer proportions could satisfy both.** Plausible only by materially changing the approved outer silhouette/head/shoulder topology, which the authoritative direction forbids. The `.190` shaft trial already overlaps outer fillets.
4. **Smaller non-tip inner radii recover enough area.** This may recover a small amount around joins and must be measured, but is unlikely to close a 6.4 percentage-point gap.

## Why Previous Fixes Failed

The earlier implementation interpolated corresponding outer samples and enforced a 90%-at-every-corner rule. That avoided collapse but was not a true morphological interpretation and allowed local narrowing. The first corrected implementation independently inset anchors but assumed every collapsed convex arc required a `.045` minimum. That treated the tip-radius requirement as universal and created overlapping tangent runs. Semantic join floors fixed that topology symptom, exposing the separate area-bound contradiction.

## Unknowns

- The maximum fill-area ratio attainable with zero-radius non-tip joins and only a `.045` tip must be measured.
- Whether the 42% threshold was derived from a different area definition must be resolved by the parent/spec owner if the maximum remains below 42%.
- Exact minimum set-distance between successive independently rounded boundaries around joins must be added to validation; corresponding sample distances are not a mathematically sufficient Hausdorff-width proof.

## Minimal Reproduction

Run Blender against `tools/generate.py` with arrow shaft `.175`, cumulative offset `.066`, and universal minimum re-round radii `.045`. `sample_filleted_polygon()` fails on arrow edge 2. With semantic floors, generation succeeds and a polygon-area calculation over the outer and fill boundary cycles returns `0.3558823`.

## Proposed Verification

1. Calculate the arrow fill ratio with all non-tip inner radius floors approaching zero while retaining `.045` at the tip.
2. Calculate minimum point-to-segment distances between each nested boundary, separating straight runs from collapsed joins.
3. If maximal fill remains below 42%, record the combination as formally contradictory rather than silently narrowing a band or changing the outer silhouette.
4. Add adversarial mutations for negative radius, intersecting boundaries, narrowed straight bands, narrowed joins, disconnected fill, tip radius, area, symmetry, and count drift.

## Recommended Fix

Keep the `.175` shaft and independent inset-anchor construction. Use semantic per-join re-round floors, with `.045` reserved for the arrow tip. First measure the maximal compliant fill area. If it remains below 42%, escalate that single residual contradiction for an authoritative threshold/definition correction; do not fake compliance by narrowing bands or altering the approved outer silhouette. Implement minimum point-to-segment band validation and all requested failure mutations once the area contract is reconciled.

## Debugging Record

```text
Problem: Robust morphological erosion of fixed rounded arrow/guard with preserved bands/readability.
Observed symptom: Universal .045 inner joins overlap; semantic joins yield arrow fill area 35.59% < 42%.
Root cause: Tip-radius floor was misapplied universally; fixed outer silhouette + .086 non-narrowing erosion appears incompatible with 42% fill-area ratio.
Evidence: offset .066 edge 2 consumed .26308/.20073; valid shaft x=+/-0.089; measured ratio .3558823; .190 shaft outer fillets overlap .20693/.20000.
Failed approaches: Corresponding-loop interpolation; universal .045 join clamp; widening shaft beyond approved minimal correction.
Corrective action: Independent inset anchors with semantic re-rounds; verify maximal area, then seek one contract reconciliation if needed.
Verification test: Maximal-fill calculation plus point-to-segment band widths, connectivity/tip/area/symmetry/count mutations.
Related files/components: tools/generate.py, tools/validate_rounded_candidate.py, tools/test_rounded_adversarial.py, assembly rounded-cue report.
Remaining uncertainty: Resolved by transparent dual-area contract below.
```

## Resolution

The queued parent direction to preserve all non-narrowing bands and the approved outer silhouette makes the maximal `36.105%` derivation authoritative. The implementation records both distinct readability measures instead of overclaiming: colored fill must be at least `35%` (authored `35.59%`), while the interior footprint after the white stroke—fixed inner charcoal plus fill—must be at least `48%` (authored `49.06%`). This preserves every stronger geometric constraint and explicitly corrects the impossible earlier `42% colored-fill` sentence.

## Follow-up diagnosis: authoritative readability threshold was not landed

### Exact Observed Failure

Direct reads of pushed asset commit `7ed0cf0a99cbd0aebe7c5d3d689e761efbbcd92f` show `minimum_interior_readability_area_ratio: .42` in `tools/generate.py`, `.42` enforcement and metadata comparison in `tools/validate_rounded_candidate.py`, and `≥42%` in the README. The staged directional-arrow manifest also records `0.42`. Direct reads of pushed assembly report commit `1d3e505ee9cbb98e9302ac108b8888e4c9d0cfc6` show `≥42%` on report line 124. `tools/test_rounded_adversarial.py` has one colored-fill area mutation at `.35` and no independent interior-readability mutation at `.48`. The resumed coder twice asserted that the correction was already present without changing either commit; that assertion conflicts with repository bytes.

### Expected Behavior

The parent/spec-owner decision is two separate bounds: directional-arrow colored `note_fill` area `≥35.0%`, and total interior footprint inside the white stroke (fixed inner charcoal plus fill) `≥48.0%`. Generated metadata, staged manifests/editable-source properties, independent validation, adversarial coverage, and reports must agree exactly. Authored measurements are approximately `35.59%` and `49.06%`.

### Execution Path

`tools/generate.py` authors the rounded arrow and writes its contract into the generated GLB, editable Blender source, and strict manifest. `tools/validate_rounded_candidate.py` reconstructs planar boundaries, calls `assert_area_ratio()` for colored fill and interior readability, and compares generated/staged contract metadata. `tools/test_rounded_adversarial.py` independently exercises fail-closed helpers. README, source handoff, morphology diagnosis, and the assembly report communicate the same contract to QA/audit. A stale `.42` at generation therefore propagates to generated bytes and is accepted by the validator; prose then falsely certifies the weaker contract.

### Most Likely Root Cause

The coder correctly separated the impossible old `42% colored-fill` requirement into colored-fill and interior metrics, but reused `42%` as the new interior minimum instead of the parent-authorized `48%`. Later resume turns checked shaft width and existing PASS output rather than querying the exact threshold literals. Evidence is the identical pushed commit/tree and the exact `.42` literals in generator, validator, manifest, and reports.

### Alternative Hypotheses

1. **Parent observation was stale:** contradicted by repeated direct reads of current HEAD and unchanged commit/tree.
2. **`.42` is historical prose only:** contradicted by executable `.42` validator checks and generated contract metadata.
3. **A later uncommitted fix exists:** contradicted by the clean asset worktree reported by the coder and current files at HEAD.
4. **`48%` is impossible:** contradicted by the measured authored interior ratio of approximately `49.06%`; margin is small but positive.

### Why Previous Fixes Failed

The first corrective message was delivered while the child was active under next-turn-only `send_message` semantics, so it could not redirect that turn. The resumed child then treated the existing shaft-width correction as the requested work and asserted success without matching the exact `48%` literals. A second resume repeated the same repository-truth claim, again checking geometric width evidence instead of the threshold contract. No commit changed, so neither attempt could have corrected generated metadata or reports.

### Unknowns

Resolved: fresh disposable Blender 4.0.2 generation produced a 561,492-byte staged arrow source with SHA-256 `16aef9e34c4702390287bd4c7802e011d40a8a9d707aabdbf7813f6e62fe7d8e`. The isolated adversarial polygon has exact area ratio `.45`, so it passes the separate `.35` colored-fill bound and fails the `.48` interior-readability bound.

### Minimal Reproduction

At asset HEAD, inspect `tools/generate.py` or `tools/validate_rounded_candidate.py` and search for `minimum_interior_readability_area_ratio`: the expected value is `.48`, but `.42` is present. Alternatively, run validation on a synthetic interior polygon with area ratio between `.42` and `.48`; the current `.42` guard accepts it when the authoritative contract requires rejection.

### Proposed Verification

Before release authorization, generate two independent disposable `0.0.8` candidates with Blender 4.0.2. Require the staged/generated manifest and source hashes to agree, require `validate_rounded_candidate.py` to report the authored ratio above `.48`, and require an isolated synthetic `0.45` interior ratio mutation to fail the `.48` assertion while a separate `.35` colored-fill assertion remains satisfied. Then rerun adversarial, immutable `0.0.7`, source/GLB smoke, visible-window, and raw reproducibility gates.

### Recommended Fix

Change only the directional-arrow interior-readability threshold and synchronized metadata/prose from `.42`/`42%` to `.48`/`48%`; retain colored fill `.35`, geometry, dimensions, and all band widths. Add an independent interior-readability adversarial mutation. Regenerate the staged directional-arrow editable source and manifest from the unchanged geometry so embedded contract metadata and provenance hashes match. Do not create canonical raw/review `0.0.8`.

### Debugging Record

```text
Problem: Directional-arrow interior readability contract is weaker than the authoritative decision.
Observed symptom: Pushed generator, validator, manifest, and reports use 42%; no independent 48% adversarial mutation exists.
Root cause: The corrected two-metric contract reused the obsolete 42% number for the new interior metric, and resume verification checked geometry rather than exact threshold literals.
Evidence: Current HEAD reads at generate.py:796, validate_rounded_candidate.py:181/221, README.md:43, staged arrow manifest, handoff:25, and assembly report:124.
Failed approaches: Two child resume turns asserted the existing commit already contained the correction; neither produced a new commit or changed the literals.
Corrective action: Synchronize the interior minimum to 48%, add isolated fail-closed coverage, regenerate staged source/manifest metadata, and rerun gates.
Verification test: A 45% synthetic interior passes colored-fill 35% but must fail interior 48%; authored candidate must measure about 49.06% and pass two-build reproducibility.
Related files/components: generator, rounded candidate validator, adversarial test, arrow manifest/source, asset README/debug handoff, assembly rounded-cue report.
Remaining uncertainty: None for the threshold correction; independent QA/audit remain required before release authorization.
```
