#!/usr/bin/env python3
"""Fail-closed validator for disposable Aero Rounded 0.0.8 candidate builds."""
from __future__ import annotations
import argparse, hashlib, json, math, struct, subprocess
from collections import defaultdict, deque
from pathlib import Path

RELEASE="0.0.8"
EXPECTED={
 "directional-arrow":("rounded-outline-v1",[.78,.78,.18],[0,0,0],69,1928,2432,"note_fill",True),
 "any-note":("outlined-circle-v1",[.70,.70,.18],[0,0,0],64,1788,2176,"note_fill",True),
 "guard":("outlined-shield-v1",[.72,.82,.16],[0,0,.07],42,1172,1536,"guard_fill",False),
}
UNCHANGED=(("bomb","urchin-v1"),("wall","red-glass-v1"),("track","blue-glass-v1"),("athlete-marker","sphere-v1"))
IMMUTABLE_GIT_TREES={
 "release/raw/0.0.1":"8e8879a750aa70715fd1ae45e62a447c8e9cd8b6",
 "release/raw/0.0.2":"c2dedfd9c18a2260f53b7c013ec77a8dcb10c877",
 "release/raw/0.0.3":"aa37bf534cc592a4057127876d567eadc3496f49",
 "release/raw/0.0.4":"be36bbd03647bfb4654e0be1ed8b3f6446ced4ec",
 "release/raw/0.0.5":"000653eace4b93f3c5d2eef11bd5c8255008b3de",
 "release/raw/0.0.6":"53181edfdb560de2aeae01e9a05c212a9b93e438",
 "release/raw/0.0.7":"846c41297230b5077ab1119880b729cc120e1098",
 "review/0.0.1":"f0cd9a0a9fdbc7519db5a5f8515d61d479dc22c9",
 "review/0.0.2":"b4c68d81faba791ebe7361f9d5a8c1bf339b5e96",
 "review/0.0.3":"9122d32d6272854f6fc0f3a29b74997cee799bcf",
 "review/0.0.4":"8342d83194d8375886f371d6d57c6fcdda677a6f",
 "review/0.0.5":"a1781ce69ba81d660e4ffb24ae8b47d3873c63bb",
 "review/0.0.6":"f5652c80852153e746774579e4c1fb495ea360f3",
 "review/0.0.7":"8ca78c143d78743ff1dfce1b9fcadc5755a02530",
}

def fail(message): raise AssertionError(message)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def parse_glb(path):
 data=path.read_bytes(); magic,version,total=struct.unpack_from("<4sII",data,0)
 if (magic,version,total)!=(b"glTF",2,len(data)): fail(f"{path}: invalid GLB")
 json_size,json_type=struct.unpack_from("<I4s",data,12)
 if json_type!=b"JSON": fail(f"{path}: JSON chunk")
 doc=json.loads(data[20:20+json_size].decode().rstrip(" \0")); offset=20+json_size
 bin_size,bin_type=struct.unpack_from("<I4s",data,offset)
 if bin_type!=b"BIN\0": fail(f"{path}: BIN chunk")
 if doc.get("images") or doc.get("textures") or any("uri" in value for value in doc.get("buffers",[])): fail(f"{path}: external dependency")
 return doc,data[offset+8:offset+8+bin_size]
def accessor(doc,binary,index):
 value=doc["accessors"][index]; view=doc["bufferViews"][value["bufferView"]]; start=view.get("byteOffset",0)+value.get("byteOffset",0)
 if value["componentType"]==5126 and value["type"]=="VEC3": return [struct.unpack_from("<fff",binary,start+i*12) for i in range(value["count"])]
 fmt,size={5123:("<H",2),5125:("<I",4)}[value["componentType"]]
 return [struct.unpack_from(fmt,binary,start+i*size)[0] for i in range(value["count"])]
def qpoint(point): return tuple(round(value,7) for value in point)

def validate_cue(path,role):
 variant,dims,pivot,samples,expected_triangles,ceiling,fill_role,tintable=EXPECTED[role]
 doc,binary=parse_glb(path); primitives=doc["meshes"][0]["primitives"]
 if len(primitives)!=3: fail(f"{role}: expected three material primitives")
 attrs=primitives[0]["attributes"]
 if set(attrs)!={"POSITION","NORMAL"} or any(p["attributes"]!=attrs for p in primitives): fail(f"{role}: explicit shared POSITION/NORMAL")
 positions=accessor(doc,binary,attrs["POSITION"]); normals=accessor(doc,binary,attrs["NORMAL"])
 materials=doc["materials"]; by_name={m["name"]:m for m in materials}
 expected_names={"mat/charcoal","mat/white","mat/green" if role=="guard" else "mat/tint_base"}
 if set(by_name)!=expected_names: fail(f"{role}: material inventory {set(by_name)}")
 for name,material in by_name.items():
  expected_role="outline_charcoal" if name=="mat/charcoal" else ("outline_white" if name=="mat/white" else fill_role)
  expected_extra={"materialRole":expected_role,"runtimeTintable":expected_role=="note_fill","blend":"opaque","cull":"back","depthTest":True,"depthWrite":True}
  if material.get("alphaMode")!="OPAQUE" or material.get("doubleSided") is not False or material["pbrMetallicRoughness"]["baseColorFactor"][3]!=1 or material.get("extras",{}).get("aerobeat")!=expected_extra: fail(f"{role}: material contract {name}")
 triangles=[]; triangle_material=[]
 for primitive in primitives:
  values=accessor(doc,binary,primitive["indices"])
  for i in range(0,len(values),3): triangles.append(tuple(values[i:i+3])); triangle_material.append(materials[primitive["material"]]["name"])
 if len(triangles)!=expected_triangles or len(triangles)>ceiling or expected_triangles!=28*samples-4: fail(f"{role}: triangle formula/count {len(triangles)}")
 lo=[min(p[i] for p in positions) for i in range(3)]; hi=[max(p[i] for p in positions) for i in range(3)]
 measured=[hi[i]-lo[i] for i in range(3)]
 if any(abs(a-b)>2e-5 for a,b in zip(measured,dims)): fail(f"{role}: dimensions {measured}")
 edges=defaultdict(list); directed_edges=defaultdict(list); unique=set(); volume=0; minimum_dot=1
 for face_index,tri in enumerate(triangles):
  key=tuple(sorted(qpoint(positions[index]) for index in tri))
  if key in unique: fail(f"{role}: duplicate geometric triangle")
  unique.add(key); a,b,c=(positions[index] for index in tri)
  ab=tuple(b[i]-a[i] for i in range(3)); ac=tuple(c[i]-a[i] for i in range(3))
  cross=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]); length=math.sqrt(sum(x*x for x in cross))
  if length<=1e-10: fail(f"{role}: degenerate triangle")
  volume+=sum(a[i]*cross[i] for i in range(3))/6
  unit=tuple(x/length for x in cross)
  for index in tri:
   normal=normals[index]; normal_length=math.sqrt(sum(x*x for x in normal)); dot=sum(unit[i]*normal[i] for i in range(3))/normal_length
   minimum_dot=min(minimum_dot,dot)
   if abs(normal_length-1)>2e-5 or dot<=.90: fail(f"{role}: normal disagreement {dot}")
  qp=[qpoint(positions[index]) for index in tri]
  for left,right in zip(qp,(qp[1],qp[2],qp[0])):
   key=tuple(sorted((left,right))); edges[key].append(face_index); directed_edges[key].append((left,right))
 if volume<=0: fail(f"{role}: non-positive signed volume {volume}")
 if any(len(owners)!=2 for owners in edges.values()): fail(f"{role}: not geometric two-manifold")
 if any(pair[0]!=(pair[1][1],pair[1][0]) for pair in directed_edges.values()): fail(f"{role}: inconsistent outward winding")
 adjacency=[set() for _ in triangles]
 for owners in edges.values():
  a,b=owners; adjacency[a].add(b); adjacency[b].add(a)
 seen={0}; queue=deque([0])
 while queue:
  for neighbor in adjacency[queue.popleft()]:
   if neighbor not in seen: seen.add(neighbor); queue.append(neighbor)
 if len(seen)!=len(triangles): fail(f"{role}: disconnected exterior")
 vertices={qpoint(p) for p in positions}; euler=len(vertices)-len(edges)+len(triangles)
 if euler!=2: fail(f"{role}: Euler characteristic {euler}")
 zmin,zmax=lo[2],hi[2]
 def boundary_components(material_pair=None,z=zmax):
  graph=defaultdict(set)
  for edge,owners in edges.items():
   if not all(abs(point[2]-z)<1e-6 for point in edge): continue
   if material_pair is not None and {triangle_material[index] for index in owners}!=set(material_pair): continue
   a,b=edge[0][:2],edge[1][:2]; graph[a].add(b); graph[b].add(a)
  components=[]; unseen=set(graph)
  while unseen:
   start=next(iter(unseen)); current=start; previous=None; ordered=[]
   while current not in ordered:
    ordered.append(current); unseen.discard(current)
    choices=[point for point in graph[current] if point!=previous]
    if not choices: fail(f"{role}: open material boundary")
    previous,current=current,choices[0]
   if current!=start: fail(f"{role}: non-cycle material boundary")
   components.append(ordered)
  return components
 white_boundaries=boundary_components(("mat/charcoal","mat/white"))
 fill_name="mat/green" if role=="guard" else "mat/tint_base"
 fill_boundaries=boundary_components(("mat/charcoal",fill_name))
 if len(white_boundaries)!=2 or len(fill_boundaries)!=1 or any(len(component)!=samples for component in white_boundaries+fill_boundaries): fail(f"{role}: material boundary loops")
 white_boundaries.sort(key=lambda component:max(math.hypot(*point) for point in component),reverse=True)
 outer_white,inner_white=white_boundaries; fill_boundary=fill_boundaries[0]
 def corresponding_separation(outer,inner):
  best=None
  for candidate in (inner,list(reversed(inner))):
   for shift in range(len(candidate)):
    distances=[math.dist(outer[index],candidate[(index+shift)%len(candidate)]) for index in range(len(outer))]
    score=sum(distances)
    if best is None or score<best[0]: best=(score,min(distances))
  return best[1]
 bevel=.010 if role=="guard" else .012
 silhouette=max((component for component in boundary_components(z=zmax-bevel) if len(component)==samples),key=lambda component:max(math.hypot(*point) for point in component))
 measured_bands=(corresponding_separation(silhouette,outer_white),corresponding_separation(outer_white,inner_white),corresponding_separation(inner_white,fill_boundary))
 chord_tolerance=.0015
 if measured_bands[0]<.014*.90-chord_tolerance or measured_bands[1]<.052*.90-chord_tolerance or measured_bands[2]<.020*.90-chord_tolerance: fail(f"{role}: narrow projected bands {measured_bands}")
 for z,sign in ((zmin,-1),(zmax,1)):
  cap_faces=[i for i,tri in enumerate(triangles) if all(abs(positions[index][2]-z)<1e-6 for index in tri)]
  if not cap_faces or {triangle_material[i] for i in cap_faces}!=expected_names: fail(f"{role}: incomplete material bands at z={z}")
  if any(abs(normals[index][2]-sign)>1e-6 for i in cap_faces for index in triangles[i]): fail(f"{role}: cap normals")
 if role=="any-note":
  radii=sorted({round(math.hypot(x,y),6) for x,y,z in positions})
  for expected in (.264,.284,.336,.338,.35):
   if not any(abs(value-expected)<2e-5 for value in radii): fail(f"any-note: missing analytic radius {expected}: {radii}")
  outer=[math.hypot(x,y) for x,y,z in positions if abs(math.hypot(x,y)-.35)<2e-5]
  if not outer or min(outer)/max(outer)<.998: fail("any-note: circularity")
 return {"role":role,"samples":samples,"triangles":len(triangles),"ceiling":ceiling,"minimum_normal_dot":minimum_dot,"signed_volume":volume,"euler":euler}

def validate(authority,candidate):
 if (authority/"release/raw/0.0.8").exists() or (authority/"review/0.0.8").exists(): fail("canonical 0.0.8 release/review must remain absent")
 for relative,expected in IMMUTABLE_GIT_TREES.items():
  actual=subprocess.check_output(["git","rev-parse",f"HEAD:{relative}"],cwd=authority,text=True).strip()
  if actual!=expected: fail(f"immutable predecessor Git tree drift {relative}: {actual}")
 release=candidate/"release/raw"/RELEASE
 if not release.is_dir(): fail("candidate release absent")
 results=[]
 for role,spec in EXPECTED.items():
  variant=spec[0]; glb=release/role/f"{variant}.glb"; results.append(validate_cue(glb,role))
  candidate_manifest=candidate/"manifests"/role/f"{variant}.v1.json"; authority_manifest=authority/"manifests"/role/f"{variant}.v1.json"; manifest=load(candidate_manifest); staged=load(authority_manifest)
  candidate_source=candidate/"source"/role/variant/f"{variant}.blend"; staged_source=authority/"source"/role/variant/f"{variant}.blend"
  for document,source in ((manifest,candidate_source),(staged,staged_source)):
   files=document["files"]
   if files["source_sha256"]!=sha(source) or files["source_bytes"]!=source.stat().st_size or files["release_sha256"]!=sha(glb) or files["release_bytes"]!=glb.stat().st_size: fail(f"{role}: manifest hash/byte provenance")
  comparable=lambda document:{**document,"files":{key:value for key,value in document["files"].items() if key not in ("source_sha256","source_bytes")}}
  if comparable(manifest)!=comparable(staged): fail(f"{role}: staged/generated manifest semantic drift")
  if manifest["geometry"]["triangle_count"]!=spec[4] or manifest["geometry"]["triangle_budget"]!=spec[5] or manifest["coordinates"]["visible_face"]!="both +Z/-Z" or manifest["dependencies"]!=[] or manifest["provenance"]["external_assets"]!=[] or manifest["provenance"]["network"] is not False: fail(f"{role}: manifest geometry/face/provenance contract")
 for role,variant in UNCHANGED:
  current=release/role/f"{variant}.glb"; predecessor=authority/"release/raw/0.0.7"/role/f"{variant}.glb"
  if current.read_bytes()!=predecessor.read_bytes(): fail(f"{role}: selected GLB changed")
  current_source=candidate/"source"/role/variant/f"{variant}.blend"; predecessor_source=authority/"source"/role/variant/f"{variant}.blend"
  if current_source.read_bytes()!=predecessor_source.read_bytes(): fail(f"{role}: selected editable source changed")
 setdoc=load(release/"sets/default-v1.json")
 if setdoc!=load(authority/"sets/default-v1.json"): fail("candidate set differs from staged set")
 if setdoc["roles"]!={role:spec[0] for role,spec in EXPECTED.items()}|{role:variant for role,variant in UNCHANGED}: fail("candidate set mapping")
 return results

def main():
 parser=argparse.ArgumentParser(); parser.add_argument("--authority-root",default="."); parser.add_argument("--candidate-root",required=True); args=parser.parse_args()
 results=validate(Path(args.authority_root).resolve(),Path(args.candidate_root).resolve())
 print(json.dumps({"release":RELEASE,"cues":results},sort_keys=True))
 print("ROUNDED_VALIDATE_OK release=0.0.8 cues=3 unchanged=4")
if __name__=="__main__": main()
