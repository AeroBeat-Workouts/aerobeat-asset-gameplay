#!/usr/bin/env python3
"""Adversarial fail-closed mutations for rounded cue geometry/material contracts."""
from __future__ import annotations
import argparse, json, struct, tempfile
from pathlib import Path
from validate_rounded_candidate import EXPECTED, parse_glb, validate_cue

def rebuild(path,doc,binary):
 encoded=json.dumps(doc,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 while len(encoded)%4: encoded+=b" "
 payload=struct.pack("<4sII",b"glTF",2,12+8+len(encoded)+8+len(binary))+struct.pack("<I4s",len(encoded),b"JSON")+encoded+struct.pack("<I4s",len(binary),b"BIN\0")+bytes(binary)
 path.write_bytes(payload)
def must_reject(path,role,label):
 try: validate_cue(path,role)
 except (AssertionError,KeyError,ValueError,IndexError): return
 raise AssertionError(f"adversarial mutation accepted: {label}")
def main():
 parser=argparse.ArgumentParser(); parser.add_argument("--candidate-root",required=True); args=parser.parse_args(); candidate=Path(args.candidate_root)
 source=candidate/"release/raw/0.0.8/directional-arrow/rounded-outline-v1.glb"
 with tempfile.TemporaryDirectory(prefix="aerobeat-rounded-adversarial-") as directory:
  target=Path(directory)/"cue.glb"
  doc,binary=parse_glb(source); binary=bytearray(binary)
  primitive=doc["meshes"][0]["primitives"][0]; accessor=doc["accessors"][primitive["indices"]]; view=doc["bufferViews"][accessor["bufferView"]]; offset=view.get("byteOffset",0)+accessor.get("byteOffset",0)
  a,b=struct.unpack_from("<HH",binary,offset); struct.pack_into("<HH",binary,offset,b,a); rebuild(target,doc,binary); must_reject(target,"directional-arrow","reversed triangle")
  doc,binary=parse_glb(source); doc["materials"][0]["extras"]["aerobeat"]["runtimeTintable"]=True; rebuild(target,doc,binary); must_reject(target,"directional-arrow","structural tintability")
  doc,binary=parse_glb(source); doc["materials"][0]["doubleSided"]=True; rebuild(target,doc,binary); must_reject(target,"directional-arrow","disabled culling")
  doc,binary=parse_glb(source); doc["buffers"][0]["uri"]="external.bin"; rebuild(target,doc,binary); must_reject(target,"directional-arrow","external dependency")
 print("ROUNDED_ADVERSARIAL_OK mutations=4")
if __name__=="__main__": main()
