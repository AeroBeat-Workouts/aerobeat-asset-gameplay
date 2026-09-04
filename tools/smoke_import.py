#!/usr/bin/env python3
"""Clean-Blender dependency-free GLB smoke importer for canonical package files."""
import json, math, struct, sys
import bpy
from mathutils import Vector

path,canonical=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
data=open(path,"rb").read(); magic,version,total=struct.unpack_from("<4sII",data,0)
if magic!=b"glTF" or version!=2 or total!=len(data): raise RuntimeError("invalid GLB")
off=12; chunks={}
while off<len(data):
    n,t=struct.unpack_from("<I4s",data,off); off+=8; chunks[t]=data[off:off+n]; off+=n
doc=json.loads(chunks[b"JSON"].decode("utf-8").rstrip(" \x00")); binary=chunks[b"BIN\x00"]
if len(doc.get("meshes",[]))!=1 or doc["nodes"][0].get("name")!=canonical: raise RuntimeError("canonical identity mismatch")
def accessor(index):
    a=doc["accessors"][index]; v=doc["bufferViews"][a["bufferView"]]; start=v.get("byteOffset",0)+a.get("byteOffset",0)
    fmts={5123:("H",2),5125:("I",4),5126:("f",4)}; code,size=fmts[a["componentType"]]; width={"SCALAR":1,"VEC3":3}[a["type"]]
    stride=v.get("byteStride",size*width); result=[]
    for i in range(a["count"]): result.append(struct.unpack_from("<"+code*width,binary,start+i*stride))
    return result
primitives=doc["meshes"][0]["primitives"]; attributes=primitives[0]["attributes"]
positions=accessor(attributes["POSITION"]); normals=accessor(attributes["NORMAL"]) if "NORMAL" in attributes else None
faces=[]
for primitive in primitives:
    if primitive["attributes"]!=attributes: raise RuntimeError("primitive attribute mismatch")
    idx=[x[0] for x in accessor(primitive["indices"])]
    faces.extend(tuple(idx[i:i+3]) for i in range(0,len(idx),3))
if canonical=="athlete-marker/sphere-v1":
    if normals is None or len(normals)!=len(positions) or len(faces)!=168: raise RuntimeError("marker exact POSITION/NORMAL/face count failed")
    winding=[]; agreement=[]
    for tri in faces:
        a,b,c=(Vector(positions[i]) for i in tri); geometric=(b-a).cross(c-a); centroid=(a+b+c)/3
        winding.append(geometric.dot(centroid)); unit=geometric.normalized()
        agreement.extend(unit.dot(Vector(normals[i])) for i in tri)
    if min(winding)<=1e-8 or min(agreement)<=.9: raise RuntimeError(f"marker outward winding/NORMAL agreement failed: winding={min(winding)} agreement={min(agreement)}")
mesh=bpy.data.meshes.new(canonical+"/smoke-mesh"); mesh.from_pydata(positions,[],faces); mesh.validate(verbose=True); mesh.update()
for material_spec in doc.get("materials",[]):
    material=bpy.data.materials.new(material_spec["name"]); material.use_backface_culling=material_spec.get("doubleSided",False) is False; mesh.materials.append(material)
for polygon in mesh.polygons: polygon.use_smooth=normals is not None
if normals is not None: mesh.normals_split_custom_set_from_vertices(normals)
obj=bpy.data.objects.new(canonical,mesh); bpy.context.collection.objects.link(obj)
if len(mesh.polygons)!=len(faces) or not faces: raise RuntimeError("mesh import validation failed")
if any(abs(x)>1e-7 for x in obj.location) or any(abs(x)>1e-7 for x in obj.rotation_euler) or any(abs(x-1)>1e-7 for x in obj.scale): raise RuntimeError("non-identity transform")
if canonical=="athlete-marker/sphere-v1" and (len(mesh.materials)!=3 or any(not material.use_backface_culling for material in mesh.materials)):
    raise RuntimeError("marker reconstructed material backface culling is disabled")
print(f"SMOKE_OK kind=glb identity={canonical}")
