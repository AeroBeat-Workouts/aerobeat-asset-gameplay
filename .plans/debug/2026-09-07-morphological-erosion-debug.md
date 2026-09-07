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

The queued parent direction to preserve all non-narrowing bands and the approved outer silhouette makes the maximal `36.105%` derivation authoritative. The implementation records both distinct readability measures instead of overclaiming: colored fill must be at least `35%` (authored `35.59%`), while the interior footprint after the white stroke—fixed inner charcoal plus fill—must be at least `42%` (authored `49.06%`). This preserves every stronger geometric constraint and explicitly corrects the impossible earlier `42% colored-fill` sentence.
