#!/usr/bin/env python3
"""Fail-closed structural validator for isolated uniform-wall 0.0.10 candidates."""
from __future__ import annotations
import argparse,hashlib,json,struct
from collections import Counter
from pathlib import Path

RELEASE="0.0.10"; PREDECESSOR="0.0.9"
ROLES={"directional-arrow":"rounded-outline-v1","any-note":"outlined-circle-v1","guard":"outlined-shield-v1","bomb":"urchin-v1","wall":"red-glass-v1","track":"blue-glass-v1","athlete-marker":"sphere-v1"}
UNCHANGED=tuple(role for role in ROLES if role!="wall")
WALL_CONTRACT={"adjacent_gap":[.06,.06],"alpha_mode":"BLEND","blend":"alpha","body_opacity":.24,"cell_pitch":[1.,1.],"cull":"back","depth_test":True,"depth_write":False,"double_sided":False,"edge_cage":False,"order":"after-track","uniform_surface":True,"unit_cell_footprint":[.94,.94],"xy_scale_authoritative":[1,1],"z_scale_authoritative":True}

def fail(message): raise AssertionError(message)
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def parse_glb(path):
 data=path.read_bytes(); magic,version,total=struct.unpack_from("<4sII",data,0)
 if (magic,version,total)!=(b"glTF",2,len(data)): fail("wall GLB header")
 size,kind=struct.unpack_from("<I4s",data,12)
 if kind!=b"JSON": fail("wall GLB JSON chunk")
 doc=json.loads(data[20:20+size].decode().rstrip(" \0")); offset=20+size
 binary_size,binary_kind=struct.unpack_from("<I4s",data,offset)
 if binary_kind!=b"BIN\0" or doc.get("images") or doc.get("textures") or any("uri" in value for value in doc.get("buffers",[])): fail("wall GLB must be self-contained")
 return doc,data[offset+8:offset+8+binary_size]
def accessor(doc,binary,index):
 value=doc["accessors"][index]; view=doc["bufferViews"][value["bufferView"]]; start=view.get("byteOffset",0)+value.get("byteOffset",0)
 if value["componentType"]==5126 and value["type"]=="VEC3": return [struct.unpack_from("<fff",binary,start+i*12) for i in range(value["count"])]
 fmt,width={5123:("<H",2),5125:("<I",4)}[value["componentType"]]; return [struct.unpack_from(fmt,binary,start+i*width)[0] for i in range(value["count"])]
def validate_wall(path):
 doc,binary=parse_glb(path)
 if len(doc.get("meshes",[]))!=1 or len(doc["meshes"][0].get("primitives",[]))!=1: fail("wall must have one material primitive")
 primitive=doc["meshes"][0]["primitives"][0]
 if primitive.get("material")!=0 or set(primitive.get("attributes",{}))!={"POSITION","NORMAL"}: fail("wall primitive contract")
 positions=accessor(doc,binary,primitive["attributes"]["POSITION"]); normals=accessor(doc,binary,primitive["attributes"]["NORMAL"]); indices=accessor(doc,binary,primitive["indices"])
 if len(positions)!=36 or len(normals)!=36 or len(indices)!=36 or any(abs(sum(value*value for value in normal)-1)>1e-5 for normal in normals): fail("wall must be one explicit-normal 12-triangle box")
 expected={(x,y,z) for x in (-.47,.47) for y in (-.47,.47) for z in (-.5,.5)};points=[tuple(round(value,6) for value in position) for position in positions]
 if set(points)!=expected: fail("wall exact source bounds")
 welded={point:index for index,point in enumerate(sorted(set(points)))};welded_indices=[welded[points[index]] for index in indices]
 edges=Counter(tuple(sorted((welded_indices[i+j],welded_indices[i+(j+1)%3]))) for i in range(0,len(welded_indices),3) for j in range(3))
 if any(count!=2 for count in edges.values()): fail("wall body must be a closed two-manifold")
 material=doc.get("materials",[])
 if len(material)!=1 or material[0].get("name")!="mat/red_glass": fail("wall must omit edge material")
 value=material[0]
 if value.get("alphaMode")!="BLEND" or value.get("doubleSided") is not False or value.get("pbrMetallicRoughness",{}).get("baseColorFactor")!=[.65,.01,.018,.24]: fail("wall body alpha contract")
 expected_extra={"blend":"alpha","cull":"back","depthTest":True,"depthWrite":False,"order":"after-track","unitCellFootprint":[.94,.94],"xyScaleAuthoritative":[1,1],"zScaleAuthoritative":True}
 if value.get("extras",{}).get("aerobeat")!=expected_extra: fail("wall material runtime semantics")
 return {"weldedVertices":len(set(points)),"explicitCorners":len(positions),"triangles":len(indices)//3,"materials":len(material),"sha256":sha(path),"bytes":path.stat().st_size}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--authority-root",required=True);ap.add_argument("--candidate-root",required=True);ap.add_argument("--source-commit");ap.add_argument("--source-tree");ap.add_argument("--canonical",action="store_true");a=ap.parse_args()
 authority=Path(a.authority_root).resolve();candidate=Path(a.candidate_root).resolve();raw=candidate/"release/raw"/RELEASE;review=candidate/"review"/RELEASE
 if not raw.is_dir() or not review.is_dir(): fail("release and review trees are required")
 if a.canonical:
  if candidate!=authority: fail("canonical validation requires candidate root equal authority root")
 elif raw.resolve().is_relative_to((authority/"release/raw").resolve()): fail("candidate must be isolated")
 inventory=load(raw/"inventory.v1.json");proof=load(raw/"proof.v1.json")
 files=[path for path in raw.rglob("*") if path.is_file()]
 if len(files)!=17 or inventory.get("release")!=RELEASE or inventory.get("expected_asset_count")!=7: fail("exact candidate raw inventory")
 if sha(raw/"inventory.v1.json")!=proof.get("inventory_sha256"): fail("proof inventory binding")
 if proof.get("claims",{}).get("changed_identities")!=["wall/red-glass-v1"] or proof["claims"].get("byte_identical_predecessor_roles")!=["directional-arrow","any-note","guard","bomb","track","athlete-marker"]: fail("proof wall-only scope")
 if a.source_commit and proof.get("source_authority",{}).get("commit")!=a.source_commit: fail("proof source commit")
 if a.source_tree and proof.get("source_authority",{}).get("tree")!=a.source_tree: fail("proof source tree")
 for role in UNCHANGED:
  variant=ROLES[role]
  for relative in (Path(role)/f"{variant}.glb",Path("manifests")/role/f"{variant}.v1.json"):
   if (raw/relative).read_bytes()!=(authority/"release/raw"/PREDECESSOR/relative).read_bytes(): fail(f"unchanged predecessor drift: {relative}")
 wall=validate_wall(raw/"wall/red-glass-v1.glb");manifest=load(raw/"manifests/wall/red-glass-v1.v1.json");source_manifest=load(candidate/"manifests/wall/red-glass-v1.v1.json")
 for document in (manifest,source_manifest):
  if document.get("release")!=RELEASE or document.get("identity",{}).get("canonical_name")!="wall/red-glass-v1" or document.get("geometry",{}).get("triangle_count")!=12 or document["geometry"].get("triangle_budget")!=12 or document.get("materials",{}).get("names")!=["mat/red_glass"] or document["materials"].get("contract")!=WALL_CONTRACT: fail("wall manifest contract")
 if source_manifest.get("files",{}).get("source_sha256")!=sha(candidate/"source/wall/red-glass-v1/red-glass-v1.blend"): fail("wall source hash")
 if source_manifest["files"].get("release_sha256")!=wall["sha256"] or source_manifest["files"].get("release_bytes")!=wall["bytes"]: fail("wall release hash")
 setdoc=load(raw/"sets/default-v1.json")
 if setdoc.get("release")!=RELEASE or setdoc.get("roles")!=ROLES or (candidate/"sets/default-v1.json").read_bytes()!=(raw/"sets/default-v1.json").read_bytes(): fail("candidate set contract")
 pngs={path.name for path in review.glob("*.png")};jsons={path.name for path in review.glob("*.json")}
 if len(pngs)!=83 or jsons!={"hashes.v1.json","layout.v1.json","visibility.v1.json","contrast.v1.json","wall-grid.v1.json"}: fail("exact review inventory")
 wall_faces={f"wall--red-glass-v1--{face}-{background}.png" for face in ("plus-z","minus-z","plus-x","three-quarter-plus-z","three-quarter-minus-z") for background in ("dark","bright","blue")}
 if not wall_faces<=pngs: fail("wall multi-angle review matrix")
 layout=load(review/"layout.v1.json").get("images",{})
 if any(layout.get(name,{}).get("kind")!="wall-face-uniformity" for name in wall_faces): fail("wall review layout semantics")
 wall_grid=load(review/"wall-grid.v1.json")
 if wall_grid.get("materials")!={"analytic_only":True,"body":"mat/red_glass","edge_cage":False,"uniform_surface":True,"depth_test":True,"depth_write":False,"order":"after-track"}: fail("wall-grid uniformity evidence")
 hashes=load(review/"hashes.v1.json")
 if {entry["path"] for entry in hashes.get("files",[])}!=pngs or any(entry["sha256"]!=sha(review/entry["path"]) for entry in hashes["files"]): fail("review hash binding")
 print(json.dumps({"oracle":"uniform-wall-candidate","release":RELEASE,"wall":wall,"unchangedRoles":list(UNCHANGED),"reviewPngs":len(pngs),"edgeCage":False,"pass":True},sort_keys=True))
if __name__=="__main__":main()
