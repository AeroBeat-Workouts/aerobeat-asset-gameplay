#!/usr/bin/env python3
"""Generate and compare two isolated uniform-wall 0.0.10 candidates."""
from __future__ import annotations
import argparse,hashlib,io,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
from subprocess_contract import run_checked

RELEASE="0.0.10"
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory(root):return [(path.relative_to(root).as_posix(),path.stat().st_size,sha(path)) for path in sorted(root.rglob("*")) if path.is_file()]
def run(root,destination,commit,tree):
 archive=subprocess.check_output(["git","archive","--format=tar",commit],cwd=root)
 with tarfile.open(fileobj=io.BytesIO(archive),mode="r:") as bundle:bundle.extractall(destination,filter="data")
 command=[shutil.which("blender") or "blender","--background","--factory-startup","--python",str(destination/"tools/generate.py"),"--","--output-root",str(destination),"--release",RELEASE,"--source-commit",commit,"--source-tree",tree]
 marker="GENERATE_OK release=0.0.10 assets=7 sources=10 manifests=10 release_files=17 review_pngs=83 review_metadata=5"
 run_checked(command,operation=f"isolated uniform-wall generation {destination.name}",marker=marker,postcondition=lambda:(destination/"release/raw"/RELEASE/"wall/red-glass-v1.glb").is_file())
 subprocess.run([sys.executable,str(destination/"tools/validate_uniform_wall_candidate.py"),"--authority-root",str(root),"--candidate-root",str(destination),"--source-commit",commit,"--source-tree",tree],check=True)
def fingerprint(root,source,output):
 run_checked([shutil.which("blender") or "blender","--background","--factory-startup","--python",str(root/"tools/blender_scene_fingerprint.py"),"--",str(source),str(output)],operation=f"wall semantic fingerprint {source}",marker="SCENE_FINGERPRINT_OK",postcondition=lambda:output.is_file())
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");a=ap.parse_args();root=Path(a.root).resolve()
 if subprocess.check_output(["git","status","--porcelain"],cwd=root,text=True).strip():raise SystemExit("uniform-wall reproducibility requires a clean source authority")
 commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip();tree=subprocess.check_output(["git","rev-parse","HEAD^{tree}"],cwd=root,text=True).strip()
 with tempfile.TemporaryDirectory(prefix="aerobeat-wall-repro-") as directory:
  base=Path(directory);left=base/"left";right=base/"right";left.mkdir();right.mkdir();run(root,left,commit,tree);run(root,right,commit,tree)
  raw_left=inventory(left/"release/raw"/RELEASE);raw_right=inventory(right/"release/raw"/RELEASE);review_left=inventory(left/"review"/RELEASE);review_right=inventory(right/"review"/RELEASE)
  if raw_left!=raw_right:raise AssertionError("uniform-wall raw candidates are not byte-identical")
  if review_left!=review_right:raise AssertionError("uniform-wall review candidates are not byte-identical")
  outputs=[base/name for name in ("authority.json","left.json","right.json")];sources=[root/"source/wall/red-glass-v1/red-glass-v1.blend",left/"source/wall/red-glass-v1/red-glass-v1.blend",right/"source/wall/red-glass-v1/red-glass-v1.blend"]
  for source,output in zip(sources,outputs):fingerprint(root,source,output)
  documents=[json.loads(path.read_text()) for path in outputs]
  if documents[0]!=documents[1] or documents[0]!=documents[2]:raise AssertionError("wall semantic source fingerprints differ")
  print(json.dumps({"oracle":"uniform-wall-reproducibility","release":RELEASE,"sourceCommit":commit,"sourceTree":tree,"rawFiles":len(raw_left),"reviewFiles":len(review_left),"wallSha256":dict((name,digest) for name,_,digest in raw_left)["wall/red-glass-v1.glb"],"semanticFingerprint":sha(outputs[0]),"pass":True},sort_keys=True))
if __name__=="__main__":main()
