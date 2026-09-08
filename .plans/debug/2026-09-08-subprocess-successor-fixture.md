# Legacy subprocess-contract fixture after wall successor

## Exact Observed Failure

`python3 tools/test_subprocess_contract.py --root .` failed because its copied fixture invoked the release-`0.0.7` validator against the newly prepared mutable `wall/red-glass-v1` source. The old validator stopped at `unchanged source mutated` before reaching the fake-Blender traceback scenario.

## Expected Behavior

The subprocess test must exercise fake Blender success/traceback/marker/fatal-output handling against the exact source state belonging to the legacy `0.0.7` validator. New wall-source preparation must be tested by the `0.0.10` validator instead.

## Execution Path

The test copies the current working source tree, invokes `validate.py --release 0.0.7`, and expects execution to reach smoke import. The copied current wall source now intentionally differs from the old release authority, so source-integrity validation fails first.

## Most Likely Root Cause

The test fixture conflates mutable latest source with the historical source authority required by the legacy validator. This surfaced only because wall keeps its canonical variant name while removing the edge cage.

## Alternative Hypotheses

- Subprocess fatal-signature detection regressed: contradicted; it never ran.
- Candidate wall source is accidentally dirty: contradicted by exact generated hash and focused wall validation.

## Why Previous Fixes Failed

No subprocess fix was attempted. The old test passed before the intentional same-identity wall-source successor.

## Unknowns

None. Git `HEAD` still contains the exact pre-successor wall source, manifest, and set.

## Minimal Reproduction

Run the subprocess-contract test with the prepared wall source in the worktree.

## Proposed Verification

Materialize the legacy wall source/manifest/set from authority `HEAD` into each disposable fixture before invoking the old validator. All fake Blender scenarios must then reach and verify the subprocess contract.

## Recommended Fix

Update only fixture setup; do not weaken historical source checks in `validate.py`. The new focused validator remains responsible for `0.0.10`.

## Debugging Record

```text
Problem: Legacy subprocess test fails before testing subprocess behavior.
Observed symptom: 0.0.7 validator reports current wall source mutated.
Root cause: Disposable fixture copied latest same-identity source instead of legacy authority state.
Evidence: Stack ends at source SHA check; fake Blender is never called.
Failed approaches: None.
Corrective action: Restore three legacy tracked files from authority HEAD inside fixture.
Verification test: tools/test_subprocess_contract.py passes all fake Blender scenarios.
Related files/components: tools/test_subprocess_contract.py, validate.py, wall source/manifest/set.
Remaining uncertainty: None.
```

## Follow-up: archived authority lacks `.git`

The first fixture correction used `git archive` for exact legacy bytes. The validator then failed before fake Blender because ordinary mode also asks Git for immutable-tree identity, and archives intentionally contain no `.git`. This is a fixture-mode mismatch, not a product or subprocess defect. The existing hidden `--generated-fixture` switch disables only redundant Git/review authority checks while retaining source, release, and smoke behavior; reproducibility already uses that switch for its own disposable copies. The minimal correction is to pass `--generated-fixture` to this direct archived-fixture validator call. Verification remains all three exact fake-Blender failure signatures.

The hidden fixture flag cannot be used here because it intentionally requires `--no-smoke`, while this test must reach smoke import. Therefore the correct fixture is an exact legacy archive initialized as a local disposable Git repository with one commit. That preserves exact tree bytes and gives the historical validator the Git tree interface it requires, without a worktree or canonical mutation. Remove the hidden flag and initialize/commit the archive before fake scenarios.
