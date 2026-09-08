#!/usr/bin/env python3
"""One-shot canonical 0.0.9 builder preserving the approved source authority."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess
from pathlib import Path

from subprocess_contract import run_checked
from validate_rounded_candidate import (
    APPROVED_COMMIT, APPROVED_TREE, EXPECTED_INVENTORY_SHA256,
    EXPECTED_PROOF_SHA256, RELEASE, sha, smoke_changed, validate,
)

GENERATION_MARKER=f"GENERATE_OK release={RELEASE} assets=7 sources=10 manifests=10 release_files=17 review_pngs=68 review_metadata=5"


def fail(message):
    raise SystemExit(message)


def generation_inputs_are_authorized(root):
    tree=subprocess.check_output(["git","rev-parse",f"{APPROVED_COMMIT}^{{tree}}"],cwd=root,text=True).strip()
    if tree!=APPROVED_TREE: fail(f"approved authority tree mismatch: {tree}")
    changed=subprocess.run(["git","diff","--exit-code",APPROVED_COMMIT,"--","tools/generate.py","source","manifests","sets","LICENSE.md"],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if changed.returncode: fail("authorized generation inputs differ from approved authority\n"+changed.stdout)


def prepare(root,stage):
    (stage/"release/raw").mkdir(parents=True)
    (stage/"review").mkdir()
    shutil.copytree(root/"release/raw/0.0.8",stage/"release/raw/0.0.8")
    for name in ("source","manifests","sets"): shutil.copytree(root/name,stage/name)
    shutil.copyfile(root/"LICENSE.md",stage/"LICENSE.md")


def remove_stage(stage):
    for path in sorted((p for p in stage.rglob("*") if p.is_dir()),reverse=True): os.chmod(path,0o700)
    os.chmod(stage,0o700)
    shutil.rmtree(stage)


def argument_parser():
    parser=argparse.ArgumentParser(); parser.add_argument("--root",default="."); parser.add_argument("--release",required=True,choices=[RELEASE]); return parser


def reject_existing_targets(raw,review,stage):
    if raw.exists() or review.exists(): fail(f"canonical successor already exists: raw={raw.exists()} review={review.exists()}; never regenerate")
    if stage.exists(): fail(f"canonical staging state already exists at {stage}; inspect/recover it without regenerating")


def main():
    args=argument_parser().parse_args()
    root=Path(args.root).resolve(); raw=root/"release/raw"/RELEASE; review=root/"review"/RELEASE; stage=root/f".canonical-{RELEASE}-staging"
    generation_inputs_are_authorized(root)
    reject_existing_targets(raw,review,stage)
    blender=shutil.which("blender")
    if not blender: fail("Blender missing")
    prepare(root,stage)
    output=run_checked([blender,"--background","--factory-startup","--python",str(root/"tools/generate.py"),"--","--output-root",str(stage),"--release",RELEASE,"--source-commit",APPROVED_COMMIT,"--source-tree",APPROVED_TREE],operation="single canonical rounded generation",marker=GENERATION_MARKER,postcondition=lambda:(stage/"release/raw"/RELEASE).is_dir() and (stage/"review"/RELEASE).is_dir())
    print(output,end="")
    marker={"schema":"aerobeat.canonical-generation-state/v1","release":RELEASE,"source_commit":APPROVED_COMMIT,"source_tree":APPROVED_TREE,"inventory_sha256":sha(stage/"release/raw"/RELEASE/"inventory.v1.json"),"proof_sha256":sha(stage/"release/raw"/RELEASE/"proof.v1.json"),"generation_count":1}
    (stage/"generation-complete.json").write_text(json.dumps(marker,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    if marker["inventory_sha256"]!=EXPECTED_INVENTORY_SHA256 or marker["proof_sha256"]!=EXPECTED_PROOF_SHA256: fail(f"generated anchors differ from audited authority; preserve {stage} for recovery")
    validate(root,stage,False)
    smoke_changed(root,stage/"release/raw"/RELEASE)
    try:
        (stage/"release/raw"/RELEASE).rename(raw)
        (stage/"review"/RELEASE).rename(review)
    except Exception as error:
        fail(f"promotion incomplete; do not regenerate; recover from {stage}: {error}")
    remove_stage(stage)
    print(f"CANONICAL_BUILD_OK release={RELEASE} generation_count=1 inventory_sha256={EXPECTED_INVENTORY_SHA256} proof_sha256={EXPECTED_PROOF_SHA256}")

if __name__=="__main__": main()
