#!/usr/bin/env python3
"""Adversarial checks for the uniform wall's one-surface contract."""
from __future__ import annotations
import argparse,copy,json,struct,tempfile
from pathlib import Path
from validate_uniform_wall_candidate import parse_glb,validate_wall

def fail(message): raise AssertionError(message)
def write_glb(path,doc,binary):
 payload=json.dumps(doc,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 while len(payload)%4: payload+=b" "
 data=bytearray(binary)
 while len(data)%4:data.append(0)
 path.write_bytes(struct.pack("<4sII",b"glTF",2,12+8+len(payload)+8+len(data))+struct.pack("<I4s",len(payload),b"JSON")+payload+struct.pack("<I4s",len(data),b"BIN\0")+data)
def rejected(base_doc,binary,mutate,label):
 with tempfile.TemporaryDirectory(prefix="aerobeat-wall-adversarial-") as directory:
  path=Path(directory)/"wall.glb";doc=copy.deepcopy(base_doc);mutate(doc);write_glb(path,doc,binary)
  try:validate_wall(path)
  except AssertionError:return
  fail(f"adversarial wall accepted: {label}")
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--authority-root",required=True);ap.add_argument("--candidate-root",required=True);a=ap.parse_args();authority=Path(a.authority_root);candidate=Path(a.candidate_root)
 wall=candidate/"release/raw/0.0.10/wall/red-glass-v1.glb";doc,binary=parse_glb(wall);validate_wall(wall)
 rejected(doc,binary,lambda value:value["meshes"][0]["primitives"].append(copy.deepcopy(value["meshes"][0]["primitives"][0])),"second primitive")
 rejected(doc,binary,lambda value:value["materials"].append({**copy.deepcopy(value["materials"][0]),"name":"mat/red_edge"}),"edge material")
 rejected(doc,binary,lambda value:value["materials"][0]["pbrMetallicRoughness"]["baseColorFactor"].__setitem__(3,.82),"high-alpha rail material")
 rejected(doc,binary,lambda value:value["materials"][0]["extras"]["aerobeat"].__setitem__("depthWrite",True),"transparent depth-write")
 try:validate_wall(authority/"release/raw/0.0.9/wall/red-glass-v1.glb")
 except AssertionError:pass
 else:fail("edge-cage predecessor must fail uniform-wall contract")
 print("Uniform wall adversarial PASS: second primitive/material, 0.82 alpha, depth-write, and 0.0.9 edge cage rejected.")
if __name__=="__main__":main()
