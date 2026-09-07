#!/usr/bin/env python3
"""Build rounded 0.0.8 twice in disposable roots; never create canonical release paths."""
from __future__ import annotations
import argparse, hashlib, shutil, sys, tempfile
from pathlib import Path
from subprocess_contract import run_checked

def inventory(root):
 base=root/"release/raw/0.0.8"
 return {p.relative_to(base).as_posix():(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(base.rglob("*")) if p.is_file()}
def prepare(authority,destination):
 (destination/"release/raw").mkdir(parents=True); (destination/"review").mkdir()
 shutil.copytree(authority/"release/raw/0.0.7",destination/"release/raw/0.0.7")
 for name in ("source","manifests","sets"): shutil.copytree(authority/name,destination/name)
 shutil.copyfile(authority/"LICENSE.md",destination/"LICENSE.md")
def main():
 parser=argparse.ArgumentParser(); parser.add_argument("--root",default="."); args=parser.parse_args(); root=Path(args.root).resolve(); blender=shutil.which("blender")
 if not blender: raise SystemExit("Blender missing")
 if (root/"release/raw/0.0.8").exists() or (root/"review/0.0.8").exists(): raise SystemExit("canonical 0.0.8 must remain absent")
 with tempfile.TemporaryDirectory(prefix="aerobeat-rounded-repro-a-") as first, tempfile.TemporaryDirectory(prefix="aerobeat-rounded-repro-b-") as second:
  builds=[Path(first),Path(second)]
  for build in builds:
   prepare(root,build)
   run_checked([blender,"--background","--factory-startup","--python",str(root/"tools/generate.py"),"--","--output-root",str(build),"--release","0.0.8"],operation=f"rounded generation {build.name}",marker="GENERATE_OK release=0.0.8 assets=7 sources=10 manifests=10 release_files=17 review_pngs=68 review_metadata=5")
   run_checked([sys.executable,str(root/"tools/validate_rounded_candidate.py"),"--authority-root",str(root),"--candidate-root",str(build)],operation=f"rounded validation {build.name}",marker="ROUNDED_VALIDATE_OK release=0.0.8 cues=3 unchanged=4")
  left,right=inventory(builds[0]),inventory(builds[1])
  if left!=right:
   changed=[name for name in sorted(set(left)|set(right)) if left.get(name)!=right.get(name)]
   raise SystemExit("NONDETERMINISTIC rounded candidate:\n  "+"\n  ".join(changed))
  print(f"ROUNDED_REPRODUCIBILITY_OK release=0.0.8 files={len(left)} builds=2 canonical_release_absent=1")
if __name__=="__main__": main()
