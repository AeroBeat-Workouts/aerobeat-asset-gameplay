# Additive knee gameplay art release 0.0.13

**Status:** approved Section C/D asset-release coder slice; Assembly Bead `aerobeat-web-assembly-gmnl.6.2` claimed and in progress. Owner: asset art-tools coder; parent independently reviews before closing Bead. **Next acceptance:** two new Cookie Blender 4.0.2 disposable builds match every 0.0.13 raw/review byte, both knee source semantic fingerprints, and strict manifest/import checks before any canonical promotion. No UI fidelity contract applies: knee images were inspiration and independent human approvals, not exact mockups.

## Decision and scope

Derrick separately approved floating `knee-target/hover-shell-strike-v1` *for now* and wearable `knee-pad/segmented-lightwrap-v1`, plus the existing semantic `.blend` scene fingerprint for source equivalence. Preserve exact GLB/PNG/review byte gates, strict SHA manifests, clean Blender imports and all 0.0.12 contents. Add one new immutable raw `0.0.13`, independently swappable roles in `sets/default-v1.json`, separate source snapshots and review tree. No existing candidate, release, renderer, Assembly, public service, human-visible game copy, or tracked-knee runtime changes. Only commit/push a coherent release after all gates pass; parent verifies independently.

## References

- Asset `README.md` and `AGENTS.md` release rule; `tools/validate_track_candidate.py`, `tools/reproducibility_track.py`.
- Assembly `.plans/2026-10-20-boxing-spacing-repetition-knee-strikes.md` Sections C/D; Bead `.6.2`.
- Candidate deterministic generators from `9e78fa9b643d0cf9a811be6ec69d8c9453494a9e`, `candidates/knee-art-2026-10-20/reproducibility-tool-findings.md`.
- Git predecessor raw/review `0.0.12`, unchanged bytes required.

## Tasks

1. **Inspect predecessor and choose minimal contract** (in progress): reuse 0.0.12 seven GLBs and seven manifests without mutation; add two GLBs, v1 manifests, nine-role set, inventory/proof, source snapshots, and additive review PNGs. Exact 0.0.12 files cannot be made byte-identical to changed set/inventory/proof; carry the old set and its hash only in immutable 0.0.12 and change only the new set. Bead `.6.2`.
2. **Implement candidate-only staging and validator** (pending): check unused 0.0.13 paths, pinned generator source commit/tree, predecessor immutable Git tree, correct permitted raw contents, full SHA manifests, independent identities/geometry/materials, and smoke. No canonical writes until proof passes. Bead `.6.2`.
3. **Run genuine two-build release proof** (pending): invoke pinned Cookie Blender 4.0.2 generators into two empty roots; strict validate per root, compare raw/review files byte-for-byte and two semantic scene fingerprints; record hashes/commands. Bead `.6.2`.
4. **Promote and document only if green** (pending): stage approved bytes, validate canonical and predecessor unchanged, commit/push asset-only release with README update; parent separately verifies/owns Bead closure. Bead `.6.2`.

## Current guardrails and release gate review

- Keep: asset `AGENTS.md` final rule (strict validation, Blender source/GLB smoke, two independent temporary builds), README's semantic `.blend` source equivalence and raw/review exact bytes, 0.0.12 predecessor and source Git identities.
- No added speculative security/provenance layer; top-level inventory and proof are existing required layout. Avoid mutable-source binary hashes in cross-root manifests/proof, which would falsify strict deterministic release bytes.
- Runtime visual scale, actual knee tracking, scoring and public cutover remain Assembly Section D work; this art release does not claim them.
