#!/usr/bin/env python3
"""Adversarial fail-closed mutations for rounded cue geometry/material contracts."""
from __future__ import annotations
import argparse, json, struct, tempfile
from pathlib import Path
from validate_rounded_candidate import (EXPECTED, assert_area_ratio, assert_naive_radii_positive,
 assert_non_narrowing_band, assert_simple_polygon, assert_single_fill_boundary,
 assert_symmetric, circumradius, parse_glb, validate_cue)

def rebuild(path,doc,binary):
 encoded=json.dumps(doc,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 while len(encoded)%4: encoded+=b" "
 payload=struct.pack("<4sII",b"glTF",2,12+8+len(encoded)+8+len(binary))+struct.pack("<I4s",len(encoded),b"JSON")+encoded+struct.pack("<I4s",len(binary),b"BIN\0")+bytes(binary)
 path.write_bytes(payload)
def must_reject(path,role,label):
 try: validate_cue(path,role)
 except (AssertionError,KeyError,ValueError,IndexError): return
 raise AssertionError(f"adversarial mutation accepted: {label}")
def must_fail(operation,label):
 try: operation()
 except AssertionError: return
 raise AssertionError(f"adversarial morphology accepted: {label}")
def require(condition,label):
 if not condition: raise AssertionError(label)
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
  doc,binary=parse_glb(source); primitive=doc["meshes"][0]["primitives"][0]; doc["accessors"][primitive["indices"]]["count"]-=3; rebuild(target,doc,binary); must_reject(target,"directional-arrow","triangle count drift")
 outer=[(0,0),(1,0),(1,1),(0,1)]; narrowed=[(.005,.005),(.995,.005),(.995,.995),(.005,.995)]; widened=[(.1,.1),(.9,.1),(.9,.9),(.1,.9)]; readable=[(.25,.05),(.75,.05),(.75,.95),(.25,.95)]
 must_fail(lambda:assert_naive_radii_positive([.05,.055,.06],.086),"naive negative radius")
 must_fail(lambda:assert_simple_polygon([(0,0),(1,1),(0,1),(1,0)],"synthetic"),"self intersection")
 must_fail(lambda:assert_non_narrowing_band(outer,narrowed,.014,"synthetic straight/join"),"narrow straight run/join")
 assert_non_narrowing_band(outer,widened,.014,"synthetic widened join")
 must_fail(lambda:assert_single_fill_boundary([outer,widened],"synthetic"),"disconnected fill")
 must_fail(lambda:require(circumradius((-.02,0),(0,.02),(.02,0))>=.045,"tip radius"),"small fill tip")
 must_fail(lambda:assert_area_ratio([(.45,.45),(.55,.45),(.55,.55),(.45,.55)],outer,.35,"synthetic fill"),"fill area")
 assert_area_ratio(readable,outer,.35,"synthetic colored fill")
 must_fail(lambda:assert_area_ratio(readable,outer,.48,"synthetic interior readability"),"interior readability area")
 must_fail(lambda:assert_symmetric([(0,0),(1,0),(0,1)],"synthetic"),"symmetry")
 print("ROUNDED_ADVERSARIAL_OK mutations=14")
if __name__=="__main__": main()
