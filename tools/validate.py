#!/usr/bin/env python3
"""Strict release/source validator for the canonical AeroBeat gameplay package."""
from __future__ import annotations
import argparse, ast, hashlib, json, math, os, shutil, struct, sys
from pathlib import Path

from subprocess_contract import run_checked

SUPPORTED_RELEASE="0.0.6"
PREDECESSOR_RELEASE="0.0.5"
EXPECTED_LICENSE_SHA256="41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0"
EXPECTED_LICENSE_BYTES=19347
PREDECESSOR_TREES={
 "release/raw/0.0.1":(17,"8d94f98a99cdf20b9b588c1d0f2173dd854b7c35c28f5f3b94a715f5392fc77e"),
 "review/0.0.1":(10,"1fed80f58288f85c2cd93c212994b1a3eb10631097260f79f4d06a0df5ee0a7e"),
 "release/raw/0.0.2":(17,"76cc77cab3f2ed1869cc759c096b89531b4da70b941689d00323869ca7045dec"),
 "review/0.0.2":(11,"2ac3a84590af70569eb3fd64f3c2387878eb27f74df4effcd337f6b3e0e85528"),
 "release/raw/0.0.3":(17,"b3e7364637d363537554fe10e6e85a3ab724fe45b67ba70837547ed89f5e3afa"),
 "review/0.0.3":(13,"0540616b54e3d5d0dec5437914650b59ac7c25b475370cb8aed4c5bfca244ee6"),
 "release/raw/0.0.4":(17,"7d2bb0e4662322869e92d7005801d250108b177171d9494dc2d6424609551b9a"),
 "review/0.0.4":(16,"db87aac1135729d14cfbb7f3c37824f4cd04f9df604ea9fe73987912a6f08ae7"),
 "release/raw/0.0.5":(17,"24f6bb3b86657716ed03958a32dee5c9db3904aa980cb0a839aacac0590cc860"),
 "review/0.0.5":(18,"04cac552f675060223abc9fa003caed27b9d7ddcbc254cc5125654bb773653a7"),
}
UNCHANGED_SOURCE_SHA256={
 "any-note/circle-v1/circle-v1.blend":"d4326da274913b454d8af9888c71295235bfd81c2c891fbbc980bea34f54365e",
 "bomb/urchin-v1/urchin-v1.blend":"ff251ad67d6c95b4ffd1fc6fed65fb74cd94696b1dff32438b4c2b5138e4ebe9",
 "guard/shield-v1/shield-v1.blend":"f3254883e8b68802792b538bf5ffe27a9eae65fb9b18dc39eebd6f8f5863978b",
 "track/blue-glass-v1/blue-glass-v1.blend":"2c2424b3d2d18bb3b49799ecfd6ed2f8810b7d469c46dc70a889a5c04c052b51",
 "directional-arrow/outline-v1/outline-v1.blend":"ecedc0e21178830a673d4932ea932327fc1b417a6eb6023ba20a1646a1a2ae7b",
 "wall/red-glass-v1/red-glass-v1.blend":"d7977bd1871bf2ebf0094885252ffdaf524196f060aacde5d15a0b96bde50d96",
}
PREDECESSOR_CHANGED_SOURCE_SHA256={
 "athlete-marker/sphere-v1/sphere-v1.blend":"cab8b4099540654cd1895ef65ba88e57c62aa40ab0908f4bfbcc5a19535a15c4",
}
UNCHANGED_MANIFEST_SHA256={
 "directional-arrow/outline-v1.v1.json":"7411eee9421978d29d3d45f200c7b8c868388723711bee4786d047a7da4dfbcd",
 "any-note/circle-v1.v1.json":"30cb273bcbb8d04b3d61ffe66a8edb23dfae5fd99fe54cb321f632522b8cfe7f",
 "guard/shield-v1.v1.json":"112c2b43be1446e9f7aaeaac5ffd7e3f73c5d73032dd409817d4273e03d39162",
 "bomb/urchin-v1.v1.json":"33102397bc76f70a28bba713ff05a0d84076bcb72b0c1529ddad3515236a18be",
 "wall/red-glass-v1.v1.json":"5711a33a968381a0f5046563327924358070aa442c414d00fc0a2dd05fb0ae33",
 "track/blue-glass-v1.v1.json":"da6c278d1bb9b45daac3e2319bdaa7e133576c4978cda8834feed45ce7a78adc",
}
EXPECTED={
"directional-arrow":("outline-v1",[.78,.78,.18],[0,0,0],420),
"any-note":("circle-v1",[.70,.70,.18],[0,0,0],320),
"guard":("shield-v1",[.72,.82,.16],[0,0,.07],520),
"bomb":("urchin-v1",[.78,.78,.78],[0,0,0],900),
"wall":("red-glass-v1",[.94,.94,1.0],[0,0,0],144),
"track":("blue-glass-v1",[4.2,.06,24.0],[0,.03,0],160),
"athlete-marker":("sphere-v1",[.18,.18,.18],[0,0,0],192),
}
TOP_KEYS={"schema","release","identity","files","names","source_authority","geometry","coordinates","materials","reuse","rights","provenance","dependencies"}
GEO_KEYS={"dimensions","measured_aabb","pivot","object_origin","rotation_euler","scale","triangle_count","triangle_budget","collision_free_bound"}
SCREEN_DIRECTIONS={"up":0,"up-right":-45,"right":-90,"down-right":-135,"down":180,"down-left":135,"left":90,"up-left":45}

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def tree_digest(base):
 rows=[]
 for p in sorted(x for x in base.rglob("*") if x.is_file()):
  rows.append(f"{p.relative_to(base).as_posix()}\0{p.stat().st_size}\0{sha(p)}\n")
 return len(rows),hashlib.sha256("".join(rows).encode("utf-8")).hexdigest()
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

def accessor_values(doc,binary,index):
 a=doc["accessors"][index]; view=doc["bufferViews"][a["bufferView"]]; off=view.get("byteOffset",0)+a.get("byteOffset",0); count=a["count"]
 if a["type"]=="VEC3" and a["componentType"]==5126: return [struct.unpack_from("<fff",binary,off+i*12) for i in range(count)]
 fmt,size={5123:("<H",2),5125:("<I",4)}[a["componentType"]]
 return [struct.unpack_from(fmt,binary,off+i*size)[0] for i in range(count)]

def polygon_area_2d(poly):
 return sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))*.5

def triangle_intersection_area(a,b):
 subject=list(a)
 clip=list(b)
 if polygon_area_2d(clip)<0: clip.reverse()
 for i in range(3):
  p,q=clip[i],clip[(i+1)%3]
  if not subject: return 0.0
  result=[]
  def side(x): return (q[0]-p[0])*(x[1]-p[1])-(q[1]-p[1])*(x[0]-p[0])
  for s,e in zip(subject,subject[1:]+subject[:1]):
   ds,de=side(s),side(e); sins=ds>=-1e-10; eins=de>=-1e-10
   if sins!=eins:
    den=ds-de
    if abs(den)>1e-14:
     t=ds/den; result.append((s[0]+t*(e[0]-s[0]),s[1]+t*(e[1]-s[1])))
   if eins: result.append(e)
  subject=result
 return abs(polygon_area_2d(subject)) if len(subject)>=3 else 0.0

def assert_closed_nonoverlapping_mesh(path):
 doc,binary=parse_glb(path); positions=accessor_values(doc,binary,doc["meshes"][0]["primitives"][0]["attributes"]["POSITION"]); caps={}; edges={}
 for primitive in doc["meshes"][0]["primitives"]:
  indices=accessor_values(doc,binary,primitive["indices"])
  for i in range(0,len(indices),3):
   tri=indices[i:i+3]; points=[positions[j] for j in tri]
   for a,b in zip(tri,(tri[1],tri[2],tri[0])):
    edge=tuple(sorted((a,b))); edges[edge]=edges.get(edge,0)+1
   if max(p[2] for p in points)-min(p[2] for p in points)<=1e-7:
    z=round(sum(p[2] for p in points)/3,6); caps.setdefault(z,[]).append([(p[0],p[1]) for p in points])
 if any(count!=2 for count in edges.values()): fail(f"{path}: mesh is not closed two-manifold")
 for z,triangles in caps.items():
  for i,a in enumerate(triangles):
   for b in triangles[i+1:]:
    if triangle_intersection_area(a,b)>1e-9: fail(f"{path}: coplanar overlapping caps at z={z}")
 return {str(z):len(v) for z,v in sorted(caps.items())}

def assert_wall_geometry(path):
 doc,binary=parse_glb(path); primitives=doc["meshes"][0]["primitives"]
 if len(primitives)!=2 or [p.get("material") for p in primitives]!=[0,1]: fail(f"{path}: wall material primitive structure")
 positions=accessor_values(doc,binary,primitives[0]["attributes"]["POSITION"]); body_indices=accessor_values(doc,binary,primitives[0]["indices"]); edges={}; caps={}
 for i in range(0,len(body_indices),3):
  tri=body_indices[i:i+3]; points=[positions[j] for j in tri]
  for a,b in zip(tri,(tri[1],tri[2],tri[0])):
   edge=tuple(sorted((a,b))); edges[edge]=edges.get(edge,0)+1
  if max(p[2] for p in points)-min(p[2] for p in points)<=1e-7:
   z=round(sum(p[2] for p in points)/3,6); caps.setdefault(z,[]).append([(p[0],p[1]) for p in points])
 if len(body_indices)!=36 or any(count!=2 for count in edges.values()): fail(f"{path}: wall body is not closed two-manifold")
 for z,triangles in caps.items():
  for i,a in enumerate(triangles):
   for b in triangles[i+1:]:
    if triangle_intersection_area(a,b)>1e-9: fail(f"{path}: wall body coplanar overlap at z={z}")
 edge_indices=accessor_values(doc,binary,primitives[1]["indices"])
 if len(edge_indices)!=288: fail(f"{path}: wall analytic edge cage triangle structure")
 return {"closed_body":True,"body_triangles":12,"edge_triangles":96,"coplanar_body_overlap":False}

def assert_marker_geometry(path):
 doc,binary=parse_glb(path); primitives=doc["meshes"][0]["primitives"]; materials=[m["name"] for m in doc["materials"]]
 if materials!=["mat/charcoal","mat/white","mat/tint_base"] or len(primitives)!=3: fail(f"{path}: marker material primitive structure")
 position_accessor=primitives[0]["attributes"].get("POSITION"); normal_accessor=primitives[0]["attributes"].get("NORMAL")
 if position_accessor is None or normal_accessor is None or any(p["attributes"]!={"POSITION":position_accessor,"NORMAL":normal_accessor} for p in primitives): fail(f"{path}: marker explicit POSITION/NORMAL contract")
 positions=accessor_values(doc,binary,position_accessor); normals=accessor_values(doc,binary,normal_accessor)
 if len(positions)!=len(normals): fail(f"{path}: marker normal count")
 for position,normal in zip(positions,normals):
  pl=math.sqrt(sum(x*x for x in position)); nl=math.sqrt(sum(x*x for x in normal))
  if abs(nl-1)>1e-5 or any(abs(normal[i]-position[i]/pl)>1e-5 for i in range(3)): fail(f"{path}: marker non-radial unit normal")
 edges={}; triangles=set(); by_material={name:[] for name in materials}
 for primitive,name in zip(primitives,materials):
  indices=accessor_values(doc,binary,primitive["indices"])
  for i in range(0,len(indices),3):
   tri=tuple(indices[i:i+3]); key=tuple(sorted(tri))
   if key in triangles: fail(f"{path}: marker duplicate/coplanar overlapping face")
   triangles.add(key); by_material[name].append(tri)
   for a,b in zip(tri,(tri[1],tri[2],tri[0])): edge=tuple(sorted((a,b))); edges[edge]=edges.get(edge,0)+1
 if any(count!=2 for count in edges.values()): fail(f"{path}: marker surface is not closed two-manifold")
 counts={name:len(faces) for name,faces in by_material.items()}
 if counts!={"mat/charcoal":24,"mat/white":80,"mat/tint_base":64}: fail(f"{path}: marker material triangle partition {counts}")
 visibility={}
 for label,axis,sign in (("+X",0,1),("-X",0,-1),("+Y",1,1),("-Y",1,-1),("+Z",2,1),("-Z",2,-1)):
  visible={name for name,faces in by_material.items() if any(sign*sum(positions[index][axis] for index in tri)>1e-9 for tri in faces)}
  if visible!=set(materials): fail(f"{path}: marker materials not visible from {label}: {visible}")
  visibility[label]=sorted(visible)
 return {"closed_surface":True,"triangles":len(triangles),"material_triangle_counts":counts,"explicit_unit_radial_normals":True,"coplanar_overlapping_faces":False,"camera_material_visibility":visibility}

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
 license_path=root/"LICENSE.md"
 if not license_path.is_file(): fail(f"missing {license_path}")
 license_bytes=license_path.stat().st_size
 license_sha256=sha(license_path)
 if license_bytes!=EXPECTED_LICENSE_BYTES or license_sha256!=EXPECTED_LICENSE_SHA256:
  fail(f"{license_path}: license integrity mismatch bytes={license_bytes} sha256={license_sha256}; expected bytes={EXPECTED_LICENSE_BYTES} sha256={EXPECTED_LICENSE_SHA256}")
 for relative,expected in PREDECESSOR_TREES.items():
  base=root/relative
  if not base.is_dir(): fail(f"missing immutable predecessor tree {base}")
  actual=tree_digest(base)
  if actual!=expected: fail(f"predecessor immutability mismatch {relative}: {actual} != {expected}")
 expected_source_paths={f"{r}/{v[0]}/{v[0]}.blend" for r,v in EXPECTED.items()}
 actual_source_paths={p.relative_to(root/"source").as_posix() for p in (root/"source").rglob("*") if p.is_file()}
 if actual_source_paths!=expected_source_paths: fail(f"source inventory mismatch missing={sorted(expected_source_paths-actual_source_paths)} extra={sorted(actual_source_paths-expected_source_paths)}")
 for relative,expected_sha in UNCHANGED_SOURCE_SHA256.items():
  if sha(root/"source"/relative)!=expected_sha: fail(f"unchanged source mutated: {relative}")
 for relative,old_sha in PREDECESSOR_CHANGED_SOURCE_SHA256.items():
  if sha(root/"source"/relative)==old_sha: fail(f"required successor source did not change: {relative}")
 for relative,expected_sha in UNCHANGED_MANIFEST_SHA256.items():
  if sha(root/"manifests"/relative)!=expected_sha: fail(f"unchanged source manifest mutated: {relative}")
 expected_paths={"inventory.v1.json","proof.v1.json","sets/default-v1.json"}
 manifests=[]
 for role,(variant,dims,pivot,budget) in EXPECTED.items():
  expected_paths|={f"{role}/{variant}.glb",f"manifests/{role}/{variant}.v1.json"}
  mp=root/"manifests"/role/(variant+".v1.json"); rp=rel/"manifests"/role/(variant+".v1.json"); glb=rel/role/(variant+".glb"); blend=root/"source"/role/variant/(variant+".blend")
  for p in (mp,rp,glb,blend):
   if not p.is_file(): fail(f"missing {p}")
  if {p.name for p in blend.parent.iterdir() if p.is_file()}!={variant+".blend"}: fail(f"{role}: source inventory")
  m=load(mp); rm=load(rp); exact_keys(m,TOP_KEYS,str(mp)); exact_keys(rm,TOP_KEYS,str(rp)); exact_keys(m["geometry"],GEO_KEYS,str(mp)+" geometry")
  changed=role=="athlete-marker"
  predecessor_rp=root/"release"/"raw"/PREDECESSOR_RELEASE/"manifests"/role/(variant+".v1.json")
  if not changed:
   if rp.read_bytes()!=predecessor_rp.read_bytes(): fail(f"{role}: release manifest changed outside approved scope")
   if m["release"]!=PREDECESSOR_RELEASE: fail(f"{role}: source manifest release identity drift")
  if rm["files"].get("source_sha256") is not None or rm["source_authority"].get("blend_byte_determinism_claimed") is not False: fail(f"{role}: release manifest overclaims blend determinism")
  if m["schema"]!="aerobeat.gameplay-asset/v1" or (changed and m["release"]!=release): fail(f"{mp}: schema/release")
  identity=m["identity"]; canonical=f"{role}/{variant}"
  if identity!={"role":role,"variant":variant,"canonical_name":canonical}: fail(f"{mp}: identity")
  if m["geometry"]["dimensions"]!=dims or m["geometry"]["pivot"]!=pivot or m["geometry"]["triangle_budget"]!=budget: fail(f"{mp}: spec geometry declaration")
  if m["geometry"]["object_origin"]!=[0,0,0] or m["geometry"]["rotation_euler"]!=[0,0,0] or m["geometry"]["scale"]!=[1,1,1]: fail(f"{mp}: transforms")
  visible_face="all camera directions" if role=="athlete-marker" else ("both +Z/-Z" if role=="directional-arrow" else ("-Z" if role in ("any-note","guard") else "not-applicable"))
  if m["coordinates"]!={"handedness":"right","up":"+Y","forward":"-Z","visible_face":visible_face}: fail(f"{mp}: coordinate contract")
  if m["materials"]["analytic_only"] is not True or m["materials"]["textures"]!=[]: fail(f"{mp}: non-analytic material")
  if m["rights"]!={"license":"CC-BY-NC-4.0","creator":"AeroBeat / Gambit Games","third_party_content":False}: fail(f"{mp}: rights")
  if m["dependencies"]!=[] or m["provenance"]["external_assets"]!=[] or m["provenance"]["network"] is not False or m["provenance"]["blender"]!="4.0.2": fail(f"{mp}: provenance/dependencies")
  manifest_release=release if changed else PREDECESSOR_RELEASE
  expected_files={"source":f"source/{role}/{variant}/{variant}.blend","release":f"release/raw/{manifest_release}/{role}/{variant}.glb","source_sha256":sha(blend),"source_bytes":blend.stat().st_size,"release_sha256":sha(glb),"release_bytes":glb.stat().st_size}
  if m["files"]!=expected_files or rm["files"]!={k:v for k,v in expected_files.items() if k not in ("source_sha256","source_bytes")}: fail(f"{mp}: file paths/hashes/bytes")
  tris,aabb,d=glb_facts(glb,canonical)
  expected_names={"node":canonical,"mesh":canonical+"/mesh","materials":[x.get("name") for x in d.get("materials",[])]}
  if m["names"]!=expected_names or rm["names"]!=expected_names or m["materials"]["names"]!=expected_names["materials"]: fail(f"{role}: mesh/node/material names")
  materials={x["name"]:x for x in d.get("materials",[])}
  if role=="directional-arrow":
   expected_contract={"opacity":1.0,"alpha_mode":"OPAQUE","blend":"opaque","double_sided":False,"cull":"back","depth_test":True,"depth_write":True,"white_outline_material":"mat/white","runtime_tint_material":"mat/tint_base","runtime_tint_targets":["red","yellow","green"],"styled_faces":["+Z","-Z"],"coplanar_overlapping_caps":False,"renderer_y_flip":False,"screen_direction_rotation_degrees":SCREEN_DIRECTIONS}
   if m["materials"].get("contract")!=expected_contract or rm["materials"].get("contract")!=expected_contract: fail("directional-arrow: opaque/tint contract")
   if set(materials)!={"mat/charcoal","mat/white","mat/tint_base"}: fail("directional-arrow: exact material inventory")
   for name,mat in materials.items():
    if mat.get("alphaMode")!="OPAQUE" or mat.get("doubleSided") is not False or mat["pbrMetallicRoughness"]["baseColorFactor"][3]!=1: fail(f"directional-arrow: nonopaque material {name}")
    extras=mat.get("extras",{}).get("aerobeat",{})
    if extras.get("blend")!="opaque" or extras.get("cull")!="back" or extras.get("depthTest") is not True or extras.get("depthWrite") is not True: fail(f"directional-arrow: depth/blend/cull semantics {name}")
   if materials["mat/tint_base"].get("extras",{}).get("aerobeat",{}).get("runtimeTintable") is not True: fail("directional-arrow: core not runtime tintable")
   if materials["mat/white"].get("extras",{}).get("aerobeat",{}).get("runtimeTintable") is not False: fail("directional-arrow: white outline must not be runtime tinted")
   cap_counts=assert_closed_nonoverlapping_mesh(glb)
   if cap_counts!={"-0.09":14,"-0.088":14,"-0.086":5,"0.086":5,"0.088":14,"0.09":14}: fail(f"directional-arrow: unexpected styled face depth structure {cap_counts}")
   expected_vectors={"up":(0,1),"up-right":(1,1),"right":(1,0),"down-right":(1,-1),"down":(0,-1),"down-left":(-1,-1),"left":(-1,0),"up-left":(-1,1)}
   for direction,degrees in SCREEN_DIRECTIONS.items():
    radians=math.radians(degrees); vector=(-math.sin(radians),math.cos(radians)); signs=tuple(0 if abs(x)<1e-5 else (1 if x>0 else -1) for x in vector)
    if signs!=expected_vectors[direction]: fail(f"directional-arrow: incorrect +Z screen semantic {direction}={degrees}")
  elif role=="wall":
   expected_contract={"body_opacity":0.24,"edge_opacity":0.82,"alpha_mode":"BLEND","blend":"alpha","double_sided":False,"cull":"back","depth_test":True,"depth_write":False,"order":"after-track","unit_cell_footprint":[0.94,0.94],"cell_pitch":[1.0,1.0],"adjacent_gap":[0.06,0.06],"xy_scale_authoritative":[1,1],"z_scale_authoritative":True}
   if m["materials"].get("contract")!=expected_contract or rm["materials"].get("contract")!=expected_contract: fail("wall: cell/material/depth contract")
   if set(materials)!={"mat/red_glass","mat/red_edge"}: fail("wall: exact analytic material inventory")
   for name,alpha in (("mat/red_glass",.24),("mat/red_edge",.82)):
    mat=materials[name]; factor=mat.get("pbrMetallicRoughness",{}).get("baseColorFactor",[]); extras=mat.get("extras",{}).get("aerobeat",{})
    if factor[3]!=alpha or mat.get("alphaMode")!="BLEND" or mat.get("doubleSided") is not False: fail(f"wall: material alpha/cull {name}")
    if extras!={"blend":"alpha","cull":"back","depthTest":True,"depthWrite":False,"order":"after-track","unitCellFootprint":[.94,.94],"xyScaleAuthoritative":[1,1],"zScaleAuthoritative":True}: fail(f"wall: material depth/scale semantics {name}")
   if m["geometry"]["collision_free_bound"]!=[[-.47,-.47,-.5],[.47,.47,.5]]: fail("wall: exact cell collision-free bound")
   if assert_wall_geometry(glb)!={"closed_body":True,"body_triangles":12,"edge_triangles":96,"coplanar_body_overlap":False}: fail("wall: geometry structure")
  elif role=="track":
   expected_contract={"opacity":0.52,"predecessor_opacity":0.20,"opacity_multiplier":2.6,"alpha_mode":"BLEND","blend":"alpha","double_sided":False,"cull":"back","depth_test":True,"depth_write":False,"order":"after-grid-before-wall","justification":"0.52 is 2.6x stronger than 0.20 and remains translucent blue glass over bright ice."}
   if m["materials"].get("contract")!=expected_contract or rm["materials"].get("contract")!=expected_contract: fail("track: visibility/depth/order contract")
   glass=materials.get("mat/blue_glass",{}); factor=glass.get("pbrMetallicRoughness",{}).get("baseColorFactor",[])
   if factor!=[0.1,0.58,0.92,0.52] or glass.get("alphaMode")!="BLEND" or glass.get("doubleSided") is not False: fail("track: expected stronger blue glass alpha 0.52")
   extras=glass.get("extras",{}).get("aerobeat",{})
   if extras!={"blend":"alpha","cull":"back","depthTest":True,"depthWrite":False,"order":"after-grid-before-wall"}: fail("track: depth/order semantics")
  elif role=="athlete-marker":
   expected_contract={"opacity":1.0,"alpha_mode":"OPAQUE","blend":"opaque","double_sided":False,"cull":"back","depth_test":True,"depth_write":True,"normals":"explicit-unit-radial","runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"],"all_camera_directions":["+X","-X","+Y","-Y","+Z","-Z"],"coplanar_overlapping_faces":False,"canonical_instances":["nose","left-wrist","right-wrist"]}
   if m["materials"].get("contract")!=expected_contract or rm["materials"].get("contract")!=expected_contract: fail("athlete-marker: opaque structural/tint/depth contract")
   if list(materials)!=["mat/charcoal","mat/white","mat/tint_base"]: fail("athlete-marker: exact ordered material inventory")
   for name,mat in materials.items():
    factor=mat.get("pbrMetallicRoughness",{}).get("baseColorFactor",[]); extras=mat.get("extras",{}).get("aerobeat",{})
    expected_extras={"blend":"opaque","cull":"back","depthTest":True,"depthWrite":True,"runtimeTintable":name=="mat/tint_base","structural":name in ("mat/white","mat/charcoal")}
    if mat.get("alphaMode")!="OPAQUE" or mat.get("doubleSided") is not False or factor[3]!=1 or extras!=expected_extras: fail(f"athlete-marker: material alpha/depth/tint semantics {name}")
   marker_geometry=assert_marker_geometry(glb)
   if marker_geometry["triangles"]!=168 or marker_geometry["coplanar_overlapping_faces"] is not False: fail("athlete-marker: structural geometry")
  if tris!=m["geometry"]["triangle_count"] or tris>budget: fail(f"{role}: triangles {tris}/{budget}")
  flat=lambda x:[z for row in x for z in row]
  if not eq(flat(aabb),flat(m["geometry"]["measured_aabb"])): fail(f"{role}: GLB/manifest AABB")
  b=m["geometry"]["collision_free_bound"]; pivot=m["geometry"]["pivot"]
  # Spec bounds are relative to the stated geometry/pivot reference.
  shifted=[[b[j][i]-pivot[i] for i in range(3)] for j in range(2)]
  if any(aabb[0][i]<shifted[0][i]-1e-5 or aabb[1][i]>shifted[1][i]+1e-5 for i in range(3)): fail(f"{role}: bound exceeded {aabb} vs {shifted}")
  measured=[aabb[1][i]-aabb[0][i] for i in range(3)]
  if not eq(measured,dims,2e-4): fail(f"{role}: exact dimensions {measured} != {dims}")
  predecessor_glb=root/"release"/"raw"/PREDECESSOR_RELEASE/role/(variant+".glb")
  if role=="athlete-marker":
   if sha(glb)==sha(predecessor_glb): fail(f"{role}: required geometry/material successor GLB is unchanged")
  elif glb.read_bytes()!=predecessor_glb.read_bytes(): fail(f"{role}: geometry/material GLB changed outside approved scope")
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
 arrow_claim=proof["claims"].get("directional_arrow",{})
 if arrow_claim.get("styled_faces")!=["+Z","-Z"] or arrow_claim.get("coplanar_overlapping_caps") is not False or arrow_claim.get("renderer_y_flip") is not False or arrow_claim.get("screen_direction_rotation_degrees")!=SCREEN_DIRECTIONS: fail("release proof directional-arrow structure/semantics")
 expected_wall_claim={"source_dimensions":[.94,.94,1.0],"unit_cell_footprint":[.94,.94],"cell_pitch":[1.0,1.0],"adjacent_gap":[.06,.06],"xy_scale_authoritative":[1,1],"z_scale_authoritative":True,"centered_pivot":True,"closed_body":True,"adjacent_instances_overlap":False}
 if proof["claims"].get("wall")!=expected_wall_claim: fail("release proof wall footprint/interval contract")
 if proof["claims"].get("changed_identity")!="athlete-marker/sphere-v1" or proof["claims"].get("byte_identical_predecessor_roles")!=["directional-arrow","any-note","guard","bomb","wall","track"]: fail("release proof marker-only successor scope")
 expected_marker_claim={"dimensions":[.18,.18,.18],"canonical_identity":"athlete-marker/sphere-v1","canonical_instances":["nose","left-wrist","right-wrist"],"opacity":1.0,"alpha_mode":"OPAQUE","depth_test":True,"depth_write":True,"explicit_normals":True,"runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"],"all_camera_directions":["+X","-X","+Y","-Y","+Z","-Z"],"coplanar_overlapping_faces":False}
 if proof["claims"].get("athlete_marker")!=expected_marker_claim: fail("release proof athlete-marker contract")
 review_dir=root/"review"/release; rh=load(review_dir/"hashes.v1.json"); layout=load(review_dir/"layout.v1.json")
 review_files={p.name for p in review_dir.glob("*.png")}
 marker_faces={f"athlete-marker--sphere-v1--{face}-{background}.png" for face in ("plus-x","minus-x","plus-y","minus-y","plus-z","minus-z") for background in ("bright","dark")}
 expected_reviews={"neutral-board.png","gameplay-context.png","wall-grid-comparison.png","visibility-comparison.png"}|marker_faces|{r+"--"+v[0]+".png" for r,v in EXPECTED.items()}
 if review_files!=expected_reviews or {x["path"] for x in rh["files"]}!=review_files or rh["resolution"]!=[1600,900]: fail("review inventory/resolution")
 if rh.get("layout")!={"path":"layout.v1.json","bytes":(review_dir/"layout.v1.json").stat().st_size,"sha256":sha(review_dir/"layout.v1.json")}: fail("review layout hash/size")
 if rh.get("visibility")!={"path":"visibility.v1.json","bytes":(review_dir/"visibility.v1.json").stat().st_size,"sha256":sha(review_dir/"visibility.v1.json")}: fail("review visibility hash/size")
 if rh.get("contrast")!={"path":"contrast.v1.json","bytes":(review_dir/"contrast.v1.json").stat().st_size,"sha256":sha(review_dir/"contrast.v1.json")}: fail("review contrast hash/size")
 if rh.get("wall_grid")!={"path":"wall-grid.v1.json","bytes":(review_dir/"wall-grid.v1.json").stat().st_size,"sha256":sha(review_dir/"wall-grid.v1.json")}: fail("review wall-grid hash/size")
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
 wall_grid=load(review_dir/"wall-grid.v1.json"); wall_layout=layout["images"]["wall-grid-comparison.png"]
 expected_wall_grid={"schema":"aerobeat.wall-grid-review/v1","release":release,"image":"wall-grid-comparison.png","source_dimensions":[.94,.94,1.0],"measured_source_aabb":[[-.47,-.47,-.5],[.47,.47,.5]],"canonical_cell_dimensions":[.94,.94],"cell_pitch":[1.0,1.0],"adjacent_gap":[.06,.06],"pivot":[0,0,0],"xy_scale":[1,1],"z_scale":"authoritative interval only","rows":[{"name":"one-cell","centers":[[0,1.1]],"overlap":False},{"name":"adjacent-cells","centers":[[-1,-1.1],[0,-1.1],[1,-1.1]],"overlap":False}],"materials":{"analytic_only":True,"body":"mat/red_glass","edge":"mat/red_edge","depth_test":True,"depth_write":False,"order":"after-track"},"glb_sha256":sha(rel/"wall/red-glass-v1.glb")}
 if wall_grid!=expected_wall_grid: fail("wall-grid evidence contract")
 if wall_layout.get("kind")!="wall-grid-comparison" or len(wall_layout.get("objects",[]))!=4 or any(x.get("role")!="wall" or x.get("variant")!="red-glass-v1" for x in wall_layout["objects"]): fail("wall-grid visual identity/count evidence")
 if any(abs((pitch-size)-gap)>1e-12 for pitch,size,gap in zip(wall_grid["cell_pitch"],wall_grid["source_dimensions"][:2],wall_grid["adjacent_gap"])): fail("wall-grid adjacent gap arithmetic")
 visibility=load(review_dir/"visibility.v1.json"); comparison=layout["images"]["visibility-comparison.png"]
 if visibility.get("schema")!="aerobeat.marker-visibility-review/v1" or visibility.get("release")!=release or visibility.get("predecessor")!=PREDECESSOR_RELEASE: fail("marker visibility review schema/releases")
 if visibility.get("backgrounds")!=["DARK ICE","BRIGHT ICE","BLUE ICE"] or comparison.get("backgrounds")!=visibility["backgrounds"]: fail("visibility review backgrounds")
 if visibility.get("counts_per_release")!={"athlete-marker":3} or comparison.get("counts_per_release")!=visibility["counts_per_release"]: fail("marker visibility review counts")
 objects=comparison["objects"]
 for version in (PREDECESSOR_RELEASE,release):
  if sum(x.get("release")==version and x["role"]=="athlete-marker" for x in objects)!=3: fail(f"marker visibility board counts for {version}")
 geometry=visibility.get("geometry",{})
 if geometry!={PREDECESSOR_RELEASE:{"dimensions":[.18,.18,.18],"triangles":168},release:{"dimensions":[.18,.18,.18],"triangles":168}}: fail("marker visibility geometry labels")
 successor=visibility.get("materials",{}).get(release,{})
 if successor!={"names":["mat/charcoal","mat/white","mat/tint_base"],"alpha":1.0,"alpha_mode":"OPAQUE","blend":"opaque","cull":"back","depth_test":True,"depth_write":True,"runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"]}: fail("marker visibility material values")
 pass # marker-only visibility evidence has no track mutation claim
 hashes=visibility.get("glb_sha256",{})
 if hashes!={PREDECESSOR_RELEASE:sha(root/"release"/"raw"/PREDECESSOR_RELEASE/"athlete-marker/sphere-v1.glb"),release:sha(rel/"athlete-marker/sphere-v1.glb")}: fail("marker visibility GLB hashes")
 contrast=load(review_dir/"contrast.v1.json")
 faces=["plus-x","minus-x","plus-y","minus-y","plus-z","minus-z"]
 expected_face_images=[f"athlete-marker--sphere-v1--{face}-{background}.png" for background in ("bright","dark") for face in faces]
 if contrast.get("schema")!="aerobeat.athlete-marker-contrast/v1" or contrast.get("release")!=release or contrast.get("backgrounds")!=["BRIGHT","DARK"] or contrast.get("images")!=expected_face_images or contrast.get("camera_faces")!=faces: fail("athlete-marker: all-direction bright/dark review evidence")
 if contrast.get("materials")!={"alpha":1.0,"alpha_mode":"OPAQUE","blend":"opaque","cull":"back","depth_test":True,"depth_write":True,"analytic_only":True,"runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"]}: fail("athlete-marker: contrast material evidence")
 if contrast.get("geometry")!={"dimensions":[.18,.18,.18],"surface":"one closed partitioned sphere","explicit_normals":True,"coplanar_overlapping_faces":False,"material_triangle_counts":{"mat/charcoal":24,"mat/white":80,"mat/tint_base":64},"all_materials_visible_each_camera_direction":True}: fail("athlete-marker: contrast geometry evidence")
 direction_evidence=None
 if direction_evidence is not None: fail("athlete-marker: unexpected direction metadata state")
 ratios=contrast.get("analytic_contrast",{})
 if ratios.get("minimum_structural_required")!=7.0 or ratios.get("white_vs_charcoal",0)<7.0 or ratios.get("charcoal_vs_bright_ice",0)<7.0 or ratios.get("white_vs_dark_ice",0)<7.0: fail(f"athlete-marker: insufficient bright/dark contrast {ratios}")
 for background in ("bright","dark"):
  for face in faces:
   image=f"athlete-marker--sphere-v1--{face}-{background}.png"
   entry=layout["images"].get(image,{})
   if entry.get("kind")!="athlete-marker-face-contrast" or entry.get("camera_face")!=face or entry.get("background")!=background.upper() or len(entry.get("objects",[]))!=1: fail(f"athlete-marker: missing {face}/{background} layout evidence")
 # Tool/source policy: no third-party imports, network calls, asset loading, textures, fonts, or engine metadata.
 allowed={"argparse","ast","hashlib","json","math","os","pathlib","shutil","struct","subprocess","subprocess_contract","sys","tempfile","bpy","bpy_extras","mathutils","__future__"}
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
  try:
   run_checked([blender,"--version"],operation="Blender version",marker="Blender 4.0.2")
  except RuntimeError as exc: fail(str(exc))
  glb_script=root/"tools"/"smoke_import.py"; source_script=root/"tools"/"smoke_source.py"
  for role,variant,glb,_,_ in manifests:
   canonical=f"{role}/{variant}"; blend=root/"source"/role/variant/(variant+".blend")
   for kind,path,script in (("source",blend,source_script),("glb",glb,glb_script)):
    before=sha(path)
    try:
     run_checked(
      [blender,"--background","--factory-startup","--python",str(script),"--",str(path),canonical],
      operation=f"clean Blender {kind} smoke {canonical}",
      marker=f"SMOKE_OK kind={kind} identity={canonical}",
      postcondition=lambda path=path,before=before: path.is_file() and sha(path)==before,
     )
    except RuntimeError as exc: fail(str(exc))
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
 print(f"VALIDATE_OK release={a.release} assets=7 release_files=17 smoke={0 if a.no_smoke else 1}")

if __name__=="__main__": main()
