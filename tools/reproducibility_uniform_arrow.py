#!/usr/bin/env python3
"""Reproduce the staged uniform arrow in two disposable candidates only."""
from __future__ import annotations
import argparse, hashlib, json, shutil, sys, tempfile
from pathlib import Path
from subprocess_contract import run_checked

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory(root,relative):
    base=root/relative
    return {p.relative_to(base).as_posix():(p.stat().st_size,sha(p)) for p in sorted(base.rglob("*")) if p.is_file()}
def immutable(root):
    result={}
    for family in ("release/raw","review"):
        for version in [f"0.0.{number}" for number in range(1,9)]: result[f"{family}/{version}"]=inventory(root,Path(family)/version)
    return result
def prepare(authority,destination):
    (destination/"release/raw").mkdir(parents=True); (destination/"review").mkdir()
    shutil.copytree(authority/"release/raw/0.0.7",destination/"release/raw/0.0.7")
    for name in ("source","manifests","sets"): shutil.copytree(authority/name,destination/name)
    shutil.copyfile(authority/"LICENSE.md",destination/"LICENSE.md")
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--root",default="."); args=parser.parse_args(); root=Path(args.root).resolve(); blender=shutil.which("blender")
    if not blender: raise SystemExit("Blender missing")
    before=immutable(root)
    with tempfile.TemporaryDirectory(prefix="aerobeat-uniform-arrow-a-") as left_dir,tempfile.TemporaryDirectory(prefix="aerobeat-uniform-arrow-b-") as right_dir:
        builds=[Path(left_dir),Path(right_dir)]
        for build in builds:
            prepare(root,build)
            run_checked([blender,"--background","--factory-startup","--python",str(root/"tools/generate.py"),"--","--output-root",str(build),"--release","0.0.8"],operation=f"uniform arrow generation {build.name}",marker="GENERATE_OK release=0.0.8 assets=7 sources=10 manifests=10 release_files=17 review_pngs=68 review_metadata=5")
            run_checked([sys.executable,str(root/"tools/test_uniform_arrow.py"),"--authority-root",str(root),"--candidate-root",str(build),"--skip-staged-match"],operation=f"uniform arrow validation {build.name}",marker="UNIFORM_ARROW_OK geometry_bands=3 features=4 raster_checks=2592 adversaries=3 rotations=8 colors=3 scales=3 dprs=3 unchanged_glbs=6")
        # Runtime bytes are deterministic; Blender review PNG container bytes are
        # evidence only and retain the repository's existing non-reproducibility scope.
        compared=(Path("release/raw/0.0.8"),)
        for relative in compared:
            if inventory(builds[0],relative)!=inventory(builds[1],relative): raise AssertionError(f"nondeterministic candidate bytes: {relative}")
        manifest_relative=Path("manifests/directional-arrow/rounded-outline-v1.v1.json")
        documents=[json.loads((base/manifest_relative).read_text(encoding="utf-8")) for base in (root,*builds)]
        for document in documents:
            document["files"].pop("source_sha256"); document["files"].pop("source_bytes")
        if documents[0]!=documents[1] or documents[1]!=documents[2]: raise AssertionError("staged arrow manifest semantic drift")
    after=immutable(root)
    if before!=after: raise AssertionError("immutable raw/review 0.0.1-0.0.8 drift")
    print("UNIFORM_ARROW_REPRODUCIBILITY_OK builds=2 raw_files=17 review_evidence_files_each=73 immutable_trees=16")
if __name__=="__main__": main()
