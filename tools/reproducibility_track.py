#!/usr/bin/env python3
"""Two disposable Blender 4.0.2 builds and full byte comparison for track-only 0.0.12."""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from subprocess_contract import run_checked
from validate_track_candidate import digest, sha

RELEASE = "0.0.12"
PREDECESSOR = "0.0.11"
MARKER = "GENERATE_OK release=0.0.12 assets=7 sources=10 manifests=10 release_files=17 review_pngs=83 review_metadata=5"
TRACK_SOURCE = "source/track/blue-glass-v1/blue-glass-v1.blend"


def check(value, message):
    if not value: raise AssertionError(message)


def stage(root):
    candidate = Path(tempfile.mkdtemp(prefix="aerobeat-track-0.0.12-"))
    (candidate / "release/raw").mkdir(parents=True)
    shutil.copytree(root / f"release/raw/{PREDECESSOR}", candidate / f"release/raw/{PREDECESSOR}")
    for sub in ("source", "manifests", "sets"):
        shutil.copytree(root / sub, candidate / sub)
    shutil.copy2(root / "LICENSE.md", candidate / "LICENSE.md")
    return candidate


def fingerprint(blender, root, source):
    with tempfile.TemporaryDirectory(prefix="aerobeat-track-fingerprint-") as scratch:
        target = Path(scratch) / "scene.json"
        marker = "SCENE_FINGERPRINT_OK"
        script = root / "tools/blender_scene_fingerprint.py"
        output = run_checked([blender, "--background", "--factory-startup", "--python", str(script), "--", str(source), str(target)], operation="track semantic fingerprint", marker=marker, postcondition=lambda: target.is_file())
        return sha(target)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="."); ap.add_argument("--source-commit", required=True); ap.add_argument("--source-tree", required=True)
    args = ap.parse_args(); root = Path(args.root).resolve()
    check(not (root / f"release/raw/{RELEASE}").exists() and not (root / f"review/{RELEASE}").exists(), "candidate-only gate refuses finalized canonical targets")
    blender = shutil.which("blender")
    check(blender and subprocess.check_output([blender, "--version"], text=True).splitlines()[0] == "Blender 4.0.2", "Blender 4.0.2 required")
    candidates = []
    try:
        for _ in range(2):
            candidate = stage(root); candidates.append(candidate)
            cmd = [blender, "--background", "--factory-startup", "--python", str(root / "tools/generate.py"), "--", "--output-root", str(candidate), "--release", RELEASE, "--source-commit", args.source_commit, "--source-tree", args.source_tree]
            run_checked(cmd, operation="disposable track generation", marker=MARKER, postcondition=lambda: (candidate / f"release/raw/{RELEASE}/track/blue-glass-v1.glb").is_file() and (candidate / f"review/{RELEASE}/hashes.v1.json").is_file())
            validator = [sys.executable, str(root / "tools/validate_track_candidate.py"), "--authority-root", str(root), "--candidate-root", str(candidate), "--source-commit", args.source_commit, "--source-tree", args.source_tree, "--smoke"]
            completed = subprocess.run(validator, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            check(completed.returncode == 0 and '\"pass\": true' in completed.stdout and '\"blender_smoke\": true' in completed.stdout, f"candidate strict gate failed:\n{completed.stdout}")
        result = {}
        for sub in (f"release/raw/{RELEASE}", f"review/{RELEASE}"):
            a = digest(candidates[0] / sub); b = digest(candidates[1] / sub)
            check(a == b, f"non-reproducible tree {sub}: {a} != {b}")
            for p in (candidates[0] / sub).rglob("*"):
                if p.is_file():
                    relative = p.relative_to(candidates[0] / sub)
                    check(p.read_bytes() == (candidates[1] / sub / relative).read_bytes(), f"non-reproducible file {sub}/{relative}")
            result[sub] = {"files": a[0], "bytes": a[1], "digest": a[2]}
        source_fingerprints = [fingerprint(blender, root, cand / TRACK_SOURCE) for cand in candidates]
        check(source_fingerprints[0] == source_fingerprints[1], "Blender track source semantic drift")
        print(json.dumps({"release": RELEASE, "reproducible": True, "trees": result, "source_fingerprint": source_fingerprints[0]}, sort_keys=True))
    finally:
        for cand in candidates:
            shutil.rmtree(cand)


if __name__ == "__main__": main()
