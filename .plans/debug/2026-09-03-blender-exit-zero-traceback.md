# Blender exit-zero traceback certification gap

## Exact Observed Failure

QA ran Blender 4.0.2 with an uncaught Python exception. Blender printed `Traceback ... RuntimeError: QA_SENTINEL_TRACEBACK` but returned process code `0`. A fake `blender` reporting version 4.0.2 and then returning `0` with `Traceback ... RuntimeError: QA_MASKED_IMPORT_FAILURE` caused `tools/validate.py` to return `0` and claim `clean Blender imports`.

The vulnerable checks are `tools/validate.py` smoke execution and `tools/reproducibility.py::run`, both of which accept subprocess success solely from `returncode == 0`.

## Expected Behavior

Every Blender-backed operation must fail closed unless combined stdout/stderr has no uncaught-error signature, return code is zero, exactly one operation-specific completion marker is present, and the caller verifies the expected filesystem/inventory postcondition. Source and GLB smoke operations must bind their marker to the exact canonical identity.

## Execution Path

1. Validator locates a binary named `blender` and accepts its version line.
2. Validator invokes `smoke_import.py` for each GLB.
3. Blender catches the script failure at its process boundary, prints an uncaught traceback, and nevertheless exits zero.
4. Validator checks only `cp.returncode`; it never inspects output or requires the script's `SMOKE_OK` line.
5. Reproducibility uses the same return-code-only assumption for generator and nested validator commands.
6. Therefore a missing operation can be certified whenever Blender exits zero after reporting the failure text.

## Most Likely Root Cause

The tools equate OS process return code with successful Blender script completion. On this exact Blender package that assumption is false. The absence of a required marker and output-signature scan leaves no independent proof that Python reached the operation's final line.

## Alternative Hypotheses

- A malformed GLB caused the QA result: contradicted by reproduction with a fake Blender that never reads a GLB.
- The smoke script does not emit a marker: contradicted by its existing `SMOKE_OK` print; the caller simply ignores it.
- This affects only smoke imports: contradicted by the identical return-code-only runner around generation in reproducibility.

## Why Previous Fixes Failed

No prior subprocess-contract repair exists. Strict inventory and hash checks can catch many incomplete builds, but they do not prove the invoked operation completed when stale or partially created output already exists. Return-code checks treated a Blender packaging behavior as a reliable contract.

## Unknowns

Other Blender messages may use additional fatal signatures. The repair will cover the observed traceback/Python-error/uncaught/unhandled forms and make exact completion markers plus postconditions authoritative even when an unrecognized diagnostic appears.

## Minimal Reproduction

Run `blender --background --factory-startup --python-expr 'raise RuntimeError("QA_SENTINEL_TRACEBACK")'`. Observe an uncaught traceback and return code zero. Replace Blender on `PATH` with an rc0 script printing a traceback; current strict validation still passes.

## Proposed Verification

Use one shared subprocess helper for version, source smoke, GLB smoke, generation, and nested validation. Test fake executables that return zero with a traceback, no marker, or a wrong marker. Each must fail. Then run all seven real source opens, seven real GLB imports, strict finalized validation, and two fresh reproducibility builds.

## Recommended Fix

Add a standard-library shared subprocess contract that combines stdout/stderr, requires zero return code, rejects fatal signatures, requires exactly one exact marker line, and invokes a caller-owned postcondition. Add exact identity-bound markers to source/GLB smoke scripts and a generator marker emitted only after exact source/manifest/set/release/review inventories exist. Make reproducibility require both generator and validator markers plus full inventories before byte comparison. Preserve all authored and immutable asset bytes.

## Debugging Record

Problem: Blender rc0 can mask uncaught script failures.
Observed symptom: Fake Blender rc0+Traceback is certified as clean import.
Root cause: Validator/repro runner trust return code without output marker/signature/postcondition checks.
Evidence: QA real-Blender and fake-Blender reproductions; vulnerable call sites.
Failed approaches: Return-code-only subprocess acceptance.
Corrective action: One shared fail-closed subprocess contract with exact markers and postconditions.
Verification test: Three rc0 fake-Blender adversaries fail; real source/GLB smoke and two builds pass.
Related files/components: `tools/validate.py`, `tools/reproducibility.py`, `tools/generate.py`, smoke scripts.
Remaining uncertainty: Future fatal signature variants, mitigated by exact markers and postconditions.
