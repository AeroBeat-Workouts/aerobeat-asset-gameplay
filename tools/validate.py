#!/usr/bin/env python3
"""Strict release/source validator for the canonical AeroBeat gameplay package."""
from __future__ import annotations
import argparse, ast, hashlib, json, os, shutil, struct, subprocess, sys, tempfile
from pathlib import Path

SUPPORTED_RELEASE="0.0.2"
EXPECTED={
"directional-arrow":("outline-v1",[.78,.78,.18],[0,0,0],420),
"any-note":("circle-v1",[.70,.70,.18],[0,0,0],320),
"guard":("shield-v1",[.72,.82,.16],[0,0,.07],520),
"bomb":("urchin-v1",[.78,.78,.78],[0,0,0],900),
"wall":("red-glass-v1",[1.8,1.9,1.0],[0,0,0],144),
"track":("blue-glass-v1",[4.2,.06,24.0],[0,.03,0],160),
"athlete-marker":("sphere-v1",[.18,.18,.18],[0,0,0],192),
}
TOP_KEYS={"schema","release","identity","files","names","source_authority","geometry","coordinates","materials","reuse","rights","provenance","dependencies"}
GEO_KEYS={"dimensions","measured_aabb","pivot","object_origin","rotation_euler","scale","triangle_count","triangle_budget","collision_free_bound"}

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def eq(a,b,e=1e-5): return len(a)==len(b) and all(abs(x-y)<=e for x,y in zip(a,b))
def fail(msg): raise AssertionError(msg)
def exact_keys(d,k,where):
 if set(d)!=set(k): fail(f"{where}: keys {sorted(d)} != {sorted(k)}")

def parse_glb(path):
 data=path.read_bytes()
 if len(data)<20: fail(f"{path}: truncated GLB")
 magic,ver,total=struct.unpack_from("<4sII",data,0)
 if magic!=b"glTF" or ver!=2 or total!=len(data): fail(f"{path}: invalid GLB header")
 off=12; chunks=[]
 while off<len(data):
  if off+8>len(data): fail(f"{path}: truncated chunk")
  n,t=struct.unpack_from("<I4s",data,off); off+=8
  if off+n>len(data): fail(f"{path}: chunk overflow")
  chunks.append((t,data[off:off+n])); off+=n
 if off!=len(data) or not chunks or chunks[0][0]!=b"JSON": fail(f"{path}: invalid chunk layout")
 doc=json.loads(chunks[0][1].decode("utf-8").rstrip(" \x00"))
 bins=[b for t,b in chunks if t==b"BIN\x00"]
 if len(bins)!=1: fail(f"{path}: expected one BIN chunk")
 if doc.get("asset",{}).get("version")!="2.0": fail(f"{path}: not glTF 2.0")
 for b in doc.get("buffers",[]):
  if "uri" in b: fail(f"{path}: external buffer dependency")
 if doc.get("images") or doc.get("textures"): fail(f"{path}: textures/images forbidden")
 if any("uri" in i for i in doc.get("images",[])): fail(f"{path}: external image dependency")
 forbidden={"KHR_draco_mesh_compression","EXT_meshopt_compression"}
 if forbidden.intersection(doc.get("extensionsUsed",[])): fail(f"{path}: unsupported compressed dependency")
 return doc,bins[0]

def glb_facts(path,canonical):
 d,_=parse_glb(path); nodes=d.get("nodes",[]); names=[n.get("name") for n in nodes]
 if names.count(canonical)!=1: fail(f"{path}: expected one canonical node {canonical}, got {names}")
 if len(d.get("meshes",[]))!=1: fail(f"{path}: expected exactly one mesh")
 tris=0; lo=[float("inf")]*3; hi=[float("-inf")]*3
 for prim in d["meshes"][0].get("primitives",[]):
  if prim.get("mode",4)!=4: fail(f"{path}: non-triangle primitive")
  if "indices" not in prim or "POSITION" not in prim.get("attributes",{}): fail(f"{path}: incomplete primitive")
  ia=d["accessors"][prim["indices"]]; pa=d["accessors"][prim["attributes"]["POSITION"]]
  if ia["count"]%3: fail(f"{path}: index count not divisible by 3")
  tris+=ia["count"]//3
  if "min" not in pa or "max" not in pa: fail(f"{path}: POSITION lacks bounds")
  for i in range(3): lo[i]=min(lo[i],pa["min"][i]); hi[i]=max(hi[i],pa["max"][i])
 for n in nodes:
  if any(k in n for k in ("translation","rotation","scale","matrix")):
   fail(f"{path}: transformed node violates identity transform contract: {n.get('name')}")
 return tris,[lo,hi],d

def validate(root,release,smoke=True):
 rel=root/"release"/"raw"/release
 if release!=SUPPORTED_RELEASE: fail(f"unsupported release {release}; successor tooling requires explicit {SUPPORTED_RELEASE}")
 expected_paths={"inventory.v1.json","proof.v1.json","sets/default-v1.json"}
 manifests=[]
 for role,(variant,dims,pivot,budget) in EXPECTED.items():
  expected_paths|={f"{role}/{variant}.glb",f"manifests/{role}/{variant}.v1.json"}
  mp=root/"manifests"/role/(variant+".v1.json"); rp=rel/"manifests"/role/(variant+".v1.json"); glb=rel/role/(variant+".glb"); blend=root/"source"/role/variant/(variant+".blend")
  for p in (mp,rp,glb,blend):
   if not p.is_file(): fail(f"missing {p}")
  if {p.name for p in blend.parent.iterdir() if p.is_file()}!={variant+".blend"}: fail(f"{role}: source inventory")
  m=load(mp); rm=load(rp); exact_keys(m,TOP_KEYS,str(mp)); exact_keys(rm,TOP_KEYS,str(rp)); exact_keys(m["geometry"],GEO_KEYS,str(mp)+" geometry")
  if rm["files"].get("source_sha256") is not None or rm["source_authority"].get("blend_byte_determinism_claimed") is not False: fail(f"{role}: release manifest overclaims blend determinism")
  if m["schema"]!="aerobeat.gameplay-asset/v1" or m["release"]!=release: fail(f"{mp}: schema/release")
  identity=m["identity"]; canonical=f"{role}/{variant}"
  if identity!={"role":role,"variant":variant,"canonical_name":canonical}: fail(f"{mp}: identity")
  if m["geometry"]["dimensions"]!=dims or m["geometry"]["pivot"]!=pivot or m["geometry"]["triangle_budget"]!=budget: fail(f"{mp}: spec geometry declaration")
  if m["geometry"]["object_origin"]!=[0,0,0] or m["geometry"]["rotation_euler"]!=[0,0,0] or m["geometry"]["scale"]!=[1,1,1]: fail(f"{mp}: transforms")
  if m["coordinates"]!={"handedness":"right","up":"+Y","forward":"-Z","visible_face":"-Z" if role in ("directional-arrow","any-note","guard") else "not-applicable"}: fail(f"{mp}: coordinate contract")
  if m["materials"]["analytic_only"] is not True or m["materials"]["textures"]!=[]: fail(f"{mp}: non-analytic material")
  if m["rights"]!={"license":"CC-BY-NC-4.0","creator":"AeroBeat / Gambit Games","third_party_content":False}: fail(f"{mp}: rights")
  if m["dependencies"]!=[] or m["provenance"]["external_assets"]!=[] or m["provenance"]["network"] is not False or m["provenance"]["blender"]!="4.0.2": fail(f"{mp}: provenance/dependencies")
  expected_files={"source":f"source/{role}/{variant}/{variant}.blend","release":f"release/raw/{release}/{role}/{variant}.glb","source_sha256":sha(blend),"source_bytes":blend.stat().st_size,"release_sha256":sha(glb),"release_bytes":glb.stat().st_size}
  if m["files"]!=expected_files or rm["files"]!={k:v for k,v in expected_files.items() if k not in ("source_sha256","source_bytes")}: fail(f"{mp}: file paths/hashes/bytes")
  tris,aabb,d=glb_facts(glb,canonical)
  expected_names={"node":canonical,"mesh":canonical+"/mesh","materials":[x.get("name") for x in d.get("materials",[])]}
  if m["names"]!=expected_names or rm["names"]!=expected_names or m["materials"]["names"]!=expected_names["materials"]: fail(f"{role}: mesh/node/material names")
  if tris!=m["geometry"]["triangle_count"] or tris>budget: fail(f"{role}: triangles {tris}/{budget}")
  flat=lambda x:[z for row in x for z in row]
  if not eq(flat(aabb),flat(m["geometry"]["measured_aabb"])): fail(f"{role}: GLB/manifest AABB")
  b=m["geometry"]["collision_free_bound"]; pivot=m["geometry"]["pivot"]
  # Spec bounds are relative to the stated geometry/pivot reference.
  shifted=[[b[j][i]-pivot[i] for i in range(3)] for j in range(2)]
  if any(aabb[0][i]<shifted[0][i]-1e-5 or aabb[1][i]>shifted[1][i]+1e-5 for i in range(3)): fail(f"{role}: bound exceeded {aabb} vs {shifted}")
  measured=[aabb[1][i]-aabb[0][i] for i in range(3)]
  if not eq(measured,dims,2e-4): fail(f"{role}: exact dimensions {measured} != {dims}")
  manifests.append((role,variant,glb,tris,aabb))
 actual={p.relative_to(rel).as_posix() for p in rel.rglob("*") if p.is_file()}
 if actual!=expected_paths: fail(f"release inventory mismatch missing={sorted(expected_paths-actual)} extra={sorted(actual-expected_paths)}")
 setdoc=load(rel/"sets/default-v1.json")
 if setdoc!=load(root/"sets/default-v1.json"): fail("release set differs")
 if setdoc.get("roles")!={r:v[0] for r,v in EXPECTED.items()}: fail("set mapping is not independently exact")
 if setdoc.get("constraints")!={"guard_instances_per_beat":2,"guard_canonical_asset":"guard/shield-v1"}: fail("canonical shield constraint")
 inv=load(rel/"inventory.v1.json"); listed={x["path"]:x for x in inv["payload"]}; payload=expected_paths-{"inventory.v1.json","proof.v1.json"}
 if set(listed)!=payload: fail("inventory payload paths")
 for p,e in listed.items():
  q=rel/p
  if e!={"path":p,"bytes":q.stat().st_size,"sha256":sha(q)}: fail(f"inventory hash/size {p}")
 proof=load(rel/"proof.v1.json")
 if proof["inventory_sha256"]!=sha(rel/"inventory.v1.json") or proof["claims"].get("combined_glb") is not False or proof["determinism"]["blend_snapshots_in_scope"] is not False: fail("release proof")
 review_dir=root/"review"/release; rh=load(review_dir/"hashes.v1.json"); layout=load(review_dir/"layout.v1.json")
 review_files={p.name for p in review_dir.glob("*.png")}
 expected_reviews={"neutral-board.png","gameplay-context.png"}|{r+"--"+v[0]+".png" for r,v in EXPECTED.items()}
 if review_files!=expected_reviews or {x["path"] for x in rh["files"]}!=review_files or rh["resolution"]!=[1600,900]: fail("review inventory/resolution")
 if rh.get("layout")!={"path":"layout.v1.json","bytes":(review_dir/"layout.v1.json").stat().st_size,"sha256":sha(review_dir/"layout.v1.json")}: fail("review layout hash/size")
 for e in rh["files"]:
  p=review_dir/e["path"]; data=p.read_bytes()
  if e.get("bytes")!=p.stat().st_size or sha(p)!=e["sha256"] or data[:8]!=b"\x89PNG\r\n\x1a\n" or struct.unpack(">IIBB",data[16:26])!=(1600,900,8,2): fail(f"review RGB/hash {e['path']}")
 if layout.get("schema")!="aerobeat.review-layout/v1" or layout.get("release")!=release or layout.get("resolution")!=[1600,900] or set(layout.get("images",{}))!=expected_reviews: fail("review layout schema/images")
 for image,entry in layout["images"].items():
  margin=entry.get("minimum_margin"); objects=entry.get("objects",[])
  if not isinstance(margin,(int,float)) or margin<.03 or not objects: fail(f"{image}: missing containment evidence")
  for obj in objects:
   b=obj.get("projected_bbox",[])
   if len(b)!=4 or b[0]<margin-1e-5 or b[1]<margin-1e-5 or b[2]>1-margin+1e-5 or b[3]>1-margin+1e-5: fail(f"{image}: projected object outside safe frame {obj}")
 neutral=layout["images"]["neutral-board.png"]["objects"]
 if len(neutral)!=7 or {x["role"] for x in neutral}!=set(EXPECTED): fail("neutral board must contain all seven roles once")
 context=layout["images"]["gameplay-context.png"]; counts={r:sum(x["role"]==r for x in context["objects"]) for r in EXPECTED}
 required={"directional-arrow":1,"any-note":1,"guard":2,"bomb":1,"wall":1,"track":1,"athlete-marker":3}
 if context.get("required_counts")!=required or counts!=required: fail(f"gameplay context counts {counts}")
 marker_instances={x["instance"] for x in context["objects"] if x["role"]=="athlete-marker"}
 if marker_instances!={"athlete-marker/nose","athlete-marker/left-wrist","athlete-marker/right-wrist"}: fail("gameplay marker identities")
 # Tool/source policy: no third-party imports, network calls, asset loading, textures, fonts, or engine metadata.
 allowed={"argparse","ast","hashlib","json","math","os","pathlib","shutil","struct","subprocess","sys","tempfile","bpy","bpy_extras","mathutils","__future__"}
 for p in sorted((root/"tools").glob("*.py")):
  tree=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
  imports=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import): imports|={x.name.split('.')[0] for x in n.names}
   elif isinstance(n,ast.ImportFrom) and n.module: imports.add(n.module.split('.')[0])
  if imports-allowed: fail(f"{p}: forbidden dependencies {sorted(imports-allowed)}")
  # The strict import allowlist above excludes every network client module.
 forbidden_suffix={".png.import",".glb.import",".godot",".tscn",".tres",".unity",".meta",".fbx",".obj",".jpg",".jpeg",".webp",".ttf",".otf"}
 for p in root.rglob("*"):
  if p.is_file() and any(p.name.lower().endswith(x) for x in forbidden_suffix): fail(f"forbidden runtime/import/external artifact {p}")
 if smoke:
  blender=shutil.which("blender")
  if not blender: fail("Blender missing for smoke imports")
  sv=subprocess.run([blender,"--version"],capture_output=True,text=True,check=True).stdout.splitlines()[0]
  if sv!="Blender 4.0.2": fail(f"exact Blender required, got {sv}")
  smoke_script=root/"tools"/"smoke_import.py"
  for role,variant,glb,_,_ in manifests:
   cp=subprocess.run([blender,"--background","--factory-startup","--python",str(smoke_script),"--",str(glb),f"{role}/{variant}"],capture_output=True,text=True)
   if cp.returncode: fail(f"clean Blender smoke import failed {glb}:\n{cp.stdout}\n{cp.stderr}")
 return manifests

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--release",required=True,choices=[SUPPORTED_RELEASE]); ap.add_argument("--no-smoke",action="store_true"); ap.add_argument("--finalize",action="store_true")
 a=ap.parse_args(); root=Path(a.root).resolve(); facts=validate(root,a.release,not a.no_smoke)
 if a.finalize:
  rel=root/"release"/"raw"/a.release
  for p in rel.rglob("*"): os.chmod(p,0o444 if p.is_file() else 0o555)
  os.chmod(rel,0o555)
 print("VALID",len(facts),"assets")
 for role,variant,_,tris,aabb in facts: print(f"  {role}/{variant}: {tris} triangles AABB={aabb}")
 print("VALID release inventory, SHA-256, rights, provenance, tools, dependencies, review hashes, and clean Blender imports")

if __name__=="__main__": main()
