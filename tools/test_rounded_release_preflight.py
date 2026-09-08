#!/usr/bin/env python3
"""Fail-closed pre-generation and pre-promotion adversaries for 0.0.9."""
from __future__ import annotations
import argparse, contextlib, io, json, shutil, subprocess, tempfile
from pathlib import Path

from build_rounded_release import argument_parser, generation_inputs_are_authorized, prepare, reject_existing_targets
from validate_rounded_candidate import APPROVED_COMMIT, APPROVED_TREE, RELEASE, validate_release_inventory


def must_reject(operation,label):
    try:
        operation()
    except (AssertionError,SystemExit,subprocess.CalledProcessError):
        return
    raise AssertionError(f"preflight adversary accepted: {label}")


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--root",default="."); parser.add_argument("--candidate-root",required=True); args=parser.parse_args()
    root=Path(args.root).resolve(); candidate=Path(args.candidate_root).resolve()
    assert RELEASE=="0.0.9"
    with contextlib.redirect_stderr(io.StringIO()):
        must_reject(lambda:argument_parser().parse_args(["--release","0.0.8"]),"wrong release 0.0.8")
        must_reject(lambda:argument_parser().parse_args(["--release","0.0.10"]),"wrong release 0.0.10")
    with tempfile.TemporaryDirectory(prefix="aerobeat-preflight-targets-") as directory:
        base=Path(directory); raw=base/"raw"; review=base/"review"; stage=base/"stage"
        for target,label in ((raw,"raw target"),(review,"review target"),(stage,"staging target")):
            target.mkdir(); must_reject(lambda raw=raw,review=review,stage=stage:reject_existing_targets(raw,review,stage),label); shutil.rmtree(target)
    with tempfile.TemporaryDirectory(prefix="aerobeat-preflight-prepare-") as directory:
        stage=Path(directory)/"stage"; prepare(root,stage)
        assert (stage/"release/raw/0.0.8").is_dir() and not (stage/"release/raw/0.0.7").exists()
    with tempfile.TemporaryDirectory(prefix="aerobeat-preflight-git-") as directory:
        checkout=Path(directory)/"authority"
        subprocess.run(["git","clone","-q","--shared",str(root),str(checkout)],check=True)
        subprocess.run(["git","checkout","-q",APPROVED_COMMIT],cwd=checkout,check=True)
        assert subprocess.check_output(["git","rev-parse","HEAD^{tree}"],cwd=checkout,text=True).strip()==APPROVED_TREE
        generation_inputs_are_authorized(checkout)
        with (checkout/"tools/generate.py").open("a",encoding="utf-8") as handle: handle.write("\n# dirty adversary\n")
        must_reject(lambda:generation_inputs_are_authorized(checkout),"dirty generation inputs")
    with tempfile.TemporaryDirectory(prefix="aerobeat-preflight-anchor-") as directory:
        release=Path(directory)/"0.0.9"; shutil.copytree(candidate/"release/raw"/RELEASE,release)
        proof=release/"proof.v1.json"; document=json.loads(proof.read_text(encoding="utf-8")); document["source_authority"]["tree"]="0"*40; proof.write_text(json.dumps(document,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
        must_reject(lambda:validate_release_inventory(release),"altered proof/source anchor")
    print("ROUNDED_PREFLIGHT_OK release=0.0.9 wrong_versions=2 existing_targets=3 dirty_inputs=1 predecessor=0.0.8 altered_anchors=1 blender_invocations=0 promotions=0")

if __name__=="__main__": main()
