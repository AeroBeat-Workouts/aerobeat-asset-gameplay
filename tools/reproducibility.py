#!/usr/bin/env python3
"""Build twice in independent temporary roots and require byte identity."""
from __future__ import annotations
import argparse, hashlib, os, shutil, subprocess, sys, tempfile
from pathlib import Path

# Blender .blend snapshots and rendered PNGs are intentionally outside the byte-
# deterministic contract. The complete immutable raw release is authoritative.
AREAS=("release",)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):
 return {p.relative_to(root).as_posix():(p.stat().st_size,digest(p)) for area in AREAS for p in sorted((root/area).rglob("*")) if p.is_file()}
def run(cmd):
 cp=subprocess.run(cmd,text=True,capture_output=True)
 if cp.returncode:
  print(cp.stdout); print(cp.stderr,file=sys.stderr); raise SystemExit(cp.returncode)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); a=ap.parse_args(); root=Path(a.root).resolve()
 blender=shutil.which("blender")
 if not blender: raise SystemExit("Blender not found")
 if subprocess.run([blender,"--version"],capture_output=True,text=True,check=True).stdout.splitlines()[0]!="Blender 4.0.2": raise SystemExit("Blender 4.0.2 required")
 with tempfile.TemporaryDirectory(prefix="aerobeat-repro-a-") as ad, tempfile.TemporaryDirectory(prefix="aerobeat-repro-b-") as bd:
  builds=[Path(ad),Path(bd)]; link=Path(tempfile.gettempdir())/f"aerobeat-gameplay-repro-{os.getpid()}"
  try:
   for dest in builds:
    link.symlink_to(dest,target_is_directory=True)
    run([blender,"--background","--factory-startup","--python",str(root/"tools/generate.py"),"--","--output-root",str(link)])
    link.unlink()
    run([sys.executable,str(root/"tools/validate.py"),"--root",str(dest),"--release","0.0.1","--no-smoke"])
  finally:
   if link.is_symlink(): link.unlink()
  ia,ib=inventory(builds[0]),inventory(builds[1]); primary=inventory(root)
  if ia!=ib or primary!=ia:
   bad=[k for k in sorted(set(primary)|set(ia)|set(ib)) if not (primary.get(k)==ia.get(k)==ib.get(k))]
   raise SystemExit("NONDETERMINISTIC release files:\n  "+"\n  ".join(bad))
  print(f"REPRODUCIBLE {len(ia)} immutable release files; primary plus two independent temporary builds are byte-identical")

if __name__=="__main__": main()
