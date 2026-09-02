#!/usr/bin/env python3
"""Deterministically author AeroBeat gameplay assets with Blender 4.0.2.

Run only through Blender:
  blender --background --factory-startup --python tools/generate.py -- --output-root .
No network, imported content, fonts, images, or textures are used.
"""
from __future__ import annotations
import argparse, hashlib, json, math, shutil, struct, sys
from pathlib import Path

import bpy
from mathutils import Vector

VERSION = "0.0.1"
BLENDER = "4.0.2"
GENERATOR = "aerobeat-gameplay-generator-v1"

ASSETS = [
    dict(role="directional-arrow", variant="outline-v1", dimensions=[0.78,0.78,0.18], pivot=[0,0,0], budget=420, bound=[[-0.42,-0.42,-0.11],[0.42,0.42,0.11]], reuse="one mesh for Flow and Boxing; rotate only about local Z"),
    dict(role="any-note", variant="circle-v1", dimensions=[0.70,0.70,0.18], pivot=[0,0,0], budget=320, bound=[[-0.38,-0.38,-0.11],[0.38,0.38,0.11]], reuse="one directionless mesh across applicable modes"),
    dict(role="guard", variant="shield-v1", dimensions=[0.72,0.82,0.16], pivot=[0,0,0.07], budget=520, bound=[[-0.39,-0.44,-0.10],[0.39,0.44,0.10]], reuse="exactly one canonical shield; instance twice simultaneously without mirroring or material/scale variation"),
    dict(role="bomb", variant="urchin-v1", dimensions=[0.78,0.78,0.78], pivot=[0,0,0], budget=900, bound=[[-0.42,-0.42,-0.42],[0.42,0.42,0.42]], reuse="one bomb mesh for every bomb event"),
    dict(role="wall", variant="red-glass-v1", dimensions=[1.80,1.90,1.00], pivot=[0,0,0], budget=144, bound=[[-0.94,-0.99,-0.54],[0.94,0.99,0.54]], reuse="unit interval source; scale only Z to authoritative L=max(0.08,speedWorldUnitsPerMs*(endTimestampMs-centerTimestampMs))"),
    dict(role="track", variant="blue-glass-v1", dimensions=[4.20,0.06,24.00], pivot=[0,0.03,0], budget=160, bound=[[-2.14,-0.04,-12.04],[2.14,0.08,12.04]], reuse="one canonical segment; extend by deterministic segment reuse, never stretch lane-line width"),
    dict(role="athlete-marker", variant="sphere-v1", dimensions=[0.18,0.18,0.18], pivot=[0,0,0], budget=192, bound=[[-0.10,-0.10,-0.10],[0.10,0.10,0.10]], reuse="same full 3D sphere for nose and both wrists; truthful world positions and normal depth"),
]

COLORS = {
    "white": ((0.95,0.98,1.0,1),0.30,0.0,"OPAQUE"),
    "charcoal": ((0.035,0.045,0.06,1),0.43,0.0,"OPAQUE"),
    "cyan": ((0.03,0.55,0.95,1),0.38,0.05,"OPAQUE"),
    "green": ((0.04,0.60,0.28,1),0.38,0.03,"OPAQUE"),
    "black": ((0.012,0.014,0.018,1),0.46,0.0,"OPAQUE"),
    "red_emissive": ((0.9,0.015,0.02,1),0.34,4.0,"OPAQUE"),
    "red_glass": ((0.65,0.01,0.018,0.24),0.20,0.25,"BLEND"),
    "red_edge": ((0.95,0.01,0.015,0.82),0.28,5.0,"BLEND"),
    "blue_glass": ((0.12,0.68,0.92,0.20),0.16,0.15,"BLEND"),
    "cyan_edge": ((0.05,0.80,1.0,1),0.25,3.0,"OPAQUE"),
    "marker": ((0.98,0.98,1.0,1),0.34,0.1,"OPAQUE"),
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
    m.diffuse_color=rgba; m.use_nodes=True
    if blend=="BLEND": m.blend_method="BLEND"; m.show_transparent_back=True
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

def extrude(poly,z0,z1):
    n=len(poly); v=[(x,y,z0) for x,y in poly]+[(x,y,z1) for x,y in poly]; f=[]
    # front (-Z) and rear caps; deterministic fans
    for i in range(1,n-1): f.append((0,i+1,i)); f.append((n,n+i,n+i+1))
    for i in range(n): j=(i+1)%n; f += [(i,j,n+j),(i,n+j,n+i)]
    return v,f

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
        for s,z0,z1,m in [(1,-.088,.088,"white"),(.91,-.090,-.085,"charcoal"),(.80,-.092,-.087,"cyan")]:
            cv,cf=extrude([(x*s,y*s) for x,y in p],z0,z1); add_comp(v,f,mi,cv,cf,matn(m))
    elif role=="any-note":
        for r,z0,z1,m in [(.35,-.086,.086,"white"),(.315,-.090,-.085,"charcoal"),(.275,-.094,-.089,"cyan")]:
            cv,cf=cylinder(r,z0,z1,24); add_comp(v,f,mi,cv,cf,matn(m))
    elif role=="guard":
        p=[(-.36,.30),(-.25,.41),(.25,.41),(.36,.30),(.30,-.20),(0,-.41),(-.30,-.20)]
        # Geometry center is z=-0.07 because origin is the specified rear-grip pivot.
        for s,z0,z1,m in [(1,-.144,.01,"white"),(.91,-.147,-.142,"charcoal"),(.79,-.15,-.145,"green")]:
            cv,cf=extrude([(x*s,y*s) for x,y in p],z0,z1); add_comp(v,f,mi,cv,cf,matn(m))
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
        cv,cf=box(-.9,.9,-.95,.95,-.5,.5); add_comp(v,f,mi,cv,cf,matn("red_glass"))
        # Twelve square-prism edges: exactly 96 edge triangles plus 12 body triangles.
        t=.018
        edges=[]
        # Cage prisms remain inside the exact 1.80 x 1.90 x 1.00 source extent.
        for y in (-.95+t,.95-t):
            for z in (-.5+t,.5-t): edges.append((-.9,.9,y,y,z,z,"x"))
        for x in (-.9+t,.9-t):
            for z in (-.5+t,.5-t): edges.append((x,x,-.95,.95,z,z,"y"))
        for x in (-.9+t,.9-t):
            for y in (-.95+t,.95-t): edges.append((x,x,y,y,-.5,.5,"z"))
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
        cv,cf=uv_sphere(.09); add_comp(v,f,mi,cv,cf,matn("marker"))
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
    for p in mesh.polygons: p.use_smooth=False
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
        primitives.append({"attributes":{"POSITION":0},"indices":len(accessors)-1,"material":mat_index,"mode":4})
    materials=[]
    for name in material_names:
        rgba,rough,emit,blend=COLORS[name]
        m={"name":"mat/"+name,"pbrMetallicRoughness":{"baseColorFactor":list(rgba),"metallicFactor":0.0,"roughnessFactor":rough},"doubleSided":False}
        if emit: m["emissiveFactor"]=[rgba[0]*min(emit,1),rgba[1]*min(emit,1),rgba[2]*min(emit,1)]
        if blend=="BLEND": m["alphaMode"]="BLEND"
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
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(src),compress=False,check_existing=False)
    out=root/"release"/"raw"/VERSION/role/(variant+".glb")
    names=[m.name.removeprefix("mat/") for m in obj.data.materials]; write_glb(out,obj,names)
    aabb,tris=measured(obj)
    return src,out,aabb,tris,[m.name for m in obj.data.materials]

def camera_at(location,target,lens=52):
    bpy.ops.object.camera_add(location=location); c=bpy.context.object; c.name="review/camera"; c.data.lens=lens
    c.rotation_euler=(Vector(target)-c.location).to_track_quat("-Z","Y").to_euler(); bpy.context.scene.camera=c

def setup_render(world=(.025,.032,.05,1)):
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=1600; s.render.resolution_y=900; s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGB"; s.render.film_transparent=False
    s.render.image_settings.color_depth="8"; s.render.image_settings.compression=15
    if s.world is None: s.world=bpy.data.worlds.new("review/world")
    s.world.color=world[:3]; s.view_settings.look="AgX - Medium High Contrast"
    bpy.ops.object.light_add(type="AREA",location=(4,6,-4)); bpy.context.object.data.energy=1300; bpy.context.object.data.shape="DISK"; bpy.context.object.data.size=5
    bpy.ops.object.light_add(type="AREA",location=(-4,2,3)); bpy.context.object.data.energy=900; bpy.context.object.data.size=4

def render(path):
    path.parent.mkdir(parents=True,exist_ok=True); bpy.context.scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)

def add_review_asset(spec,loc=(0,0,0),scale=(1,1,1)):
    o=make_asset(spec); o.location=loc; o.scale=scale; return o

def review(root):
    rd=root/"review"/VERSION; images=[]
    # Neutral overview board.
    reset(); setup_render();
    placements={"directional-arrow":(-2.4,.7,0),"any-note":(-1.2,.7,0),"guard":(0,.7,0),"bomb":(1.3,.7,0),"wall":(2.6,.65,.35),"athlete-marker":(-.65,-.55,0)}
    for s in ASSETS:
        if s["role"]=="track": add_review_asset(s,(0,-1.1,2.3),(.85,.85,.32))
        else: add_review_asset(s,placements[s["role"]])
    camera_at((.2,2.4,-7.3),(0,.1,0)); p=rd/"neutral-board.png"; render(p); images.append(p)
    # Gameplay context with canonical shield duplicated, long wall and three marker instances.
    reset(); setup_render((.06,.11,.16,1)); track=add_review_asset(next(x for x in ASSETS if x["role"]=="track"),(0,-1.15,5.5),(.9,.9,.55))
    ar=next(x for x in ASSETS if x["role"]=="directional-arrow"); ci=next(x for x in ASSETS if x["role"]=="any-note"); sh=next(x for x in ASSETS if x["role"]=="guard"); bo=next(x for x in ASSETS if x["role"]=="bomb"); wa=next(x for x in ASSETS if x["role"]=="wall"); mk=next(x for x in ASSETS if x["role"]=="athlete-marker")
    add_review_asset(ar,(-1.25,.15,-1.2)); add_review_asset(ci,(1.25,.15,.2)); add_review_asset(sh,(-1.05,.15,1.8)); add_review_asset(sh,(1.05,.15,1.8)); add_review_asset(bo,(0,.15,4.0)); add_review_asset(wa,(1.5,.0,6.0),(1,1,3.2))
    add_review_asset(mk,(0,.5,-2)); add_review_asset(mk,(-.65,.1,-2)); add_review_asset(mk,(.65,.1,-2))
    camera_at((5.4,5.0,-8.5),(0,-.2,3.0),48); p=rd/"gameplay-context.png"; render(p); images.append(p)
    # Individual three-quarter views.
    for s in ASSETS:
        reset(); setup_render(); o=add_review_asset(s)
        dims=s["dimensions"]; distance=max(dims)*2.2+1.2
        camera_at((distance*.55,distance*.35,-distance),(0,0,0),58)
        p=rd/(s["role"]+"--"+s["variant"]+".png"); render(p); images.append(p)
    write_json(rd/"hashes.v1.json",{"schema":"aerobeat.review-hashes/v1","release":VERSION,"resolution":[1600,900],"renderer":"Blender 4.0.2 EEVEE","files":[{"path":p.name,"sha256":sha(p)} for p in sorted(images)]})

def glb_json(path):
    b=path.read_bytes(); magic,ver,total=struct.unpack_from("<4sII",b,0); assert magic==b"glTF" and ver==2 and total==len(b)
    n,t=struct.unpack_from("<I4s",b,12); assert t==b"JSON"; return json.loads(b[20:20+n].decode("utf-8").rstrip(" \x00"))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-root",required=True); ap.add_argument("--skip-review",action="store_true"); a=ap.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    root=Path(a.output_root).absolute(); rel=root/"release"/"raw"/VERSION
    if rel.exists(): shutil.rmtree(rel)
    records=[]
    for s in ASSETS:
        src,glb,aabb,tris,mats=export_asset(root,s)
        manifest={
          "schema":"aerobeat.gameplay-asset/v1","release":VERSION,"identity":{"role":s["role"],"variant":s["variant"],"canonical_name":s["role"]+"/"+s["variant"]},
          "files":{"source":"source/%s/%s/%s.blend"%(s["role"],s["variant"],s["variant"]),"release":"release/raw/%s/%s/%s.glb"%(VERSION,s["role"],s["variant"]),"source_sha256":sha(src),"source_bytes":src.stat().st_size,"release_sha256":sha(glb),"release_bytes":glb.stat().st_size},
          "names":{"node":s["role"]+"/"+s["variant"],"mesh":s["role"]+"/"+s["variant"]+"/mesh","materials":mats},
          "source_authority":{"generator":"tools/generate.py","blend_byte_determinism_claimed":False,"note":"The tracked .blend is an editable binary snapshot; deterministic generator code is authoritative."},
          "geometry":{"dimensions":s["dimensions"],"measured_aabb":aabb,"pivot":s["pivot"],"object_origin":[0,0,0],"rotation_euler":[0,0,0],"scale":[1,1,1],"triangle_count":tris,"triangle_budget":s["budget"],"collision_free_bound":s["bound"]},
          "coordinates":{"handedness":"right","up":"+Y","forward":"-Z","visible_face":"-Z" if s["role"] in ("directional-arrow","any-note","guard") else "not-applicable"},
          "materials":{"analytic_only":True,"textures":[],"names":mats},"reuse":s["reuse"],
          "rights":{"license":"CC-BY-NC-4.0","creator":"AeroBeat / Gambit Games","third_party_content":False},
          "provenance":{"method":"locally authored deterministic procedural primitives","generator":GENERATOR,"blender":BLENDER,"external_assets":[],"network":False},
          "dependencies":[]
        }
        mp=root/"manifests"/s["role"]/(s["variant"]+".v1.json"); write_json(mp,manifest)
        release_manifest=json.loads(json.dumps(manifest)); release_manifest["files"].pop("source_sha256"); release_manifest["files"].pop("source_bytes")
        rmp=rel/"manifests"/s["role"]/(s["variant"]+".v1.json"); write_json(rmp,release_manifest)
        records.append((s,src,glb,mp,rmp,manifest))
    setdoc={"schema":"aerobeat.gameplay-set/v1","name":"default-v1","release":VERSION,"roles":{s["role"]:s["variant"] for s in ASSETS},"constraints":{"guard_instances_per_beat":2,"guard_canonical_asset":"guard/shield-v1"}}
    write_json(root/"sets"/"default-v1.json",setdoc); write_json(rel/"sets"/"default-v1.json",setdoc)
    payload=[]
    for p in sorted(rel.rglob("*")):
        if p.is_file(): payload.append({"path":p.relative_to(rel).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)})
    inv={"schema":"aerobeat.release-inventory/v1","release":VERSION,"immutable":True,"expected_asset_count":7,"payload":payload}
    write_json(rel/"inventory.v1.json",inv)
    proof={"schema":"aerobeat.release-proof/v1","release":VERSION,"inventory_sha256":sha(rel/"inventory.v1.json"),"generator":GENERATOR,"blender":BLENDER,"determinism":{"scope":"every file under release/raw/0.0.1","method":"primary plus two clean temporary byte comparisons","blend_snapshots_in_scope":False},"blend_snapshot_limitation":"Blender .blend container bytes are not claimed deterministic; tracked editable snapshots are subordinate to tools/generate.py.","claims":{"separate_glbs":True,"combined_glb":False,"analytic_materials_only":True,"textures":0,"external_dependencies":0,"canonical_shields":1,"guard_instances_required":2}}
    write_json(rel/"proof.v1.json",proof)
    if not a.skip_review: review(root)
    print("GENERATED",len(records),"assets at",root)

if __name__=="__main__": main()
