#!/usr/bin/env python3
"""One-shot canonical 0.0.11 tint-dominant marker release builder."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
from subprocess_contract import run_checked

RELEASE = "0.0.11"
PREDECESSOR = "0.0.10"
APPROVED_COMMIT = "7bd1e3eb37f62b84f3f8438696231ed0c7907ba1"
APPROVED_TREE = "7303f49ea189f133530525ae5f6b687f09b2591c"
EXPECTED_INVENTORY = "e65571211e7a5a44224c378dbb654afd56263dc37f427a9b3f0af6453a6f1d23"
EXPECTED_PROOF = "0c194b1a8f290cfe387ee34154199cc0758ace8baf9b60fa4a3beb5bdddf4227"
EXPECTED_RAW = (17, 513415, "c4d44f91ed4c77e03911c0a6e9000b8cbe036fad523321e9f081146bdaee55ad")
EXPECTED_REVIEW = (88, 94500403, "83decde469e37591af86b52f0bd5dc28c4dfe1469d466ca30c1aa40af5dc97a6")
EXPECTED_REVIEW_HASHES = "b8f0fda36dc210e78ccdf09d90baa3293704975af2f756afe9405f99afa4e0d9"
EXPECTED_MARKER = "f376934f218a25c11f2f31928c67684611aaf9c73aa1724548682ae280b5cbcc"
ROLES = {"directional-arrow": "rounded-outline-v1", "any-note": "outlined-circle-v1", "guard": "outlined-shield-v1", "bomb": "urchin-v1", "wall": "red-glass-v1", "track": "blue-glass-v1", "athlete-marker": "sphere-v1"}


def fail(message): raise SystemExit(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def tree(base):
    files = sorted(p for p in base.rglob("*") if p.is_file())
    rows = "".join(f"{p.relative_to(base).as_posix()}\0{p.stat().st_size}\0{sha(p)}\n" for p in files)
    return len(files), sum(p.stat().st_size for p in files), hashlib.sha256(rows.encode()).hexdigest()
def chmod_tree(base):
    for path in base.rglob("*"): os.chmod(path, 0o555 if path.is_dir() else 0o444)
    os.chmod(base, 0o555)
def remove_stage(stage):
    for path in sorted((p for p in stage.rglob("*") if p.is_dir()), reverse=True): os.chmod(path, 0o700)
    os.chmod(stage, 0o700); shutil.rmtree(stage)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--release", required=True, choices=[RELEASE]); a = ap.parse_args()
    root = Path(a.root).resolve()
    raw = root / "release/raw" / RELEASE; review = root / "review" / RELEASE; stage = root / f".canonical-{RELEASE}-staging"
    actual_tree = subprocess.check_output(["git", "rev-parse", f"{APPROVED_COMMIT}^{{tree}}"], cwd=root, text=True).strip()
    if actual_tree != APPROVED_TREE: fail("approved source tree mismatch")
    inputs = subprocess.run(["git", "diff", "--exit-code", APPROVED_COMMIT, "--", "tools/generate.py", "source", "manifests", "sets", "LICENSE.md"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if inputs.returncode: fail("generation inputs differ from audited authority\n" + inputs.stdout)
    if raw.exists() or review.exists(): fail(f"canonical successor already exists: raw={raw.exists()} review={review.exists()}; never regenerate")
    if stage.exists(): fail(f"canonical staging state exists at {stage}; inspect/recover, never regenerate")
    blender = shutil.which("blender")
    if not blender: fail("Blender missing")
    (stage / "release/raw").mkdir(parents=True); (stage / "review").mkdir()
    shutil.copytree(root / "release/raw" / PREDECESSOR, stage / "release/raw" / PREDECESSOR)
    for name in ("source", "manifests", "sets"): shutil.copytree(root / name, stage / name)
    shutil.copy2(root / "LICENSE.md", stage / "LICENSE.md")
    marker = f"GENERATE_OK release={RELEASE} assets=7 sources=10 manifests=10 release_files=17 review_pngs=83 review_metadata=5"
    output = run_checked([blender, "--background", "--factory-startup", "--python", str(root / "tools/generate.py"), "--", "--output-root", str(stage), "--release", RELEASE, "--source-commit", APPROVED_COMMIT, "--source-tree", APPROVED_TREE], operation="single canonical tint-dominant marker generation", marker=marker, postcondition=lambda: (stage / "release/raw" / RELEASE).is_dir() and (stage / "review" / RELEASE).is_dir()); print(output, end="")
    staged_raw = stage / "release/raw" / RELEASE; staged_review = stage / "review" / RELEASE
    actual = {"inventory": sha(staged_raw / "inventory.v1.json"), "proof": sha(staged_raw / "proof.v1.json"), "raw": tree(staged_raw), "review": tree(staged_review), "reviewHashes": sha(staged_review / "hashes.v1.json"), "marker": sha(staged_raw / "athlete-marker/sphere-v1.glb")}
    expected = {"inventory": EXPECTED_INVENTORY, "proof": EXPECTED_PROOF, "raw": EXPECTED_RAW, "review": EXPECTED_REVIEW, "reviewHashes": EXPECTED_REVIEW_HASHES, "marker": EXPECTED_MARKER}
    if actual != expected: fail(f"canonical candidate differs from audited anchors; preserve {stage}: {actual}")
    subprocess.run([sys.executable, str(root / "tools/validate_marker_candidate.py"), "--authority-root", str(root), "--candidate-root", str(stage), "--source-commit", APPROVED_COMMIT, "--source-tree", APPROVED_TREE, ], check=True)
    for role, variant in ROLES.items():
        canonical = f"{role}/{variant}"; path = staged_raw / role / f"{variant}.glb"
        run_checked([blender, "--background", "--factory-startup", "--python", str(root / "tools/smoke_import.py"), "--", str(path), canonical], operation=f"canonical candidate smoke {canonical}", marker=f"SMOKE_OK kind=glb identity={canonical}", postcondition=lambda p=path: p.is_file())
    state = {"schema": "aerobeat.canonical-generation-state/v1", "release": RELEASE, "source_commit": APPROVED_COMMIT, "source_tree": APPROVED_TREE, "inventory_sha256": EXPECTED_INVENTORY, "proof_sha256": EXPECTED_PROOF, "generation_count": 1}
    (stage / "generation-complete.json").write_text(json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n")
    try:
        staged_raw.rename(raw); staged_review.rename(review)
    except Exception as error: fail(f"promotion incomplete; recover {stage}, never regenerate: {error}")
    # Promote the regenerated editable marker snapshot (blend container bytes are not claimed deterministic).
    new_blend = stage / "source/athlete-marker/sphere-v1/sphere-v1.blend"
    if new_blend.is_file():
        shutil.copy2(new_blend, root / "source/athlete-marker/sphere-v1/sphere-v1.blend")
    chmod_tree(raw); chmod_tree(review); remove_stage(stage)
    print(f"CANONICAL_BUILD_OK release={RELEASE} generation_count=1 inventory_sha256={EXPECTED_INVENTORY} proof_sha256={EXPECTED_PROOF}")


if __name__ == "__main__": main()
