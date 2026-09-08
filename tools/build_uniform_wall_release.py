#!/usr/bin/env python3
"""One-shot canonical 0.0.10 uniform-wall release builder."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
from subprocess_contract import run_checked

RELEASE="0.0.10";PREDECESSOR="0.0.9"
APPROVED_COMMIT="f7aac5236dabd6f7716ec2f17459e5669eb335b3";APPROVED_TREE="faf799b7e7e5c05d5865d31f885b344e65f66815"
EXPECTED_INVENTORY="a8eb2ea1306a6bf760b66b835d4b0dd3359601b46b1df682fe3805ee7e7e2bc8";EXPECTED_PROOF="017a6c0efaf48f85130380d774502f25785783a7ad69d400f8c0f2275855c242"
EXPECTED_RAW=(17,427876,"839f38302fbe490732d94eec4fcb867f112ddc4c063b14e1034082078c327d2c");EXPECTED_REVIEW=(88,94621710,"86ff93353e27f3562dfb33583f6e031953893a47c9f890704f807b619e110cb7")
EXPECTED_REVIEW_HASHES="e2244580557069c212f005b460680377e1d1e99861677007acffbd681a41c0bd";EXPECTED_WALL="6a336116709c2f3c1d92453fe1b3a2821e03d31128dae72d0fc700627fa94cd7"
ROLES={"directional-arrow":"rounded-outline-v1","any-note":"outlined-circle-v1","guard":"outlined-shield-v1","bomb":"urchin-v1","wall":"red-glass-v1","track":"blue-glass-v1","athlete-marker":"sphere-v1"}
def fail(message):raise SystemExit(message)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def tree(base):
 files=sorted(path for path in base.rglob("*") if path.is_file());rows="".join(f"{path.relative_to(base).as_posix()}\0{path.stat().st_size}\0{sha(path)}\n" for path in files);return len(files),sum(path.stat().st_size for path in files),hashlib.sha256(rows.encode()).hexdigest()
def chmod_tree(base):
 for path in base.rglob("*"):os.chmod(path,0o555 if path.is_dir() else 0o444)
 os.chmod(base,0o555)
def remove_stage(stage):
 for path in sorted((p for p in stage.rglob("*") if p.is_dir()),reverse=True):os.chmod(path,0o700)
 os.chmod(stage,0o700);shutil.rmtree(stage)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--release",required=True,choices=[RELEASE]);a=ap.parse_args();root=Path(a.root).resolve();raw=root/"release/raw"/RELEASE;review=root/"review"/RELEASE;stage=root/f".canonical-{RELEASE}-staging"
 actual_tree=subprocess.check_output(["git","rev-parse",f"{APPROVED_COMMIT}^{{tree}}"],cwd=root,text=True).strip()
 if actual_tree!=APPROVED_TREE:fail("approved source tree mismatch")
 inputs=subprocess.run(["git","diff","--exit-code",APPROVED_COMMIT,"--","tools/generate.py","source","manifests","sets","LICENSE.md"],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 if inputs.returncode:fail("generation inputs differ from audited authority\n"+inputs.stdout)
 if raw.exists() or review.exists():fail(f"canonical successor already exists: raw={raw.exists()} review={review.exists()}; never regenerate")
 if stage.exists():fail(f"canonical staging state exists at {stage}; inspect/recover, never regenerate")
 blender=shutil.which("blender")
 if not blender:fail("Blender missing")
 (stage/"release/raw").mkdir(parents=True);(stage/"review").mkdir();shutil.copytree(root/"release/raw"/PREDECESSOR,stage/"release/raw"/PREDECESSOR)
 for name in ("source","manifests","sets"):shutil.copytree(root/name,stage/name)
 shutil.copy2(root/"LICENSE.md",stage/"LICENSE.md")
 marker="GENERATE_OK release=0.0.10 assets=7 sources=10 manifests=10 release_files=17 review_pngs=83 review_metadata=5"
 output=run_checked([blender,"--background","--factory-startup","--python",str(root/"tools/generate.py"),"--","--output-root",str(stage),"--release",RELEASE,"--source-commit",APPROVED_COMMIT,"--source-tree",APPROVED_TREE],operation="single canonical uniform-wall generation",marker=marker,postcondition=lambda:(stage/"release/raw"/RELEASE).is_dir() and (stage/"review"/RELEASE).is_dir());print(output,end="")
 staged_raw=stage/"release/raw"/RELEASE;staged_review=stage/"review"/RELEASE
 actual={"inventory":sha(staged_raw/"inventory.v1.json"),"proof":sha(staged_raw/"proof.v1.json"),"raw":tree(staged_raw),"review":tree(staged_review),"reviewHashes":sha(staged_review/"hashes.v1.json"),"wall":sha(staged_raw/"wall/red-glass-v1.glb")};expected={"inventory":EXPECTED_INVENTORY,"proof":EXPECTED_PROOF,"raw":EXPECTED_RAW,"review":EXPECTED_REVIEW,"reviewHashes":EXPECTED_REVIEW_HASHES,"wall":EXPECTED_WALL}
 if actual!=expected:fail(f"canonical candidate differs from audited anchors; preserve {stage}: {actual}")
 subprocess.run([sys.executable,str(root/"tools/validate_uniform_wall_candidate.py"),"--authority-root",str(root),"--candidate-root",str(stage),"--source-commit",APPROVED_COMMIT,"--source-tree",APPROVED_TREE],check=True)
 for role,variant in ROLES.items():
  canonical=f"{role}/{variant}";path=staged_raw/role/f"{variant}.glb";run_checked([blender,"--background","--factory-startup","--python",str(root/"tools/smoke_import.py"),"--",str(path),canonical],operation=f"canonical candidate smoke {canonical}",marker=f"SMOKE_OK kind=glb identity={canonical}",postcondition=lambda p=path:p.is_file())
 state={"schema":"aerobeat.canonical-generation-state/v1","release":RELEASE,"source_commit":APPROVED_COMMIT,"source_tree":APPROVED_TREE,"inventory_sha256":EXPECTED_INVENTORY,"proof_sha256":EXPECTED_PROOF,"generation_count":1};(stage/"generation-complete.json").write_text(json.dumps(state,sort_keys=True,separators=(",",":"))+"\n")
 try:staged_raw.rename(raw);staged_review.rename(review)
 except Exception as error:fail(f"promotion incomplete; recover {stage}, never regenerate: {error}")
 chmod_tree(raw);chmod_tree(review);remove_stage(stage)
 print(f"CANONICAL_BUILD_OK release={RELEASE} generation_count=1 inventory_sha256={EXPECTED_INVENTORY} proof_sha256={EXPECTED_PROOF}")
if __name__=="__main__":main()
