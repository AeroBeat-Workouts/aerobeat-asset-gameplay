# CC BY-NC 4.0 license text integrity failure

## Exact Observed Failure

Final Task 2 audit found `LICENSE.md` lines 99–102 contain this noncanonical clause:

> **b. NonCommercial.**
>
> You may not exercise any of the Licensed Rights in the Licensed Material for NonCommercial purposes.

That sentence prohibits the exact NonCommercial exercise granted by CC BY-NC 4.0. The official Creative Commons legal code has only Section 3(a), Attribution, and proceeds from Section 3(a)(4) directly to Section 4. The official plain-text legal code was fetched from `https://creativecommons.org/licenses/by-nc/4.0/legalcode.txt`; it is 19,347 bytes, 408 lines, SHA-256 `41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0`.

The same incorrect clause exists in the local `aerobeat-template-asset/LICENSE.md`, proving the new repo inherited the defect from its template reference rather than introducing a unique typo.

## Expected Behavior

`LICENSE.md` must contain the exact canonical Creative Commons Attribution-NonCommercial 4.0 International plain-text legal code. Validation must bind the tracked file to a reviewed expected SHA-256 so a future semantic inversion or other drift fails automatically.

## Execution Path

1. Task 2 required the coder to inspect the existing internal asset template before choosing the license.
2. The coder copied/adapted the template license into the new public gameplay-asset repository.
3. The template itself contains a noncanonical Section 3(b) that inverts the NonCommercial permission.
4. Asset validation checks manifest labels such as `CC-BY-NC-4.0`, but does not hash or parse `LICENSE.md`.
5. Mechanical and visual QA passed because neither gate compared legal text to an authoritative source.
6. Final audit compared the clause to official Creative Commons legal code and found the contradiction.

## Most Likely Root Cause

The immediate cause is inheritance of a corrupted/modified license file from `aerobeat-template-asset`. The systemic cause is absence of byte-integrity validation for standardized legal text. The exact identical wrong clause in both files and the validator's manifest-only checks establish this causal chain.

## Alternative Hypotheses

1. **Intentional custom restriction** — contradicted by README/manifests consistently claiming standard CC BY-NC 4.0 and by the clause being internally self-defeating.
2. **Creative Commons variant/version difference** — contradicted by the official 4.0 International legal code and the rest of the file identifying that exact license.
3. **Formatting-only drift** — contradicted by the inverted legal meaning of “may not … for NonCommercial purposes.”

## Why Previous Fixes Failed

No previous license repair was attempted. Earlier QA treated the manifest license identifier and provenance fields as sufficient. The validator checked labels, not the legal code bytes, so it could not detect semantic corruption inherited from the template.

## Unknowns

It is not yet known how many other AeroBeat repositories copied the same defective license. That broader inventory is outside this immediate Task 2 repair and should be tracked separately from the blocking gameplay-asset correction.

## Minimal Reproduction

Read `LICENSE.md` lines 99–102 and compare them with official Section 3 at `https://creativecommons.org/licenses/by-nc/4.0/legalcode.txt`. Run current `python3 tools/validate.py --root . --release 0.0.2`; it passes despite the contradiction, proving the validation gap.

## Proposed Verification

1. Replace `LICENSE.md` with the exact official 19,347-byte plain-text content.
2. Confirm SHA-256 equals `41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0`.
3. Add a validator constant/check for the exact expected license hash and test that a temporary one-byte mutation fails.
4. Re-run strict release, GLB-import, and reproducibility validation.
5. Prove `release/raw/0.0.1`, `review/0.0.1`, `release/raw/0.0.2`, and `review/0.0.2` are byte-unchanged.

## Recommended Fix

Use the official Creative Commons plain-text legal code verbatim, pin its SHA-256 in validation, and add a negative mutation test. Do not modify either immutable asset release or review evidence. File separate discovered work for the faulty template and any broader repository inventory rather than expanding this blocking repair unpredictably.

## Debugging Record

Problem: Public gameplay asset repo claims CC BY-NC 4.0 but contains contradictory legal text.
Observed symptom: Noncanonical Section 3(b) says Licensed Rights may not be exercised for NonCommercial purposes.
Root cause: Corrupted license inherited from `aerobeat-template-asset`, with no exact license-integrity validation.
Evidence: Identical clause in both repos; official 19,347-byte legal code SHA-256 `41003d4a...`; current validator still passes.
Failed approaches: Manifest-label/provenance-only license validation.
Corrective action: Replace with official text, pin exact hash, add negative mutation check, track template defect separately.
Verification test: Exact hash plus mutated-copy rejection and unchanged immutable release/review ledgers.
Related files/components: `LICENSE.md`, `tools/validate.py`, `aerobeat-template-asset/LICENSE.md`, Bead `k72.20`.
Remaining uncertainty: Number of other repositories carrying the same inherited defect.
