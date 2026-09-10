#!/usr/bin/env python3
"""Candidate-only reproducibility gate for the tint-dominant 0.0.11 marker release.

Generates two independent isolated candidates, requires every raw and review file to
match byte-for-byte between them, and confirms three identical semantic Blender source
fingerprints. Never touches a canonical release path or the authority predecessor.
"""
from __future__ import annotations
import argparse, hashlib, shutil, subprocess, sys, tempfile
from pathlib import Path

RELEASE = "0.0.11"
PREDECESSOR = "0.0.10"
MARKER_SOURCE = "source/athlete-marker/sphere-v1/sphere-v1.blend"


def fail(message): raise SystemExit(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stage(root, tag):
    """Build an isolated disposable candidate root under /tmp."""
    cand = Path(tempfile.mkdtemp(prefix=f"aerobeat-{RELEASE}-{tag}-"))
    (cand / "release/raw").mkdir(parents=True)
    shutil.copytree(root / "release/raw" / PREDECESSOR, cand / "release/raw" / PREDECESSOR)
    for name in ("source", "manifests", "sets"):
        shutil.copytree(root / name, cand / name)
    shutil.copy2(root / "LICENSE.md", cand / "LICENSE.md")
    return cand


def generate(blender, root, cand, commit, tree):
    marker = f"GENERATE_OK release={RELEASE} assets=7 sources=10 manifests=10 release_files=17 review_pngs=83 review_metadata=5"
    cmd = [blender, "--background", "--factory-startup", "--python", str(root / "tools/generate.py"), "--", "--output-root", str(cand), "--release", RELEASE, "--source-commit", commit, "--source-tree", tree]
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = completed.stdout or ""
    if completed.returncode != 0: fail(f"generation failed rc={completed.returncode}\n{output}")
    if output.count(marker) != 1: fail(f"expected exactly one completion marker\n{output}")
    if not (cand / "release/raw" / RELEASE).is_dir() or not (cand / "review" / RELEASE).is_dir(): fail("generation did not create release+review trees")


def tree_digest(base):
    files = sorted(p for p in base.rglob("*") if p.is_file())
    rows = "".join(f"{p.relative_to(base).as_posix()}\0{p.stat().st_size}\0{sha(p)}\n" for p in files)
    return len(files), sum(p.stat().st_size for p in files), hashlib.sha256(rows.encode()).hexdigest()


def fingerprint(blender, blend_path, out_json):
    script = str((Path(__file__).resolve().parent) / "blender_scene_fingerprint.py")
    cmd = [blender, "--background", "--factory-startup", "--python", script, "--", str(blend_path), str(out_json)]
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if completed.returncode != 0: fail(f"fingerprint failed\n{completed.stdout}")
    if not Path(out_json).is_file(): fail("fingerprint output missing")
    return sha(out_json)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--source-commit", required=True); ap.add_argument("--source-tree", required=True); a = ap.parse_args()
    root = Path(a.root).resolve()
    blender = shutil.which("blender")
    if not blender: fail("Blender missing")
    if (root / "release/raw" / RELEASE).exists() or (root / "review" / RELEASE).exists(): fail(f"canonical {RELEASE} already exists; this is a candidate-only gate")
    temps = []
    try:
        cand_a = stage(root, "a"); temps.append(cand_a)
        cand_b = stage(root, "b"); temps.append(cand_b)
        for cand in (cand_a, cand_b):
            generate(blender, root, cand, a.source_commit, a.source_tree)
        # Two independent builds must match byte-for-byte across raw and review.
        for sub in ("release/raw/" + RELEASE, "review/" + RELEASE):
            da = tree_digest(cand_a / sub); db = tree_digest(cand_b / sub)
            if da != db: fail(f"{sub} differs between isolated builds: A={da} B={db}")
            print(f"IDENTICAL {sub}: {da[0]} files / {da[1]} bytes / {da[2]}")
        # Three identical semantic Blender source fingerprints (two staged + authority working copy).
        fps = set()
        for tag, src in (("a", cand_a / MARKER_SOURCE), ("b", cand_b / MARKER_SOURCE), ("auth", root / MARKER_SOURCE)):
            out_json = Path(tempfile.mkstemp(prefix=f"fp-{tag}-")[1])
            try:
                fps.add(fingerprint(blender, src, out_json))
            finally:
                out_json.unlink(missing_ok=True)
        if len(fps) != 1: fail(f"marker source fingerprint not stable across builds: {len(fps)} distinct values")
        print("IDENTICAL marker source semantic fingerprint x3:", fps.pop()[:16], "...")
        print(f"REPRODUCIBLE_OK release={RELEASE} raw+review byte-identical across two isolated builds; source fingerprint stable x3")
    finally:
        for cand in temps:
            shutil.rmtree(cand, ignore_errors=True)


if __name__ == "__main__": main()
