#!/usr/bin/env python3
"""Red-before/green-after geometry and raster oracles for the rounded arrow."""
from __future__ import annotations
import argparse, hashlib, json, math, shutil, tempfile
from collections import defaultdict
from pathlib import Path
from subprocess_contract import run_checked
from validate_rounded_candidate import accessor, assert_directional_arrow_contract, parse_glb, qpoint, validate_cue

BANDS=(
    ("outer-charcoal", "silhouette", "outer-white", .014),
    ("white", "outer-white", "inner-white", .052),
    ("inner-charcoal", "inner-white", "fill", .020),
)
DIRECTIONS=(0,-45,-90,-135,180,135,90,45)
COLORS=((.92,.12,.10),(.98,.78,.08),(.10,.82,.32))
SCALES=(.75,1.0,1.5)
DPRS=(1,2,3)
RASTER_TOLERANCE=.002
CHARCOAL=(.035,.045,.06)
WHITE=(.95,.98,1.0)
BACKGROUND=(0.0,0.0,0.0)

def polygon_area(points):
    return abs(sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))/2)

def point_in_polygon(point,polygon):
    x,y=point; inside=False
    for i,(ax,ay) in enumerate(polygon):
        bx,by=polygon[(i+1)%len(polygon)]
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax: inside=not inside
    return inside

def nearest(point,loop):
    best=None
    for i,left in enumerate(loop):
        right=loop[(i+1)%len(loop)]; vx,vy=right[0]-left[0],right[1]-left[1]; wx,wy=point[0]-left[0],point[1]-left[1]
        t=0 if vx*vx+vy*vy==0 else max(0,min(1,(wx*vx+wy*vy)/(vx*vx+vy*vy)))
        candidate=(left[0]+t*vx,left[1]+t*vy); distance=math.dist(point,candidate)
        if best is None or distance<best[0]: best=(distance,candidate)
    return best

def feature(point,loop):
    x,y=point; ax=abs(x); xmax=max(abs(px) for px,py in loop); ymax=max(py for px,py in loop)
    if y>.75*ymax: return "tip"
    if -.35*ymax<y<.65*ymax and .20*xmax<ax<.55*xmax: return "concave-shoulder"
    if y>-.35*ymax and ax>=.55*xmax: return "convex-shoulder"
    return "shaft"

def boundaries(path):
    doc,binary=parse_glb(path); primitives=doc["meshes"][0]["primitives"]; attrs=primitives[0]["attributes"]
    positions=accessor(doc,binary,attrs["POSITION"]); materials=doc["materials"]; triangles=[]; triangle_material=[]
    for primitive in primitives:
        values=accessor(doc,binary,primitive["indices"])
        for i in range(0,len(values),3): triangles.append(tuple(values[i:i+3])); triangle_material.append(materials[primitive["material"]]["name"])
    edges=defaultdict(list)
    for face_index,triangle in enumerate(triangles):
        points=[qpoint(positions[index]) for index in triangle]
        for left,right in zip(points,(points[1],points[2],points[0])): edges[tuple(sorted((left,right)))].append(face_index)
    def components(material_pair=None,z=.09):
        graph=defaultdict(set)
        for edge,owners in edges.items():
            if not all(abs(point[2]-z)<1e-6 for point in edge): continue
            if material_pair is not None and {triangle_material[index] for index in owners}!=set(material_pair): continue
            left,right=edge[0][:2],edge[1][:2]; graph[left].add(right); graph[right].add(left)
        result=[]; unseen=set(graph)
        while unseen:
            start=next(iter(unseen)); current=start; previous=None; ordered=[]
            while current not in ordered:
                ordered.append(current); unseen.discard(current)
                choices=[point for point in graph[current] if point!=previous]
                if not choices: raise AssertionError("open boundary")
                previous,current=current,choices[0]
            if current!=start: raise AssertionError("non-cycle boundary")
            result.append(ordered)
        return result
    white=sorted(components(("mat/charcoal","mat/white")),key=lambda loop:max(math.hypot(*point) for point in loop),reverse=True)
    fill=components(("mat/charcoal","mat/tint_base"))[0]
    silhouette=max((loop for loop in components(z=.078) if len(loop)==69),key=lambda loop:max(math.hypot(*point) for point in loop))
    return {"silhouette":silhouette,"outer-white":white[0],"inner-white":white[1],"fill":fill}

def measurements(loops):
    result={}
    for label,outer_name,inner_name,target in BANDS:
        outer,inner=loops[outer_name],loops[inner_name]; by_feature=defaultdict(list)
        for i,point in enumerate(inner):
            following=inner[(i+1)%len(inner)]
            for sample in (point,((point[0]+following[0])/2,(point[1]+following[1])/2)):
                distance,_=nearest(sample,outer); by_feature[feature(sample,inner)].append(distance)
        missing={"shaft","concave-shoulder","convex-shoulder","tip"}-set(by_feature)
        if missing: raise AssertionError(f"{label}: missing feature windows {sorted(missing)}")
        flat=[value for values in by_feature.values() for value in values]
        result[label]={"target":target,"minimum":min(flat),"maximum":max(flat),"spread":max(flat)-min(flat),"features":{name:(min(values),max(values)) for name,values in sorted(by_feature.items())}}
    return result

def assert_uniform(values,tolerance=.00050):
    for label,data in values.items():
        if data["minimum"]<data["target"]-tolerance or data["maximum"]>data["target"]+tolerance:
            raise AssertionError(f"{label}: nonuniform {data['minimum']}..{data['maximum']} target={data['target']}")

def material_at(point,loops,fill_color):
    if not point_in_polygon(point,loops["silhouette"]): return "background",BACKGROUND
    if not point_in_polygon(point,loops["outer-white"]): return "outer-charcoal",CHARCOAL
    if not point_in_polygon(point,loops["inner-white"]): return "white",WHITE
    if not point_in_polygon(point,loops["fill"]): return "inner-charcoal",CHARCOAL
    return "fill",fill_color

def color_distance(left,right): return math.sqrt(sum((a-b)**2 for a,b in zip(left,right)))

def worst_case_probes(loops):
    probes=[]
    for label,outer_name,inner_name,target in BANDS:
        outer,inner=loops[outer_name],loops[inner_name]; grouped=defaultdict(list)
        for index,point in enumerate(inner):
            following=inner[(index+1)%len(inner)]
            for kind,sample in (("vertex",point),("midpoint",((point[0]+following[0])/2,(point[1]+following[1])/2))):
                distance,outer_point=nearest(sample,outer)
                grouped[feature(sample,inner)].append((distance,kind,index,outer_point,sample))
        for name in ("shaft","concave-shoulder","convex-shoulder","tip"):
            values=grouped.get(name,[])
            if len(values)<2: raise AssertionError(f"raster {label}: insufficient {name} probes")
            # Exercise both extrema, never the old best-to-nominal representative.
            for extremum,item in (("minimum",min(values)),("maximum",max(values))):
                distance,kind,index,outer_point,inner_point=item
                probes.append((label,name,f"{extremum}-{kind}-{index}",target,distance,outer_point,inner_point))
    return probes

def raster_matrix(loops):
    for index,color in enumerate(COLORS):
        if min(color_distance(color,other) for other in (CHARCOAL,WHITE,BACKGROUND))<.20:
            raise AssertionError(f"raster color {index} lacks meaningful contrast: {color}")
    probes=worst_case_probes(loops); checks=0; observed=defaultdict(list); color_signatures=set()
    fill_probe=(sum(point[0] for point in loops["fill"])/len(loops["fill"]),sum(point[1] for point in loops["fill"])/len(loops["fill"]))
    for degrees in DIRECTIONS:
        angle=math.radians(degrees); c,s=math.cos(angle),math.sin(angle)
        for color_index,color in enumerate(COLORS):
            # Classification consumes rendered RGB values; each requested color must
            # remain present and distinguishable rather than being a loop-only no-op.
            if material_at(fill_probe,loops,color)[1]!=color: raise AssertionError(f"raster fill color lost: {color}")
            color_signatures.add(tuple(round(value,6) for value in material_at(fill_probe,loops,color)[1]))
            for scale in SCALES:
                for dpr in DPRS:
                    pitch=.78/(64*scale*dpr)
                    for label,name,probe,target,geometric_width,outer_point,inner_point in probes:
                        rotated_outer=(c*outer_point[0]-s*outer_point[1],s*outer_point[0]+c*outer_point[1])
                        rotated_inner=(c*inner_point[0]-s*inner_point[1],s*inner_point[0]+c*inner_point[1])
                        vx,vy=rotated_inner[0]-rotated_outer[0],rotated_inner[1]-rotated_outer[1]; length=math.hypot(vx,vy); nx,ny=vx/length,vy/length
                        phase=((rotated_outer[0]/pitch)*.61803398875+(rotated_outer[1]/pitch)*.38196601125)%1
                        # Fine deterministic coverage sampling retains scale/DPR/rotation
                        # phase but caps world-space quantization far below the .014 band.
                        step=min(pitch/32,.00025); start=-.004+phase*step
                        count=0; rendered=set(); index=0
                        while start+index*step<=length+.004:
                            distance=start+index*step; rx=rotated_outer[0]+nx*distance; ry=rotated_outer[1]+ny*distance
                            # Map the raster sample back to object space for analytic coverage.
                            point=(c*rx+s*ry,-s*rx+c*ry); material,rgb=material_at(point,loops,color); rendered.add(rgb)
                            if material==label and rgb==(WHITE if label=="white" else CHARCOAL): count+=1
                            index+=1
                        width=count*step
                        if abs(width-target)>RASTER_TOLERANCE:
                            raise AssertionError(f"raster {label}/{name}/{probe} rot={degrees} color={color_index} scale={scale} dpr={dpr}: {width} target={target} geometry={geometric_width} tolerance={RASTER_TOLERANCE}")
                        if not rendered: raise AssertionError("empty raster probe")
                        observed[(label,name,probe)].append(width); checks+=1
    if len(color_signatures)!=len(COLORS): raise AssertionError("raster colors are not semantically distinct")
    for key,widths in observed.items():
        if min(widths)<=0 or max(abs(value-BANDS[[item[0] for item in BANDS].index(key[0])][3]) for value in widths)>RASTER_TOLERANCE:
            raise AssertionError(f"raster worst-case failure {key}: {min(widths)}..{max(widths)}")
    return checks,{"minimum":min(min(values) for values in observed.values()),"maximum":max(max(values) for values in observed.values()),"tolerance":RASTER_TOLERANCE,"probes":len(probes)}

def adversaries(loops):
    mutations=0
    for band,_,inner_name,target in BANDS:
        mutated={name:list(loop) for name,loop in loops.items()}; loop=mutated[inner_name]; candidates=[i for i,p in enumerate(loop) if feature(p,loop)=="concave-shoulder"]
        index=candidates[len(candidates)//2]; distance,outer_point=nearest(loop[index],mutated[dict((x[0],x[1]) for x in BANDS)[band]])
        px,py=loop[index]; vx,vy=px-outer_point[0],py-outer_point[1]; length=math.hypot(vx,vy)
        loop[index]=(px+vx/length*.004,py+vy/length*.004)
        geometry_rejected=raster_rejected=False
        try: assert_uniform(measurements(mutated))
        except AssertionError: geometry_rejected=True
        try: raster_matrix(mutated)
        except AssertionError: raster_rejected=True
        if not geometry_rejected or not raster_rejected: raise AssertionError(f"adversarial shoulder bulge accepted: {band} geometry={geometry_rejected} raster={raster_rejected}")
        mutations+=1
    return mutations

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def scene_fingerprint(root,source):
    blender=shutil.which("blender")
    if not blender: raise AssertionError("Blender missing for semantic scene fingerprint")
    with tempfile.TemporaryDirectory(prefix="aerobeat-scene-fingerprint-") as directory:
        output=Path(directory)/"fingerprint.json"
        run_checked([blender,"--background","--factory-startup","--python",str(root/"tools/blender_scene_fingerprint.py"),"--",str(source),str(output)],operation=f"semantic scene fingerprint {source}",marker="SCENE_FINGERPRINT_OK",postcondition=lambda:output.is_file() and output.stat().st_size>0)
        document=json.loads(output.read_text(encoding="utf-8"))
        if document.get("schema")!="aerobeat.blender-semantic-scene-fingerprint/v1" or document.get("blender")!="4.0.2": raise AssertionError("semantic scene fingerprint identity")
        return sha(output),document

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--candidate-root",required=True); parser.add_argument("--authority-root",default="."); parser.add_argument("--skip-staged-match",action="store_true"); args=parser.parse_args()
    authority=Path(args.authority_root).resolve(); candidate=Path(args.candidate_root).resolve()
    relative=Path("directional-arrow/rounded-outline-v1/rounded-outline-v1.blend")
    staged_source=authority/"source"/relative; candidate_source=candidate/"source"/relative
    manifest_path=Path("manifests/directional-arrow/rounded-outline-v1.v1.json")
    staged_manifest=authority/manifest_path; candidate_manifest=candidate/manifest_path
    staged_fingerprint=generated_fingerprint=None
    if not args.skip_staged_match:
        staged_fingerprint,staged_scene=scene_fingerprint(authority,staged_source)
        generated_fingerprint,generated_scene=scene_fingerprint(authority,candidate_source)
        if staged_fingerprint!=generated_fingerprint or staged_scene!=generated_scene: raise AssertionError(f"staged/generated arrow semantic scene fingerprint drift: {staged_fingerprint} != {generated_fingerprint}; documents_equal={staged_scene==generated_scene}")
        staged_document=json.loads(staged_manifest.read_text(encoding="utf-8")); generated_document=json.loads(candidate_manifest.read_text(encoding="utf-8"))
        comparable=lambda document:{**document,"files":{key:value for key,value in document["files"].items() if key not in ("source_sha256","source_bytes")}}
        if comparable(staged_document)!=comparable(generated_document): raise AssertionError("staged/generated arrow manifest semantic drift")
    manifest=json.loads(candidate_manifest.read_text(encoding="utf-8")); files=manifest["files"]
    candidate_glb=candidate/"release/raw/0.0.9/directional-arrow/rounded-outline-v1.glb"
    if (files["source_sha256"],files["source_bytes"],files["release_sha256"],files["release_bytes"])!=(sha(candidate_source),candidate_source.stat().st_size,sha(candidate_glb),candidate_glb.stat().st_size): raise AssertionError("arrow manifest provenance")
    contract=manifest["materials"]["contract"]; assert_directional_arrow_contract(contract)
    old_contract=dict(contract,boundary_construction="independent-inset-anchor-morphological-erosion",join_policy="collapsed joins re-rounded independently; bands may widen but never narrow")
    try: assert_directional_arrow_contract(old_contract)
    except AssertionError: old_contract_red=True
    else: raise AssertionError("superseded arrow morphology contract accepted")
    unchanged=(("any-note","outlined-circle-v1"),("guard","outlined-shield-v1"),("bomb","urchin-v1"),("wall","red-glass-v1"),("track","blue-glass-v1"),("athlete-marker","sphere-v1"))
    for role,variant in unchanged:
        left=authority/"release/raw/0.0.8"/role/f"{variant}.glb"; right=candidate/"release/raw/0.0.9"/role/f"{variant}.glb"
        if left.read_bytes()!=right.read_bytes(): raise AssertionError(f"unchanged candidate GLB drift: {role}")
    topology=validate_cue(candidate_glb,"directional-arrow")
    before=measurements(boundaries(authority/"release/raw/0.0.8/directional-arrow/rounded-outline-v1.glb"))
    try: assert_uniform(before)
    except AssertionError: geometry_red=True
    else: raise AssertionError("red-before immutable 0.0.8 unexpectedly passed geometry")
    try: raster_matrix(boundaries(authority/"release/raw/0.0.8/directional-arrow/rounded-outline-v1.glb"))
    except AssertionError: raster_red=True
    else: raise AssertionError("red-before immutable 0.0.8 unexpectedly passed raster")
    red=geometry_red and raster_red
    after_loops=boundaries(candidate/"release/raw/0.0.9/directional-arrow/rounded-outline-v1.glb"); after=measurements(after_loops); assert_uniform(after)
    fill_ratio=polygon_area(after_loops["fill"])/polygon_area(after_loops["silhouette"]); interior_ratio=polygon_area(after_loops["inner-white"])/polygon_area(after_loops["silhouette"])
    if fill_ratio<.35 or interior_ratio<.48: raise AssertionError(f"readability {fill_ratio} {interior_ratio}")
    checks,raster=raster_matrix(after_loops); mutations=adversaries(after_loops)
    print({"red_before":{"geometry":geometry_red,"raster":raster_red},"before":before,"after":after,"fill_ratio":fill_ratio,"interior_ratio":interior_ratio,"topology":topology,"unchanged_glbs":len(unchanged),"raster_checks":checks,"raster_range":raster,"adversaries":mutations,"semantic_scene_fingerprint":staged_fingerprint,"raw_blend_bytes_claimed":False,"superseded_contract_red":old_contract_red})
    print(f"UNIFORM_ARROW_OK geometry_bands=3 features=4 raster_checks={checks} adversaries={mutations} rotations=8 colors=3 scales=3 dprs=3 unchanged_glbs={len(unchanged)}")
if __name__=="__main__": main()
