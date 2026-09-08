#!/usr/bin/env python3
"""Non-generating preflight tests for the one-shot 0.0.10 builder."""
from __future__ import annotations
import argparse,importlib.util,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch

def load_builder(root):
 spec=importlib.util.spec_from_file_location("uniform_wall_builder",root/"tools/build_uniform_wall_release.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def expect_exit(module,root,message,*,diff_code=0):
 result=subprocess.CompletedProcess([],diff_code,"generation drift" if diff_code else "")
 with patch.object(sys,"argv",["builder","--root",str(root),"--release",module.RELEASE]),patch.object(module.subprocess,"check_output",return_value=(module.APPROVED_TREE+"\n")),patch.object(module.subprocess,"run",return_value=result):
  try:module.main()
  except SystemExit as error:
   if message not in str(error):raise AssertionError(f"wrong preflight rejection: {error}") from error
  else:raise AssertionError(f"builder accepted preflight defect: {message}")
def main():
 root=Path(__file__).resolve().parents[1];module=load_builder(root);candidate=Path("/tmp/aerobeat-wall-audit-candidate-cr6wjw_1")
 if not candidate.is_dir():raise SystemExit("retained audited candidate is required for non-generating preflight")
 actual=(module.sha(candidate/"release/raw/0.0.10/inventory.v1.json"),module.sha(candidate/"release/raw/0.0.10/proof.v1.json"),module.tree(candidate/"release/raw/0.0.10"),module.tree(candidate/"review/0.0.10"),module.sha(candidate/"review/0.0.10/hashes.v1.json"),module.sha(candidate/"release/raw/0.0.10/wall/red-glass-v1.glb"));expected=(module.EXPECTED_INVENTORY,module.EXPECTED_PROOF,module.EXPECTED_RAW,module.EXPECTED_REVIEW,module.EXPECTED_REVIEW_HASHES,module.EXPECTED_WALL)
 if actual!=expected:raise AssertionError("builder anchors differ from audited candidate")
 tree=subprocess.check_output(["git","rev-parse",f"{module.APPROVED_COMMIT}^{{tree}}"],cwd=root,text=True).strip()
 if tree!=module.APPROVED_TREE:raise AssertionError("approved source authority mismatch")
 changed=subprocess.run(["git","diff","--exit-code",module.APPROVED_COMMIT,"--","tools/generate.py","source","manifests","sets","LICENSE.md"],cwd=root)
 if changed.returncode:raise AssertionError("generation inputs drifted after source audit")
 with tempfile.TemporaryDirectory(prefix="aerobeat-wall-builder-preflight-") as directory:
  base=Path(directory);(base/"release/raw/0.0.10").mkdir(parents=True);expect_exit(module,base,"canonical successor already exists")
 with tempfile.TemporaryDirectory(prefix="aerobeat-wall-builder-preflight-") as directory:
  base=Path(directory);(base/".canonical-0.0.10-staging").mkdir();expect_exit(module,base,"canonical staging state exists")
 with tempfile.TemporaryDirectory(prefix="aerobeat-wall-builder-preflight-") as directory:expect_exit(module,Path(directory),"generation inputs differ",diff_code=1)
 print("Uniform wall release preflight PASS: authority/anchors pinned; existing raw, staging, and generation drift rejected without Blender.")
if __name__=="__main__":main()
