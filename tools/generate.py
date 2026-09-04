#!/usr/bin/env python3
"""Deterministically author AeroBeat gameplay assets with Blender 4.0.2.

Run only through Blender:
  blender --background --factory-startup --python tools/generate.py -- --output-root .
No network, imported content, fonts, images, or textures are used.
"""
from __future__ import annotations
import argparse, hashlib, json, math, struct, sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

SUPPORTED_RELEASE = "0.0.7"
PREDECESSOR_RELEASE = "0.0.6"
VERSION = None
BLENDER = "4.0.2"
GENERATOR = "aerobeat-gameplay-generator-v6"
CHANGED_SOURCE_ROLES = {"athlete-marker"}

ASSETS = [
    dict(role="directional-arrow", variant="outline-v1", dimensions=[0.78,0.78,0.18], pivot=[0,0,0], budget=420, bound=[[-0.42,-0.42,-0.11],[0.42,0.42,0.11]], reuse="one mesh for Flow and Boxing; rotate only about local Z"),
    dict(role="any-note", variant="circle-v1", dimensions=[0.70,0.70,0.18], pivot=[0,0,0], budget=320, bound=[[-0.38,-0.38,-0.11],[0.38,0.38,0.11]], reuse="one directionless mesh across applicable modes"),
    dict(role="guard", variant="shield-v1", dimensions=[0.72,0.82,0.16], pivot=[0,0,0.07], budget=520, bound=[[-0.39,-0.44,-0.10],[0.39,0.44,0.10]], reuse="exactly one canonical shield; instance twice simultaneously without mirroring or material/scale variation"),
    dict(role="bomb", variant="urchin-v1", dimensions=[0.78,0.78,0.78], pivot=[0,0,0], budget=900, bound=[[-0.42,-0.42,-0.42],[0.42,0.42,0.42]], reuse="one bomb mesh for every bomb event"),
    dict(role="wall", variant="red-glass-v1", dimensions=[0.94,0.94,1.00], pivot=[0,0,0], budget=144, bound=[[-0.47,-0.47,-0.50],[0.47,0.47,0.50]], reuse="one canonical 0.94 x 0.94 cell footprint at unit X/Y scale; scale only Z to authoritative L=max(0.08,speedWorldUnitsPerMs*(endTimestampMs-centerTimestampMs)); adjacent 1.0-pitch cells retain a 0.06 gap"),
    dict(role="track", variant="blue-glass-v1", dimensions=[4.20,0.06,24.00], pivot=[0,0.03,0], budget=160, bound=[[-2.14,-0.04,-12.04],[2.14,0.08,12.04]], reuse="one canonical segment; extend by deterministic segment reuse, never stretch lane-line width"),
    dict(role="athlete-marker", variant="sphere-v1", dimensions=[0.18,0.18,0.18], pivot=[0,0,0], budget=192, bound=[[-0.10,-0.10,-0.10],[0.10,0.10,0.10]], reuse="same full 3D sphere for nose and both wrists; truthful world positions and normal depth"),
]

SCREEN_DIRECTIONS = {
    "up": 0, "up-right": -45, "right": -90, "down-right": -135,
    "down": 180, "down-left": 135, "left": 90, "up-left": 45,
}

COLORS = {
    "white": ((0.95,0.98,1.0,1),0.30,0.45,"OPAQUE"),
    "charcoal": ((0.035,0.045,0.06,1),0.43,0.0,"OPAQUE"),
    "cyan": ((0.03,0.55,0.95,1),0.38,0.05,"OPAQUE"),
    "green": ((0.04,0.60,0.28,1),0.38,0.03,"OPAQUE"),
    "black": ((0.012,0.014,0.018,1),0.46,0.0,"OPAQUE"),
    "red_emissive": ((0.9,0.015,0.02,1),0.34,4.0,"OPAQUE"),
    "red_glass": ((0.65,0.01,0.018,0.24),0.20,0.25,"BLEND"),
    "red_edge": ((0.95,0.01,0.015,0.82),0.28,5.0,"BLEND"),
    # Neutral opaque core intentionally accepts red/yellow/green runtime multiplication
    # without changing the structural white outline or charcoal separator.
    "tint_base": ((0.92,0.92,0.92,1),0.34,0.08,"OPAQUE"),
    # 0.52 is 2.6x the predecessor's 0.20 alpha: materially stronger against the
    # bright ice photosphere while retaining a recognizably translucent blue surface.
    "blue_glass": ((0.10,0.58,0.92,0.52),0.16,0.20,"BLEND"),
    "cyan_edge": ((0.05,0.80,1.0,1),0.25,3.0,"OPAQUE"),
    "panel": ((0.10,0.14,0.20,1),0.45,0.18,"OPAQUE"),
    "dark_ice": ((0.015,0.025,0.055,1),0.60,0.05,"OPAQUE"),
    "bright_ice": ((0.72,0.88,0.96,1),0.52,0.12,"OPAQUE"),
    "blue_ice": ((0.03,0.24,0.52,1),0.48,0.18,"OPAQUE"),
}

def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)+"\n"
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def write_json(path,obj): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(canonical(obj),encoding="utf-8")

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def material(name):
    rgba,rough,emit,blend=COLORS[name]
    m=bpy.data.materials.new("mat/"+name)
    m.diffuse_color=rgba; m.use_nodes=True; m.use_backface_culling=True
    if blend=="BLEND": m.blend_method="BLEND"; m.show_transparent_back=False
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=rgba
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=0.0
    bs.inputs["Alpha"].default_value=rgba[3]
    bs.inputs["Emission Color"].default_value=(rgba[0],rgba[1],rgba[2],1)
    bs.inputs["Emission Strength"].default_value=emit
    return m

def add_comp(verts,faces,mats, cv,cf,mi):
    o=len(verts); verts.extend(cv); faces.extend(tuple(o+i for i in f) for f in cf); mats.extend([mi]*len(cf))

def polygon_area(poly): return sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))*.5

def triangulate(poly):
    """Deterministic ear clipping for a counter-clockwise simple loop."""
    if polygon_area(poly)<=0: raise ValueError("triangulation requires counter-clockwise loop")
    indices=list(range(len(poly))); result=[]
    def cross(a,b,c): return (poly[b][0]-poly[a][0])*(poly[c][1]-poly[a][1])-(poly[b][1]-poly[a][1])*(poly[c][0]-poly[a][0])
    def inside(p,a,b,c):
        q=poly[p]; aa=poly[a]; bb=poly[b]; cc=poly[c]
        signs=((bb[0]-aa[0])*(q[1]-aa[1])-(bb[1]-aa[1])*(q[0]-aa[0]),(cc[0]-bb[0])*(q[1]-bb[1])-(cc[1]-bb[1])*(q[0]-bb[0]),(aa[0]-cc[0])*(q[1]-cc[1])-(aa[1]-cc[1])*(q[0]-cc[0]))
        return min(signs)>=-1e-10
    while len(indices)>3:
        for k,b in enumerate(indices):
            a=indices[k-1]; c=indices[(k+1)%len(indices)]
            if cross(a,b,c)>1e-10 and not any(inside(p,a,b,c) for p in indices if p not in (a,b,c)):
                result.append((a,b,c)); indices.pop(k); break
        else: raise ValueError("polygon cannot be triangulated")
    result.append(tuple(indices)); return result

def extrude(poly,z0,z1):
    n=len(poly); v=[(x,y,z0) for x,y in poly]+[(x,y,z1) for x,y in poly]; f=[]
    for a,b,c in triangulate(poly): f.append((a,c,b)); f.append((n+a,n+b,n+c))
    for i in range(n): j=(i+1)%n; f += [(i,j,n+j),(i,n+j,n+i)]
    return v,f

def rear_and_sides(poly,z0,z1):
    """Outer depth shell without a front cap; the front is explicit ring geometry."""
    n=len(poly); v=[(x,y,z0) for x,y in poly]+[(x,y,z1) for x,y in poly]; f=[]
    for a,b,c in triangulate(poly): f.append((n+a,n+b,n+c))
    for i in range(n):
        j=(i+1)%n; f += [(i,j,n+j),(i,n+j,n+i)]
    return v,f

def ring(outer,inner,z):
    """Continuous front-facing annulus between corresponding silhouette loops."""
    if len(outer)!=len(inner): raise ValueError("ring loops must correspond")
    n=len(outer); v=[(x,y,z) for x,y in outer]+[(x,y,z) for x,y in inner]; f=[]
    for i in range(n):
        j=(i+1)%n; f += [(i,n+j,j),(i,n+i,n+j)]
    return v,f

def rimmed_plate(poly,z0,z1,separator_scale,inset_scale,inset_material):
    """Legacy single-face plate retained byte-identically for circle and shield."""
    outer=list(poly)
    if polygon_area(outer)<0: outer.reverse()
    separator=[(x*separator_scale,y*separator_scale) for x,y in outer]
    inset=[(x*inset_scale,y*inset_scale) for x,y in outer]
    parts=[]
    parts.append((*rear_and_sides(outer,z0,z1),"charcoal"))
    parts.append((*ring(outer,separator,z0),"white"))
    parts.append((*ring(separator,inset,z0),"charcoal"))
    parts.append((*extrude(inset,z0,z1),inset_material))
    return parts

def closed_frame(outer,inner,z0,z1):
    """Closed annular extrusion with no cap overlap and outward winding."""
    if len(outer)!=len(inner): raise ValueError("frame loops must correspond")
    n=len(outer); v=[(x,y,z0) for x,y in outer]+[(x,y,z1) for x,y in outer]+[(x,y,z0) for x,y in inner]+[(x,y,z1) for x,y in inner]; f=[]
    for i in range(n):
        j=(i+1)%n
        f += [(i,j,n+j),(i,n+j,n+i)]                         # outer wall
        f += [(2*n+i,3*n+j,2*n+j),(2*n+i,3*n+i,3*n+j)]       # inner wall
        f += [(i,2*n+j,j),(i,2*n+i,2*n+j)]                   # -Z annulus
        f += [(n+i,n+j,3*n+j),(n+i,3*n+j,3*n+i)]             # +Z annulus
    return v,f

def bidirectional_rimmed_plate(poly,separator,inset,z0,z1,inset_material):
    """Three closed, depth-separated opaque solids styled identically on ±Z."""
    outer=list(poly); separator=list(separator); inset=list(inset)
    if polygon_area(outer)<0: outer.reverse()
    if polygon_area(separator)<0: separator.reverse()
    if polygon_area(inset)<0: inset.reverse()
    epsilon=.002
    return [
        (*closed_frame(outer,separator,z0,z1),"white"),
        (*closed_frame(separator,inset,z0+epsilon,z1-epsilon),"charcoal"),
        (*extrude(inset,z0+2*epsilon,z1-2*epsilon),inset_material),
    ]

def box(x0,x1,y0,y1,z0,z1):
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return v,f

def cylinder(radius,z0,z1,n=24):
    p=[(radius*math.cos(2*math.pi*i/n),radius*math.sin(2*math.pi*i/n)) for i in range(n)]
    return extrude(p,z0,z1)

def uv_sphere(r,n=12,rings=7):
    v=[(0,r,0)]
    for j in range(1,rings+1):
        th=math.pi*j/(rings+1); y=r*math.cos(th); rr=r*math.sin(th)
        for i in range(n):
            a=2*math.pi*i/n; v.append((rr*math.cos(a),y,rr*math.sin(a)))
    v.append((0,-r,0)); bot=len(v)-1; f=[]
    for i in range(n): f.append((0,1+i,1+(i+1)%n))
    for j in range(rings-1):
        a=1+j*n; b=a+n
        for i in range(n): ni=(i+1)%n; f += [(a+i,b+i,b+ni),(a+i,b+ni,a+ni)]
    a=1+(rings-1)*n
    for i in range(n): f.append((a+i,bot,a+(i+1)%n))
    return v,f

def cone_between(base,tip,radius,n=8):
    d=Vector(tip)-Vector(base); w=d.normalized(); ref=Vector((0,1,0)) if abs(w.y)<0.9 else Vector((1,0,0)); u=w.cross(ref).normalized(); q=w.cross(u).normalized()
    v=[]
    for i in range(n):
        a=2*math.pi*i/n; p=Vector(base)+radius*(math.cos(a)*u+math.sin(a)*q); v.append(tuple(p))
    v.append(tuple(tip)); f=[]
    for i in range(n): f.append((i,(i+1)%n,n))
    for i in range(1,n-1): f.append((0,i+1,i))
    return v,f

def torus(major,minor,nmajor=16,nminor=4):
    v=[]
    for i in range(nmajor):
        a=2*math.pi*i/nmajor
        for j in range(nminor):
            b=2*math.pi*j/nminor; rr=major+minor*math.cos(b); v.append((rr*math.cos(a),minor*math.sin(b),rr*math.sin(a)))
    f=[]
    for i in range(nmajor):
        for j in range(nminor):
            a=i*nminor+j; b=((i+1)%nmajor)*nminor+j; c=((i+1)%nmajor)*nminor+(j+1)%nminor; d=i*nminor+(j+1)%nminor
            f += [(a,b,c),(a,c,d)]
    return v,f

def build_geometry(role):
    v=[]; f=[]; mi=[]; names=[]
    def matn(n):
        if n not in names: names.append(n)
        return names.index(n)
    if role=="directional-arrow":
        p=[(-.16,-.39),(.16,-.39),(.16,.05),(.39,.05),(0,.39),(-.39,.05),(-.16,.05)]
        separator=[(-.135,-.36),(.135,-.36),(.135,.08),(.31,.08),(0,.335),(-.31,.08),(-.135,.08)]
        inset=[(-.105,-.32),(.105,-.32),(.105,.115),(.235,.115),(0,.275),(-.235,.115),(-.105,.115)]
        for cv,cf,m in bidirectional_rimmed_plate(p,separator,inset,-.09,.09,"tint_base"):
            add_comp(v,f,mi,cv,cf,matn(m))
    elif role=="any-note":
        p=[(.35*math.cos(2*math.pi*i/24),.35*math.sin(2*math.pi*i/24)) for i in range(24)]
        for cv,cf,m in rimmed_plate(p,-.09,.09,.87,.73,"cyan"):
            add_comp(v,f,mi,cv,cf,matn(m))
    elif role=="guard":
        p=[(-.36,.30),(-.25,.41),(.25,.41),(.36,.30),(.30,-.20),(0,-.41),(-.30,-.20)]
        # Geometry center is z=-0.07 because origin is the specified rear-grip pivot.
        for cv,cf,m in rimmed_plate(p,-.15,.01,.88,.73,"green"):
            add_comp(v,f,mi,cv,cf,matn(m))
    elif role=="bomb":
        cv,cf=uv_sphere(.22); add_comp(v,f,mi,cv,cf,matn("black"))
        dirs=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
        golden=math.pi*(3-math.sqrt(5))
        for i in range(10):
            y=1-2*(i+.5)/10; rr=math.sqrt(1-y*y); a=i*golden+.37; dirs.append((rr*math.cos(a),y,rr*math.sin(a)))
        for d in dirs:
            q=Vector(d).normalized(); cv,cf=cone_between(q*.19,q*.39,.052,8); add_comp(v,f,mi,cv,cf,matn("charcoal"))
        cv,cf=torus(.225,.012); add_comp(v,f,mi,cv,cf,matn("red_emissive"))
    elif role=="wall":
        half=.47
        cv,cf=box(-half,half,-half,half,-.5,.5); add_comp(v,f,mi,cv,cf,matn("red_glass"))
        # Twelve square-prism edges: exactly 96 edge triangles plus 12 body triangles.
        t=.018
        edges=[]
        # Cage prisms remain inside the exact 0.94 x 0.94 x 1.00 source extent.
        for y in (-half+t,half-t):
            for z in (-.5+t,.5-t): edges.append((-half,half,y,y,z,z,"x"))
        for x in (-half+t,half-t):
            for z in (-.5+t,.5-t): edges.append((x,x,-half,half,z,z,"y"))
        for x in (-half+t,half-t):
            for y in (-half+t,half-t): edges.append((x,x,y,y,-.5,.5,"z"))
        for x0,x1,y0,y1,z0,z1,axis in edges:
            if axis=="x": cv,cf=box(x0,x1,y0-t,y0+t,z0-t,z0+t)
            elif axis=="y": cv,cf=box(x0-t,x0+t,y0,y1,z0-t,z0+t)
            else: cv,cf=box(x0-t,x0+t,y0-t,y0+t,z0,z1)
            # retain side faces only (8 triangles) for an open analytic cage
            add_comp(v,f,mi,cv,cf[4:],matn("red_edge"))
    elif role=="track":
        # Origin is the specified top-surface pivot; geometry center is Y=-0.03.
        cv,cf=box(-2.1,2.1,-.06,0,-12,12); add_comp(v,f,mi,cv,cf,matn("blue_glass"))
        for x in (-2.088,-.7,.7,2.088):
            cv,cf=box(x-.012,x+.012,-.006,0,-12,12); add_comp(v,f,mi,cv,cf,matn("cyan_edge"))
    elif role=="athlete-marker":
        # One canonical 0.18-unit sphere. Its single closed surface is partitioned,
        # never layered: tintable panels are bounded by white structure and a dark
        # separator grid around all three coordinate planes. Every camera hemisphere
        # therefore sees all three materials without coplanar or intersecting shells.
        cv,cf=uv_sphere(.09)
        # uv_sphere's legacy order is inward for this coordinate convention. Reverse
        # only the marker successor so glTF CCW front faces point outward while all
        # immutable non-marker assets retain their exact predecessor bytes.
        cf=[(a,c,b) for a,b,c in cf]
        for face in cf:
            center=[sum(cv[i][axis] for i in face)/(3*.09) for axis in range(3)]
            plane_distance=min(abs(value) for value in center)
            material_name="charcoal" if plane_distance<=.08 else ("white" if plane_distance<=.22 else "tint_base")
            mi.append(matn(material_name))
        v.extend(cv); f.extend(cf)
    return v,f,mi,names

def make_asset(spec):
    v,f,mi,names=build_geometry(spec["role"])
    mesh=bpy.data.meshes.new(spec["role"]+"/"+spec["variant"]+"/mesh")
    mesh.from_pydata(v,[],f); mesh.materials.clear()
    for n in names: mesh.materials.append(material(n))
    for poly,idx in zip(mesh.polygons,mi): poly.material_index=idx
    mesh.update()
    obj=bpy.data.objects.new(spec["role"]+"/"+spec["variant"],mesh)
    bpy.context.collection.objects.link(obj); obj.rotation_euler=(0,0,0); obj.scale=(1,1,1); obj.location=(0,0,0)
    for p in mesh.polygons: p.use_smooth=spec["role"]=="athlete-marker"
    return obj

def measured(obj):
    vs=[Vector(obj.data.vertices[i].co) for i in range(len(obj.data.vertices))]
    lo=[min(p[k] for p in vs) for k in range(3)]; hi=[max(p[k] for p in vs) for k in range(3)]
    return [[round(x,6) for x in lo],[round(x,6) for x in hi]],sum(len(p.vertices)-2 for p in obj.data.polygons)

def write_glb(path,obj,material_names):
    """Write a minimal deterministic glTF 2.0 binary without exporter dependencies."""
    positions=[tuple(v.co) for v in obj.data.vertices]
    binary=bytearray().join(struct.pack("<fff",*p) for p in positions)
    views=[{"buffer":0,"byteOffset":0,"byteLength":len(binary),"target":34962}]
    accessors=[{"bufferView":0,"componentType":5126,"count":len(positions),"type":"VEC3","min":[min(p[i] for p in positions) for i in range(3)],"max":[max(p[i] for p in positions) for i in range(3)]}]
    attributes={"POSITION":0}
    if obj.name.startswith("athlete-marker/"):
        normals=[]
        for position in positions:
            length=math.sqrt(sum(value*value for value in position))
            normals.append(tuple(value/length for value in position))
        while len(binary)%4: binary.append(0)
        offset=len(binary); binary.extend(b"".join(struct.pack("<fff",*normal) for normal in normals))
        views.append({"buffer":0,"byteOffset":offset,"byteLength":len(binary)-offset,"target":34962})
        accessors.append({"bufferView":len(views)-1,"componentType":5126,"count":len(normals),"type":"VEC3","min":[min(n[i] for n in normals) for i in range(3)],"max":[max(n[i] for n in normals) for i in range(3)]})
        attributes["NORMAL"]=len(accessors)-1
    primitives=[]
    for mat_index in range(len(material_names)):
        indices=[]
        for poly in obj.data.polygons:
            if poly.material_index==mat_index:
                if len(poly.vertices)!=3: raise RuntimeError("generator requires triangulated faces")
                indices.extend(poly.vertices)
        while len(binary)%4: binary.append(0)
        off=len(binary); component=5123 if len(positions)<65536 else 5125; fmt="<H" if component==5123 else "<I"
        binary.extend(b"".join(struct.pack(fmt,i) for i in indices))
        views.append({"buffer":0,"byteOffset":off,"byteLength":len(binary)-off,"target":34963})
        accessors.append({"bufferView":len(views)-1,"componentType":component,"count":len(indices),"type":"SCALAR","min":[min(indices)],"max":[max(indices)]})
        primitives.append({"attributes":dict(attributes),"indices":len(accessors)-1,"material":mat_index,"mode":4})
    materials=[]
    role=obj.name.split("/",1)[0]
    for name in material_names:
        rgba,rough,emit,blend=COLORS[name]
        m={"name":"mat/"+name,"pbrMetallicRoughness":{"baseColorFactor":list(rgba),"metallicFactor":0.0,"roughnessFactor":rough},"doubleSided":False}
        if emit: m["emissiveFactor"]=[rgba[0]*min(emit,1),rgba[1]*min(emit,1),rgba[2]*min(emit,1)]
        if blend=="BLEND": m["alphaMode"]="BLEND"
        if role=="directional-arrow":
            m["alphaMode"]="OPAQUE"
            m["extras"]={"aerobeat":{"blend":"opaque","cull":"back","depthTest":True,"depthWrite":True,"runtimeTintable":name=="tint_base"}}
        elif role=="track":
            m["extras"]={"aerobeat":{"blend":"alpha" if blend=="BLEND" else "opaque","cull":"back","depthTest":True,"depthWrite":False if blend=="BLEND" else True,"order":"after-grid-before-wall"}}
        elif role=="wall":
            m["extras"]={"aerobeat":{"blend":"alpha","cull":"back","depthTest":True,"depthWrite":False,"order":"after-track","unitCellFootprint":[0.94,0.94],"xyScaleAuthoritative":[1,1],"zScaleAuthoritative":True}}
        elif role=="athlete-marker":
            m["alphaMode"]="OPAQUE"
            m["extras"]={"aerobeat":{"blend":"opaque","cull":"back","depthTest":True,"depthWrite":True,"runtimeTintable":name=="tint_base","structural":name in ("white","charcoal")}}
        materials.append(m)
    doc={"asset":{"generator":GENERATOR,"version":"2.0"},"scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0,"name":obj.name}],"meshes":[{"name":obj.data.name,"primitives":primitives}],"materials":materials,"buffers":[{"byteLength":len(binary)}],"bufferViews":views,"accessors":accessors}
    js=json.dumps(doc,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    while len(js)%4: js+=b" "
    while len(binary)%4: binary.append(0)
    payload=struct.pack("<4sII",b"glTF",2,12+8+len(js)+8+len(binary))+struct.pack("<I4s",len(js),b"JSON")+js+struct.pack("<I4s",len(binary),b"BIN\x00")+bytes(binary)
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(payload)

def export_asset(root,spec):
    reset(); obj=make_asset(spec); role=spec["role"]; variant=spec["variant"]
    src=root/"source"/role/variant/(variant+".blend"); src.parent.mkdir(parents=True,exist_ok=True)
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    # Preserve six unchanged editable snapshots byte-for-byte in the canonical
    # checkout. Clean temporary builds still receive a complete seven-source shape.
    if not src.exists() or role in CHANGED_SOURCE_ROLES:
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(src),compress=False,check_existing=False)
    out=root/"release"/"raw"/VERSION/role/(variant+".glb")
    names=[m.name.removeprefix("mat/") for m in obj.data.materials]
    if role in CHANGED_SOURCE_ROLES:
        write_glb(out,obj,names)
    else:
        predecessor=root/"release"/"raw"/PREDECESSOR_RELEASE/role/(variant+".glb")
        out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(predecessor.read_bytes())
    aabb,tris=measured(obj)
    return src,out,aabb,tris,[m.name for m in obj.data.materials]

def camera_at(location,target,lens=52):
    bpy.ops.object.camera_add(location=location); c=bpy.context.object; c.name="review/camera"; c.data.lens=lens
    c.rotation_euler=(Vector(target)-c.location).to_track_quat("-Z","Y").to_euler(); bpy.context.scene.camera=c
    return c

def setup_render(world=(.025,.032,.05,1)):
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=1600; s.render.resolution_y=900; s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGB"; s.render.film_transparent=False
    s.render.image_settings.color_depth="8"; s.render.image_settings.compression=15
    if s.world is None: s.world=bpy.data.worlds.new("review/world")
    s.world.color=world[:3]; s.view_settings.look="AgX - Medium High Contrast"
    bpy.ops.object.light_add(type="AREA",location=(4,6,-4)); bpy.context.object.data.energy=1500; bpy.context.object.data.shape="DISK"; bpy.context.object.data.size=5
    bpy.ops.object.light_add(type="AREA",location=(-4,2,3)); bpy.context.object.data.energy=950; bpy.context.object.data.size=4

def render(path):
    path.parent.mkdir(parents=True,exist_ok=True); bpy.context.scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)

def add_review_asset(spec,loc=(0,0,0),scale=(1,1,1),rotation=(0,0,0),instance=None):
    o=make_asset(spec); o.location=loc; o.scale=scale; o.rotation_euler=rotation
    if instance: o.name="review/"+instance
    return o

def add_label(text,loc,size=.24,align="CENTER"):
    bpy.ops.object.text_add(location=loc); o=bpy.context.object; o.name="review/label/"+text
    o.data.body=text; o.data.align_x=align; o.data.align_y="CENTER"; o.data.size=size; o.data.extrude=.002; o.rotation_euler[1]=math.pi
    o.data.materials.append(material("white")); return o

def add_panel(cx,cy,w,h,z=.35,material_name="panel"):
    cv,cf=box(cx-w/2,cx+w/2,cy-h/2,cy+h/2,z,z+.015)
    mesh=bpy.data.meshes.new("review/panel/mesh"); mesh.from_pydata(cv,[],cf); mesh.materials.append(material(material_name)); mesh.update()
    o=bpy.data.objects.new("review/panel",mesh); bpy.context.collection.objects.link(o); return o

def world_corners(obj):
    bpy.context.view_layer.update()
    return [obj.matrix_world @ Vector(c) for c in obj.bound_box]

def projected_bbox(camera,obj):
    points=[world_to_camera_view(bpy.context.scene,camera,p) for p in world_corners(obj)]
    return [round(min(p.x for p in points),6),round(min(p.y for p in points),6),round(max(p.x for p in points),6),round(max(p.y for p in points),6)]

def fit_camera(objects,direction=(.55,.35,-1),margin=.08,lens=55,orthographic=False):
    points=[p for o in objects for p in world_corners(o)]
    lo=Vector(tuple(min(p[i] for p in points) for i in range(3))); hi=Vector(tuple(max(p[i] for p in points) for i in range(3))); center=(lo+hi)*.5
    radius=max((p-center).length for p in points); direction=Vector(direction).normalized()
    c=camera_at(center+direction*max(2.0,radius*2.2),center,lens)
    if orthographic: c.data.type="ORTHO"; c.data.ortho_scale=max(2.0,(hi.y-lo.y)*1.25)
    for _ in range(160):
        boxes=[projected_bbox(c,o) for o in objects]
        if all(b[0]>=margin and b[1]>=margin and b[2]<=1-margin and b[3]<=1-margin for b in boxes): return c,boxes
        if orthographic: c.data.ortho_scale*=1.04
        else: c.location=center+(c.location-center)*1.04
    raise RuntimeError("calculated review camera could not contain all object bounds")

def layout_entry(camera,role,variant,obj,instance,release=None):
    entry={"role":role,"variant":variant,"instance":instance,"projected_bbox":projected_bbox(camera,obj)}
    if release is not None: entry["release"]=release
    return entry

def import_review_mesh(path,name,require_outward=False):
    """Reconstruct this repository's minimal GLB with embedded NORMAL/cull truth."""
    data=path.read_bytes(); magic,version,total=struct.unpack_from("<4sII",data,0)
    if magic!=b"glTF" or version!=2 or total!=len(data): raise RuntimeError(f"invalid review GLB {path}")
    json_size,json_type=struct.unpack_from("<I4s",data,12)
    if json_type!=b"JSON": raise RuntimeError(f"missing JSON chunk in {path}")
    doc=json.loads(data[20:20+json_size].decode("utf-8").rstrip(" \x00"))
    bin_header=20+json_size; bin_size,bin_type=struct.unpack_from("<I4s",data,bin_header)
    if bin_type!=b"BIN\x00": raise RuntimeError(f"missing BIN chunk in {path}")
    binary=data[bin_header+8:bin_header+8+bin_size]
    def accessor(index):
        a=doc["accessors"][index]; view=doc["bufferViews"][a["bufferView"]]
        offset=view.get("byteOffset",0)+a.get("byteOffset",0); count=a["count"]
        if a["type"]=="VEC3" and a["componentType"]==5126:
            return [struct.unpack_from("<fff",binary,offset+i*12) for i in range(count)]
        formats={5123:("<H",2),5125:("<I",4)}
        fmt,size=formats[a["componentType"]]
        return [struct.unpack_from(fmt,binary,offset+i*size)[0] for i in range(count)]
    primitives=doc["meshes"][0]["primitives"]; attributes=primitives[0]["attributes"]
    positions=accessor(attributes["POSITION"]); normals=accessor(attributes["NORMAL"]) if "NORMAL" in attributes else None
    faces=[]; material_indices=[]
    for primitive in primitives:
        if primitive["attributes"]!=attributes: raise RuntimeError(f"review primitive attribute mismatch in {path}")
        indices=accessor(primitive["indices"])
        faces.extend(tuple(indices[i:i+3]) for i in range(0,len(indices),3))
        material_indices.extend([primitive["material"]]*(len(indices)//3))
    if require_outward:
        if normals is None or len(normals)!=len(positions): raise RuntimeError(f"review marker lacks embedded NORMAL in {path}")
        for tri in faces:
            a,b,c=(Vector(positions[i]) for i in tri); geometric=(b-a).cross(c-a); centroid=(a+b+c)/3
            if geometric.dot(centroid)<=1e-8: raise RuntimeError(f"review marker is not outward CCW in {path}")
            unit=geometric.normalized()
            if any(unit.dot(Vector(normals[i]))<=.9 for i in tri): raise RuntimeError(f"review marker geometric/NORMAL disagreement in {path}")
    mesh=bpy.data.meshes.new("review/"+name+"/mesh"); mesh.from_pydata(positions,[],faces)
    for spec in doc.get("materials",[]):
        pbr=spec["pbrMetallicRoughness"]; rgba=tuple(pbr["baseColorFactor"]); m=bpy.data.materials.new(spec["name"])
        m.diffuse_color=rgba; m.use_nodes=True; m.use_backface_culling=spec.get("doubleSided",False) is False
        if spec.get("alphaMode","OPAQUE")=="BLEND": m.blend_method="BLEND"; m.show_transparent_back=False
        bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=rgba; bs.inputs["Alpha"].default_value=rgba[3]; bs.inputs["Roughness"].default_value=pbr.get("roughnessFactor",.5); bs.inputs["Metallic"].default_value=pbr.get("metallicFactor",0)
        emissive=spec.get("emissiveFactor")
        if emissive: bs.inputs["Emission Color"].default_value=(*emissive,1); bs.inputs["Emission Strength"].default_value=1
        mesh.materials.append(m)
    for polygon,index in zip(mesh.polygons,material_indices): polygon.material_index=index; polygon.use_smooth=normals is not None
    mesh.update()
    if normals is not None: mesh.normals_split_custom_set_from_vertices(normals)
    if any(not material.use_backface_culling for material in mesh.materials): raise RuntimeError(f"review material culling disabled in {path}")
    obj=bpy.data.objects.new("review/"+name,mesh); bpy.context.collection.objects.link(obj)
    return obj

def review(root):
    rd=root/"review"/VERSION; images=[]; layouts={}
    # Intentional labeled 4x2 neutral inspection grid; every asset is fully in frame.
    reset(); setup_render(); assets=[]; panels=[]; labels=[]
    cells=[(-4.5,1.6),(-1.5,1.6),(1.5,1.6),(4.5,1.6),(-3,-1.65),(0,-1.65),(3,-1.65)]
    roles={s["role"]:s for s in ASSETS}; scales={"directional-arrow":1.35,"any-note":1.35,"guard":1.25,"bomb":1.35,"wall":.58,"track":.42,"athlete-marker":3.2}
    rotations={"wall":(math.radians(18),math.radians(-22),0),"track":(math.radians(62),0,0)}
    for s,(x,y) in zip(ASSETS,cells):
        panels.append(add_panel(x,y,2.72,2.72)); sc=scales[s["role"]]
        o=add_review_asset(s,(x,y+.18,0),(sc,sc,.08 if s["role"]=="track" else sc),rotations.get(s["role"],(0,0,0)),s["role"]+"/neutral")
        assets.append((s,o,s["role"]+"/neutral")); labels.append(add_label(s["role"]+" / "+s["variant"],(x,y-1.02,-.22),.19))
    labels.append(add_label("AEROBEAT "+VERSION+" - SEVEN CANONICAL ASSETS",(0,3.35,-.22),.32))
    labels.append(add_label("FRONT = -Z   |   +Y UP   |   WHITE RIM / CHARCOAL SEPARATOR / ROLE INSET",(0,-3.25,-.22),.20))
    camera,boxes=fit_camera([x[1] for x in assets]+panels+labels,direction=(0,0,-1),margin=.035,lens=52,orthographic=True)
    p=rd/"neutral-board.png"; render(p); images.append(p)
    layouts[p.name]={"kind":"neutral-grid","minimum_margin":.035,"objects":[layout_entry(camera,s["role"],s["variant"],o,n) for s,o,n in assets]}
    # Perspective gameplay context: required roles, exactly two shields, and three distinct marker spheres.
    reset(); setup_render((.06,.11,.16,1)); context=[]
    def ctx(role,loc,scale=(1,1,1),instance=None):
        s=roles[role]; name=instance or role; o=add_review_asset(s,loc,scale,instance=name); context.append((s,o,name)); return o
    ctx("track",(0,-1.15,4.5),(.9,.9,.50),"track/context")
    ctx("directional-arrow",(-1.65,.45,-.1),(1.5,1.5,1.5),"directional-arrow/context")
    ctx("any-note",(1.25,.15,.9),(1.5,1.5,1.5),"any-note/context")
    ctx("guard",(-1.05,.15,2.4),(1.5,1.5,1.5),"guard/left-identical")
    ctx("guard",(1.05,.15,2.4),(1.5,1.5,1.5),"guard/right-identical")
    ctx("bomb",(0,.15,4.2),(1.2,1.2,1.2),"bomb/context")
    ctx("wall",(1.35,.0,6.7),(1,1,3.2),"wall/scaled-full-interval")
    ctx("athlete-marker",(0,.65,-1.5),(2,2,2),"athlete-marker/nose")
    ctx("athlete-marker",(-.72,.08,-1.5),(2,2,2),"athlete-marker/left-wrist")
    ctx("athlete-marker",(.72,.08,-1.5),(2,2,2),"athlete-marker/right-wrist")
    camera,_=fit_camera([x[1] for x in context],direction=(.46,.42,-1),margin=.10,lens=52)
    # Review-only built-in Blender text overlay; never exported or stored in a source snapshot.
    cam_q=camera.rotation_euler.copy(); forward=cam_q.to_quaternion() @ Vector((0,0,-1)); right=cam_q.to_quaternion() @ Vector((1,0,0)); up=cam_q.to_quaternion() @ Vector((0,1,0))
    overlay_center=camera.location+forward*1.25
    text="GAMEPLAY CONTEXT - COMPLETE FRAME\nARROW | CIRCLE | 2x IDENTICAL SHIELD | BOMB | SCALED WALL | TRACK\nMARKERS: NOSE | LEFT WRIST | RIGHT WRIST"
    t=add_label(text,overlay_center+up*.20,.013); t.data.space_line=1.15; t.rotation_euler=cam_q; t.location-=right*.0
    p=rd/"gameplay-context.png"; render(p); images.append(p)
    layouts[p.name]={"kind":"gameplay-context","minimum_margin":.10,"required_counts":{"directional-arrow":1,"any-note":1,"guard":2,"bomb":1,"wall":1,"track":1,"athlete-marker":3},"objects":[layout_entry(camera,s["role"],s["variant"],o,n) for s,o,n in context]}
    # Canonical one-cell and adjacent-cell wall proof. Grid centers use exact 1.0
    # pitch, both cell faces and wall sources are exact 0.94 squares, and the
    # visible 0.06 pitch gap remains unobstructed. Geometry is local analytic art.
    reset(); setup_render((.035,.055,.085,1)); wall_grid=[]; cells=[]; labels=[]
    wall_path=root/"release"/"raw"/VERSION/"wall"/"red-glass-v1.glb"
    for row_y,row_name in ((1.1,"ONE CELL"),(-1.1,"THREE ADJACENT CELLS")):
        centers=(0,) if row_name=="ONE CELL" else (-1,0,1)
        for x in centers:
            cv,cf=box(x-.47,x+.47,row_y-.47,row_y+.47,-.535,-.52)
            mesh=bpy.data.meshes.new(f"review/cell/{row_name}/{x}/mesh"); mesh.from_pydata(cv,[],cf); mesh.materials.append(material("blue_ice")); mesh.update()
            cell=bpy.data.objects.new(f"review/cell/{row_name}/{x}",mesh); bpy.context.collection.objects.link(cell); cells.append(cell)
            wall=import_review_mesh(wall_path,f"wall-grid/{row_name}/{x}"); wall.location=(x,row_y,0); wall_grid.append((wall,row_name,x))
        labels.append(add_label(row_name,(0,row_y-.76,-.64),.18))
    labels.append(add_label("WALL 0.94 x 0.94 | CELL 0.94 x 0.94 | PITCH 1.00 | GAP 0.06",(0,2.18,-.64),.24))
    labels.append(add_label("UNIT X/Y SCALE | CENTERED PIVOT | AUTHORITATIVE Z SCALE ONLY",(0,-2.20,-.64),.18))
    camera,_=fit_camera([x[0] for x in wall_grid]+cells+labels,direction=(0,0,-1),margin=.08,lens=56)
    p=rd/"wall-grid-comparison.png"; render(p); images.append(p)
    layouts[p.name]={"kind":"wall-grid-comparison","minimum_margin":.08,"objects":[layout_entry(camera,"wall","red-glass-v1",o,f"wall/{name}/{x}") for o,name,x in wall_grid]}
    wall_grid_evidence={"schema":"aerobeat.wall-grid-review/v1","release":VERSION,"image":p.name,"source_dimensions":[.94,.94,1.0],"measured_source_aabb":[[-.47,-.47,-.5],[.47,.47,.5]],"canonical_cell_dimensions":[.94,.94],"cell_pitch":[1.0,1.0],"adjacent_gap":[.06,.06],"pivot":[0,0,0],"xy_scale":[1,1],"z_scale":"authoritative interval only","rows":[{"name":"one-cell","centers":[[0,1.1]],"overlap":False},{"name":"adjacent-cells","centers":[[-1,-1.1],[0,-1.1],[1,-1.1]],"overlap":False}],"materials":{"analytic_only":True,"body":"mat/red_glass","edge":"mat/red_edge","depth_test":True,"depth_write":False,"order":"after-track"},"glb_sha256":sha(wall_path)}
    write_json(rd/"wall-grid.v1.json",wall_grid_evidence)
    # Truthful predecessor/current marker comparison across analytic backgrounds.
    reset(); setup_render(); compare=[]; panels=[]; labels=[]
    rows=[("DARK ICE",2.05,"dark_ice"),("BRIGHT ICE",0,"bright_ice"),("BLUE ICE",-2.05,"blue_ice")]
    predecessor_root=root if (root/"release"/"raw"/PREDECESSOR_RELEASE).is_dir() else Path(__file__).resolve().parents[1]
    columns=[(PREDECESSOR_RELEASE,-3.25),(VERSION,3.25)]
    for release,x in columns:
        labels.append(add_label("RELEASE "+release,(x,3.34,-.24),.30))
        for bg,y,panel_material in rows:
            panels.append(add_panel(x,y,6.0,1.75,.40,panel_material))
            labels.append(add_label(bg,(x-2.50,y+.60,-.26),.16,"LEFT"))
            release_root=predecessor_root if release==PREDECESSOR_RELEASE else root
            marker_path=release_root/"release"/"raw"/release/"athlete-marker"/"sphere-v1.glb"
            marker=import_review_mesh(marker_path,f"compare/{release}/{bg}/marker",require_outward=release==VERSION)
            marker.location=(x,y+.02,-.18); marker.scale=(5.2,5.2,5.2)
            compare.append(("athlete-marker","sphere-v1",marker,f"{release}/{bg}/marker",release))
            labels.append(add_label("0.18 UNIT BOUNDS | A=1 OPAQUE",(x,y-.66,-.26),.135))
    old_marker=sha(predecessor_root/"release"/"raw"/PREDECESSOR_RELEASE/"athlete-marker"/"sphere-v1.glb")
    new_marker=sha(root/"release"/"raw"/VERSION/"athlete-marker"/"sphere-v1.glb")
    labels.append(add_label("CANONICAL MARKER VISIBILITY | ACTUAL GLBs | SAME -Z REVIEW FRAMING",(0,3.78,-.24),.22))
    labels.append(add_label(VERSION+": OUTWARD CCW | EMBEDDED NORMALS | BACKFACE CULLING ENABLED",(0,-3.18,-.24),.14))
    labels.append(add_label(PREDECESSOR_RELEASE+" SHA256 marker "+old_marker,(0,-3.46,-.24),.105))
    labels.append(add_label(VERSION+" SHA256 marker "+new_marker,(0,-3.68,-.24),.105))
    camera,_=fit_camera([x[2] for x in compare]+panels+labels,direction=(0,0,-1),margin=.035,lens=52,orthographic=True)
    p=rd/"visibility-comparison.png"; render(p); images.append(p)
    layouts[p.name]={"kind":"visibility-comparison","minimum_margin":.035,"backgrounds":[x[0] for x in rows],"counts_per_release":{"athlete-marker":3},"backface_culling":True,"objects":[layout_entry(camera,r,v,o,n,release) for r,v,o,n,release in compare]}
    visibility={"schema":"aerobeat.marker-visibility-review/v1","release":VERSION,"predecessor":PREDECESSOR_RELEASE,"image":"visibility-comparison.png","backgrounds":[x[0] for x in rows],"camera":"consistent -Z review-facing mini-scenes; actual release GLBs","counts_per_release":{"athlete-marker":3},"geometry":{PREDECESSOR_RELEASE:{"dimensions":[.18,.18,.18],"triangles":168},VERSION:{"dimensions":[.18,.18,.18],"triangles":168,"outward_ccw":True,"embedded_normal_agreement":True}},"materials":{PREDECESSOR_RELEASE:{"names":["mat/charcoal","mat/white","mat/tint_base"],"alpha":1.0,"alpha_mode":"OPAQUE","backface_culling":True,"rejected_inward_winding":True},VERSION:{"names":["mat/charcoal","mat/white","mat/tint_base"],"alpha":1.0,"alpha_mode":"OPAQUE","blend":"opaque","cull":"back","depth_test":True,"depth_write":True,"backface_culling":True,"runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"]}},"glb_sha256":{PREDECESSOR_RELEASE:old_marker,VERSION:new_marker}}
    write_json(rd/"visibility.v1.json",visibility)
    # Camera-accessible marker evidence covers every cardinal hemisphere on both
    # bright and dark fields. The source remains exactly 0.18 units in every axis.
    face_images=[]; marker_spec=roles["athlete-marker"]
    camera_directions=(("plus-x",(1,0,0)),("minus-x",(-1,0,0)),("plus-y",(0,1,0)),("minus-y",(0,-1,0)),("plus-z",(0,0,1)),("minus-z",(0,0,-1)))
    for background,color_name in (("bright", "bright_ice"),("dark","dark_ice")):
        for face,direction in camera_directions:
            reset(); setup_render(COLORS[color_name][0])
            marker_path=root/"release"/"raw"/VERSION/"athlete-marker"/"sphere-v1.glb"
            o=import_review_mesh(marker_path,f"athlete-marker/{face}-{background}",require_outward=True)
            camera,_=fit_camera([o],direction=direction,margin=.16,lens=58)
            p=rd/f"athlete-marker--sphere-v1--{face}-{background}.png"; render(p); images.append(p); face_images.append(p.name)
            layouts[p.name]={"kind":"athlete-marker-face-contrast","camera_face":face,"background":background.upper(),"minimum_margin":.16,"backface_culling":True,"embedded_normals":True,"exterior_visible":True,"objects":[layout_entry(camera,"athlete-marker","sphere-v1",o,f"athlete-marker/{face}-{background}")]}
    def linear_luminance(rgb):
        channels=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        return .2126*channels[0]+.7152*channels[1]+.0722*channels[2]
    def contrast(a,b):
        x,y=linear_luminance(a),linear_luminance(b)
        return round((max(x,y)+.05)/(min(x,y)+.05),6)
    bright=COLORS["bright_ice"][0][:3]; dark=COLORS["dark_ice"][0][:3]; white=COLORS["white"][0][:3]; charcoal=COLORS["charcoal"][0][:3]
    contrast_evidence={"schema":"aerobeat.athlete-marker-contrast/v1","release":VERSION,"backgrounds":["BRIGHT","DARK"],"images":face_images,"camera_faces":[x[0] for x in camera_directions],"materials":{"alpha":1.0,"alpha_mode":"OPAQUE","blend":"opaque","cull":"back","depth_test":True,"depth_write":True,"backface_culling":True,"analytic_only":True,"runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"]},"geometry":{"dimensions":[.18,.18,.18],"surface":"one closed partitioned sphere","explicit_normals":True,"outward_ccw":True,"geometric_normal_agreement":True,"coplanar_overlapping_faces":False,"material_triangle_counts":{"mat/charcoal":24,"mat/white":80,"mat/tint_base":64},"all_materials_visible_each_camera_direction":True,"exterior_visible_with_backface_culling":True},"analytic_contrast":{"white_vs_charcoal":contrast(white,charcoal),"charcoal_vs_bright_ice":contrast(charcoal,bright),"white_vs_dark_ice":contrast(white,dark),"minimum_structural_required":7.0}}
    write_json(rd/"contrast.v1.json",contrast_evidence)
    # Calculated, safe-margin individual three-quarter views.
    for s in ASSETS:
        reset(); setup_render(); o=add_review_asset(s,rotation=(0,math.radians(58),0) if s["role"]=="track" else (0,0,0),instance=s["role"]+"/individual")
        direction=(.30,1,-.38) if s["role"]=="track" else ((.42,.32,-1) if s["role"] in ("wall","bomb","athlete-marker") else (.24,.16,-1))
        camera,_=fit_camera([o],direction=direction,margin=.12,lens=58)
        p=rd/(s["role"]+"--"+s["variant"]+".png"); render(p); images.append(p)
        layouts[p.name]={"kind":"individual","minimum_margin":.12,"objects":[layout_entry(camera,s["role"],s["variant"],o,s["role"]+"/individual")]}
    write_json(rd/"layout.v1.json",{"schema":"aerobeat.review-layout/v1","release":VERSION,"resolution":[1600,900],"images":layouts})
    write_json(rd/"hashes.v1.json",{"schema":"aerobeat.review-hashes/v1","release":VERSION,"resolution":[1600,900],"renderer":"Blender 4.0.2 EEVEE","files":[{"path":p.name,"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(images)],"layout":{"path":"layout.v1.json","bytes":(rd/"layout.v1.json").stat().st_size,"sha256":sha(rd/"layout.v1.json")},"visibility":{"path":"visibility.v1.json","bytes":(rd/"visibility.v1.json").stat().st_size,"sha256":sha(rd/"visibility.v1.json")},"contrast":{"path":"contrast.v1.json","bytes":(rd/"contrast.v1.json").stat().st_size,"sha256":sha(rd/"contrast.v1.json")},"wall_grid":{"path":"wall-grid.v1.json","bytes":(rd/"wall-grid.v1.json").stat().st_size,"sha256":sha(rd/"wall-grid.v1.json")}})

def glb_json(path):
    b=path.read_bytes(); magic,ver,total=struct.unpack_from("<4sII",b,0); assert magic==b"glTF" and ver==2 and total==len(b)
    n,t=struct.unpack_from("<I4s",b,12); assert t==b"JSON"; return json.loads(b[20:20+n].decode("utf-8").rstrip(" \x00"))

def material_manifest(role,names):
    result={"analytic_only":True,"textures":[],"names":names}
    if role=="directional-arrow":
        result["contract"]={
            "opacity":1.0,"alpha_mode":"OPAQUE","blend":"opaque","double_sided":False,
            "cull":"back","depth_test":True,"depth_write":True,
            "white_outline_material":"mat/white","runtime_tint_material":"mat/tint_base",
            "runtime_tint_targets":["red","yellow","green"],"styled_faces":["+Z","-Z"],
            "coplanar_overlapping_caps":False,"renderer_y_flip":False,
            "screen_direction_rotation_degrees":SCREEN_DIRECTIONS}
    elif role=="track":
        result["contract"]={
            "opacity":0.52,"predecessor_opacity":0.20,"opacity_multiplier":2.6,
            "alpha_mode":"BLEND","blend":"alpha","double_sided":False,"cull":"back",
            "depth_test":True,"depth_write":False,"order":"after-grid-before-wall",
            "justification":"0.52 is 2.6x stronger than 0.20 and remains translucent blue glass over bright ice."}
    elif role=="wall":
        result["contract"]={
            "body_opacity":0.24,"edge_opacity":0.82,"alpha_mode":"BLEND","blend":"alpha",
            "double_sided":False,"cull":"back","depth_test":True,"depth_write":False,
            "order":"after-track","unit_cell_footprint":[0.94,0.94],"cell_pitch":[1.0,1.0],
            "adjacent_gap":[0.06,0.06],"xy_scale_authoritative":[1,1],"z_scale_authoritative":True}
    elif role=="athlete-marker":
        result["contract"]={
            "opacity":1.0,"alpha_mode":"OPAQUE","blend":"opaque","double_sided":False,
            "cull":"back","depth_test":True,"depth_write":True,"normals":"explicit-unit-radial",
            "winding":"outward-ccw","geometric_normal_agreement":True,"source_backface_culling":True,
            "runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"],
            "all_camera_directions":["+X","-X","+Y","-Y","+Z","-Z"],
            "coplanar_overlapping_faces":False,"canonical_instances":["nose","left-wrist","right-wrist"]}
    return result

def main():
    global VERSION
    ap=argparse.ArgumentParser(); ap.add_argument("--output-root",required=True); ap.add_argument("--release",required=True,choices=[SUPPORTED_RELEASE]); a=ap.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    VERSION=a.release
    root=Path(a.output_root).absolute(); rel=root/"release"/"raw"/VERSION; review_target=root/"review"/VERSION
    if rel.exists() or review_target.exists(): raise SystemExit(f"immutable successor target already exists: release={rel.exists()} review={review_target.exists()}")
    records=[]
    for s in ASSETS:
        src,glb,aabb,tris,mats=export_asset(root,s)
        manifest={
          "schema":"aerobeat.gameplay-asset/v1","release":VERSION,"identity":{"role":s["role"],"variant":s["variant"],"canonical_name":s["role"]+"/"+s["variant"]},
          "files":{"source":"source/%s/%s/%s.blend"%(s["role"],s["variant"],s["variant"]),"release":"release/raw/%s/%s/%s.glb"%(VERSION,s["role"],s["variant"]),"source_sha256":sha(src),"source_bytes":src.stat().st_size,"release_sha256":sha(glb),"release_bytes":glb.stat().st_size},
          "names":{"node":s["role"]+"/"+s["variant"],"mesh":s["role"]+"/"+s["variant"]+"/mesh","materials":mats},
          "source_authority":{"generator":"tools/generate.py","blend_byte_determinism_claimed":False,"note":"The tracked .blend is an editable binary snapshot; deterministic generator code is authoritative."},
          "geometry":{"dimensions":s["dimensions"],"measured_aabb":aabb,"pivot":s["pivot"],"object_origin":[0,0,0],"rotation_euler":[0,0,0],"scale":[1,1,1],"triangle_count":tris,"triangle_budget":s["budget"],"collision_free_bound":s["bound"]},
          "coordinates":{"handedness":"right","up":"+Y","forward":"-Z","visible_face":"all camera directions" if s["role"]=="athlete-marker" else ("both +Z/-Z" if s["role"]=="directional-arrow" else ("-Z" if s["role"] in ("any-note","guard") else "not-applicable"))},
          "materials":material_manifest(s["role"],mats),"reuse":s["reuse"],
          "rights":{"license":"CC-BY-NC-4.0","creator":"AeroBeat / Gambit Games","third_party_content":False},
          "provenance":{"method":"locally authored deterministic procedural primitives","generator":GENERATOR,"blender":BLENDER,"external_assets":[],"network":False},
          "dependencies":[]
        }
        mp=root/"manifests"/s["role"]/(s["variant"]+".v1.json")
        rmp=rel/"manifests"/s["role"]/(s["variant"]+".v1.json")
        if s["role"] in CHANGED_SOURCE_ROLES:
            write_json(mp,manifest)
            release_manifest=json.loads(json.dumps(manifest)); release_manifest["files"].pop("source_sha256"); release_manifest["files"].pop("source_bytes")
            write_json(rmp,release_manifest)
        else:
            authority=root if mp.is_file() else Path(__file__).resolve().parents[1]
            predecessor_manifest=authority/"release"/"raw"/PREDECESSOR_RELEASE/"manifests"/s["role"]/(s["variant"]+".v1.json")
            rmp.parent.mkdir(parents=True,exist_ok=True); rmp.write_bytes(predecessor_manifest.read_bytes())
            if not mp.is_file():
                source_manifest=authority/"manifests"/s["role"]/(s["variant"]+".v1.json")
                mp.parent.mkdir(parents=True,exist_ok=True); mp.write_bytes(source_manifest.read_bytes())
            manifest=json.loads(mp.read_text(encoding="utf-8"))
        records.append((s,src,glb,mp,rmp,manifest))
    setdoc={"schema":"aerobeat.gameplay-set/v1","name":"default-v1","release":VERSION,"roles":{s["role"]:s["variant"] for s in ASSETS},"constraints":{"guard_instances_per_beat":2,"guard_canonical_asset":"guard/shield-v1"}}
    write_json(root/"sets"/"default-v1.json",setdoc); write_json(rel/"sets"/"default-v1.json",setdoc)
    payload=[]
    for p in sorted(rel.rglob("*")):
        if p.is_file(): payload.append({"path":p.relative_to(rel).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)})
    inv={"schema":"aerobeat.release-inventory/v1","release":VERSION,"immutable":True,"expected_asset_count":7,"payload":payload}
    write_json(rel/"inventory.v1.json",inv)
    proof={"schema":"aerobeat.release-proof/v1","release":VERSION,"inventory_sha256":sha(rel/"inventory.v1.json"),"generator":GENERATOR,"blender":BLENDER,"determinism":{"scope":"every file under release/raw/%s"%VERSION,"method":"primary plus two clean temporary byte comparisons","blend_snapshots_in_scope":False},"blend_snapshot_limitation":"Blender .blend container bytes are not claimed deterministic; tracked editable snapshots are subordinate to tools/generate.py.","claims":{"separate_glbs":True,"combined_glb":False,"analytic_materials_only":True,"textures":0,"external_dependencies":0,"canonical_shields":1,"guard_instances_required":2,"changed_identity":"athlete-marker/sphere-v1","byte_identical_predecessor_roles":["directional-arrow","any-note","guard","bomb","wall","track"],"directional_arrow":{"opacity":1.0,"alpha_mode":"OPAQUE","depth_test":True,"depth_write":True,"styled_faces":["+Z","-Z"],"coplanar_overlapping_caps":False,"renderer_y_flip":False,"runtime_tint_targets":["red","yellow","green"],"screen_direction_rotation_degrees":SCREEN_DIRECTIONS},"track":{"opacity":0.52,"predecessor_opacity":0.20,"opacity_multiplier":2.6,"alpha_mode":"BLEND","depth_write":False,"order":"after-grid-before-wall"},"wall":{"source_dimensions":[0.94,0.94,1.0],"unit_cell_footprint":[0.94,0.94],"cell_pitch":[1.0,1.0],"adjacent_gap":[0.06,0.06],"xy_scale_authoritative":[1,1],"z_scale_authoritative":True,"centered_pivot":True,"closed_body":True,"adjacent_instances_overlap":False},"athlete_marker":{"dimensions":[0.18,0.18,0.18],"canonical_identity":"athlete-marker/sphere-v1","canonical_instances":["nose","left-wrist","right-wrist"],"opacity":1.0,"alpha_mode":"OPAQUE","depth_test":True,"depth_write":True,"explicit_normals":True,"winding":"outward-ccw","geometric_normal_agreement":True,"source_backface_culling":True,"runtime_tint_material":"mat/tint_base","structural_materials":["mat/white","mat/charcoal"],"all_camera_directions":["+X","-X","+Y","-Y","+Z","-Z"],"coplanar_overlapping_faces":False}}}
    write_json(rel/"proof.v1.json",proof)
    review(root)
    expected_release={"inventory.v1.json","proof.v1.json","sets/default-v1.json"}
    expected_sources=set(); expected_manifests=set()
    for s in ASSETS:
        role=s["role"]; variant=s["variant"]
        expected_release|={f"{role}/{variant}.glb",f"manifests/{role}/{variant}.v1.json"}
        expected_sources.add(f"{role}/{variant}/{variant}.blend")
        expected_manifests.add(f"{role}/{variant}.v1.json")
    actual_release={p.relative_to(rel).as_posix() for p in rel.rglob("*") if p.is_file()}
    actual_sources={p.relative_to(root/"source").as_posix() for p in (root/"source").rglob("*") if p.is_file()}
    actual_manifests={p.relative_to(root/"manifests").as_posix() for p in (root/"manifests").rglob("*") if p.is_file()}
    review_dir=root/"review"/VERSION
    actual_review_pngs={p.name for p in review_dir.glob("*.png")}
    marker_faces={f"athlete-marker--sphere-v1--{face}-{background}.png" for face in ("plus-x","minus-x","plus-y","minus-y","plus-z","minus-z") for background in ("bright","dark")}
    expected_review_pngs={"neutral-board.png","gameplay-context.png","wall-grid-comparison.png","visibility-comparison.png"}|marker_faces|{s["role"]+"--"+s["variant"]+".png" for s in ASSETS}
    actual_review_metadata={p.name for p in review_dir.glob("*.json")}
    if actual_release!=expected_release: raise RuntimeError(f"generation release postcondition mismatch: {sorted(actual_release)}")
    if actual_sources!=expected_sources: raise RuntimeError(f"generation source postcondition mismatch: {sorted(actual_sources)}")
    if actual_manifests!=expected_manifests: raise RuntimeError(f"generation manifest postcondition mismatch: {sorted(actual_manifests)}")
    if actual_review_pngs!=expected_review_pngs or actual_review_metadata!={"hashes.v1.json","layout.v1.json","visibility.v1.json","contrast.v1.json","wall-grid.v1.json"}: raise RuntimeError("generation review postcondition mismatch")
    if {p.name for p in (root/"sets").glob("*.json")}!={"default-v1.json"}: raise RuntimeError("generation set postcondition mismatch")
    print("GENERATE_OK release=0.0.7 assets=7 sources=7 manifests=7 release_files=17 review_pngs=23 review_metadata=5")

if __name__=="__main__": main()
