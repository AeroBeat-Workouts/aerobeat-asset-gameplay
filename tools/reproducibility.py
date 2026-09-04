#!/usr/bin/env python3
"""Build twice in independent temporary roots and require byte identity."""
from __future__ import annotations
import argparse, hashlib, os, shutil, sys, tempfile
from pathlib import Path

from subprocess_contract import run_checked

# Blender .blend snapshots and rendered PNGs are intentionally outside the byte-
# deterministic contract. The complete immutable raw release is authoritative.
SUPPORTED_RELEASE="0.0.5"
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root,release):
 base=root/"release"/"raw"/release
 return {p.relative_to(base).as_posix():(p.stat().st_size,digest(p)) for p in sorted(base.rglob("*")) if p.is_file()}
ASSETS=(
 ("directional-arrow","outline-v1"),("any-note","circle-v1"),("guard","shield-v1"),
 ("bomb","urchin-v1"),("wall","red-glass-v1"),("track","blue-glass-v1"),
 ("athlete-marker","sphere-v1"),
)
def assert_build_postconditions(root,release):
 rel=root/"release"/"raw"/release
 expected_release={"inventory.v1.json","proof.v1.json","sets/default-v1.json"}|{path for role,variant in ASSETS for path in (f"{role}/{variant}.glb",f"manifests/{role}/{variant}.v1.json")}
 expected_sources={f"{role}/{variant}/{variant}.blend" for role,variant in ASSETS}
 expected_manifests={f"{role}/{variant}.v1.json" for role,variant in ASSETS}
 expected_pngs={"neutral-board.png","gameplay-context.png","wall-grid-comparison.png","visibility-comparison.png","directional-arrow--outline-v1--plus-z-bright.png","directional-arrow--outline-v1--minus-z-bright.png"}|{f"{role}--{variant}.png" for role,variant in ASSETS}
 actual_release={p.relative_to(rel).as_posix() for p in rel.rglob("*") if p.is_file()}
 actual_sources={p.relative_to(root/"source").as_posix() for p in (root/"source").rglob("*") if p.is_file()}
 actual_manifests={p.relative_to(root/"manifests").as_posix() for p in (root/"manifests").rglob("*") if p.is_file()}
 review=root/"review"/release
 actual_pngs={p.name for p in review.glob("*.png")}; actual_metadata={p.name for p in review.glob("*.json")}
 if actual_release!=expected_release: raise AssertionError(f"release inventory {sorted(actual_release)}")
 if actual_sources!=expected_sources: raise AssertionError(f"source inventory {sorted(actual_sources)}")
 if actual_manifests!=expected_manifests: raise AssertionError(f"manifest inventory {sorted(actual_manifests)}")
 if {p.name for p in (root/"sets").glob("*.json")}!={"default-v1.json"}: raise AssertionError("set inventory")
 if actual_pngs!=expected_pngs or actual_metadata!={"hashes.v1.json","layout.v1.json","visibility.v1.json","contrast.v1.json","wall-grid.v1.json"}: raise AssertionError("review inventory")
 return True

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--release",required=True,choices=[SUPPORTED_RELEASE]); a=ap.parse_args(); root=Path(a.root).resolve()
 blender=shutil.which("blender")
 if not blender: raise SystemExit("Blender not found")
 run_checked([blender,"--version"],operation="Blender version",marker="Blender 4.0.2")
 with tempfile.TemporaryDirectory(prefix="aerobeat-repro-a-") as ad, tempfile.TemporaryDirectory(prefix="aerobeat-repro-b-") as bd:
  builds=[Path(ad),Path(bd)]; link=Path(tempfile.gettempdir())/f"aerobeat-gameplay-repro-{os.getpid()}"
  try:
   for dest in builds:
    for relative in ("release/raw/0.0.1","release/raw/0.0.2","release/raw/0.0.3","release/raw/0.0.4","review/0.0.1","review/0.0.2","review/0.0.3","review/0.0.4"):
     shutil.copytree(root/relative,dest/relative)
    for relative in ("directional-arrow/outline-v1/outline-v1.blend","any-note/circle-v1/circle-v1.blend","athlete-marker/sphere-v1/sphere-v1.blend","bomb/urchin-v1/urchin-v1.blend","guard/shield-v1/shield-v1.blend","track/blue-glass-v1/blue-glass-v1.blend"):
     target=dest/"source"/relative; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(root/"source"/relative,target)
    link.symlink_to(dest,target_is_directory=True)
    run_checked(
     [blender,"--background","--factory-startup","--python",str(root/"tools/generate.py"),"--","--output-root",str(link),"--release",a.release],
     operation=f"Blender generation {dest.name}",
     marker="GENERATE_OK release=0.0.5 assets=7 sources=7 manifests=7 release_files=17 review_pngs=13 review_metadata=5",
     postcondition=lambda dest=dest: assert_build_postconditions(dest,a.release),
    )
    link.unlink()
    shutil.copyfile(root/"LICENSE.md",dest/"LICENSE.md")
    run_checked(
     [sys.executable,str(root/"tools/validate.py"),"--root",str(dest),"--release",a.release,"--no-smoke"],
     operation=f"strict temporary validation {dest.name}",
     marker=f"VALIDATE_OK release={a.release} assets=7 release_files=17 smoke=0",
     postcondition=lambda dest=dest: assert_build_postconditions(dest,a.release),
    )
  finally:
   if link.is_symlink(): link.unlink()
  ia,ib=inventory(builds[0],a.release),inventory(builds[1],a.release); primary=inventory(root,a.release)
  if ia!=ib or primary!=ia:
   bad=[k for k in sorted(set(primary)|set(ia)|set(ib)) if not (primary.get(k)==ia.get(k)==ib.get(k))]
   raise SystemExit("NONDETERMINISTIC release files:\n  "+"\n  ".join(bad))
  print(f"REPRODUCIBLE {len(ia)} immutable release files; primary plus two independent temporary builds are byte-identical")
  print(f"REPRODUCIBILITY_OK release={a.release} files={len(ia)} builds=2")

if __name__=="__main__": main()
