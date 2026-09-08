#!/usr/bin/env python3
"""Write a deterministic semantic fingerprint document for one Blender scene.

The .blend container itself is intentionally not a reproducibility authority: Blender
may embed nondeterministic save metadata. This tool fingerprints the authored scene
state that can affect editable identity and generated geometry/material output.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import bpy


def scalar(value):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value.hex()
    if hasattr(value, "to_list"):
        return scalar(value.to_list())
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): scalar(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)) or hasattr(value, "__iter__"):
        return [scalar(item) for item in value]
    return str(value)


def properties(owner):
    return {key: scalar(owner[key]) for key in sorted(owner.keys()) if key != "_RNA_UI"}


def matrix(value):
    return [[float(cell).hex() for cell in row] for row in value]


def socket_value(socket):
    if not hasattr(socket, "default_value"):
        return None
    try:
        return scalar(socket.default_value)
    except (TypeError, ValueError):
        return None


def node_tree(tree):
    if tree is None:
        return None
    nodes=[]
    for node in sorted(tree.nodes, key=lambda item: item.name):
        nodes.append({
            "name":node.name,
            "type":node.bl_idname,
            "label":node.label,
            "location":scalar(tuple(node.location)),
            "width":float(node.width).hex(),
            "mute":bool(node.mute),
            "hide":bool(node.hide),
            "properties":properties(node),
            "inputs":[{"name":item.name,"identifier":item.identifier,"default":socket_value(item)} for item in node.inputs],
            "outputs":[{"name":item.name,"identifier":item.identifier,"default":socket_value(item)} for item in node.outputs],
        })
    links=sorted((link.from_node.name,link.from_socket.identifier,link.to_node.name,link.to_socket.identifier) for link in tree.links)
    return {"nodes":nodes,"links":[list(item) for item in links],"properties":properties(tree)}


def material_document(material):
    return {
        "name":material.name,
        "diffuse_color":scalar(tuple(material.diffuse_color)),
        "metallic":float(material.metallic).hex(),
        "roughness":float(material.roughness).hex(),
        "use_backface_culling":bool(material.use_backface_culling),
        "surface_render_method":getattr(material,"surface_render_method",None),
        "use_nodes":bool(material.use_nodes),
        "node_tree":node_tree(material.node_tree) if material.use_nodes else None,
        "properties":properties(material),
    }


def mesh_document(mesh):
    mesh.calc_loop_triangles()
    return {
        "name":mesh.name,
        "vertices":[{"co":scalar(tuple(item.co))} for item in mesh.vertices],
        "edges":[{"vertices":list(item.vertices),"sharp":bool(getattr(item,"use_edge_sharp",False))} for item in mesh.edges],
        "loops":[{"vertex_index":item.vertex_index} for item in mesh.loops],
        "has_custom_normals":bool(mesh.has_custom_normals),
        "polygons":[{
            "vertices":list(item.vertices),
            "loop_indices":list(item.loop_indices),
            "material_index":item.material_index,
            "use_smooth":bool(item.use_smooth),
        } for item in mesh.polygons],
        "loop_triangles":[{"vertices":list(item.vertices),"loops":list(item.loops),"polygon_index":item.polygon_index} for item in mesh.loop_triangles],
        "materials":[item.name if item else None for item in mesh.materials],
        "uv_layers":[{"name":layer.name,"active_render":bool(layer.active_render),"data":[scalar(tuple(item.uv)) for item in layer.data]} for layer in mesh.uv_layers],
        "color_attributes":[{"name":item.name,"domain":item.domain,"data_type":item.data_type} for item in mesh.color_attributes],
        "properties":properties(mesh),
    }


def object_document(obj):
    modifiers=[]
    for modifier in obj.modifiers:
        values={}
        for prop in modifier.bl_rna.properties:
            if prop.identifier in {"rna_type","name","type"} or prop.is_readonly:
                continue
            try:
                value=getattr(modifier,prop.identifier)
                if isinstance(value,(str,bool,int,float)) or hasattr(value,"to_list"):
                    values[prop.identifier]=scalar(value)
            except (AttributeError,TypeError,ValueError):
                pass
        modifiers.append({"name":modifier.name,"type":modifier.type,"values":values})
    return {
        "name":obj.name,
        "type":obj.type,
        "data":obj.data.name if obj.data else None,
        "parent":obj.parent.name if obj.parent else None,
        "parent_type":obj.parent_type,
        "matrix_local":matrix(obj.matrix_local),
        "matrix_parent_inverse":matrix(obj.matrix_parent_inverse),
        "rotation_mode":obj.rotation_mode,
        "hide_render":bool(obj.hide_render),
        "hide_viewport":bool(obj.hide_viewport),
        "visible_camera":bool(obj.visible_camera),
        "material_slots":[slot.material.name if slot.material else None for slot in obj.material_slots],
        "modifiers":modifiers,
        "properties":properties(obj),
    }


def collection_document(collection):
    return {
        "name":collection.name,
        "objects":sorted(item.name for item in collection.objects),
        "children":sorted(item.name for item in collection.children),
        "hide_render":bool(collection.hide_render),
        "hide_viewport":bool(collection.hide_viewport),
        "properties":properties(collection),
    }


def scene_document(scene):
    unit=scene.unit_settings
    return {
        "name":scene.name,
        "frame_start":scene.frame_start,
        "frame_end":scene.frame_end,
        "frame_step":scene.frame_step,
        "unit_settings":{"system":unit.system,"scale_length":float(unit.scale_length).hex(),"length_unit":unit.length_unit},
        "camera":scene.camera.name if scene.camera else None,
        "world":scene.world.name if scene.world else None,
        "root_collection":scene.collection.name,
        "objects":sorted(item.name for item in scene.objects),
        "properties":properties(scene),
    }


def main():
    args=sys.argv[sys.argv.index("--")+1:]
    if len(args)!=2:
        raise SystemExit("usage: blender ... -- <source.blend> <fingerprint.json>")
    source,output=map(Path,args)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    document={
        "schema":"aerobeat.blender-semantic-scene-fingerprint/v1",
        "blender":".".join(str(item) for item in bpy.app.version),
        "derived_load_normals":"excluded as recalculated scheduling-dependent values; custom-normal presence is fingerprinted and runtime GLB normals remain byte-exact",
        "scenes":[scene_document(item) for item in sorted(bpy.data.scenes,key=lambda value:value.name)],
        "collections":[collection_document(item) for item in sorted(bpy.data.collections,key=lambda value:value.name)],
        "objects":[object_document(item) for item in sorted(bpy.data.objects,key=lambda value:value.name)],
        "meshes":[mesh_document(item) for item in sorted(bpy.data.meshes,key=lambda value:value.name)],
        "materials":[material_document(item) for item in sorted(bpy.data.materials,key=lambda value:value.name)],
        "worlds":[{"name":item.name,"color":scalar(tuple(item.color)),"use_nodes":bool(item.use_nodes),"node_tree":node_tree(item.node_tree) if item.use_nodes else None,"properties":properties(item)} for item in sorted(bpy.data.worlds,key=lambda value:value.name)],
        "actions":[{"name":item.name,"frame_range":scalar(tuple(item.frame_range)),"properties":properties(item)} for item in sorted(bpy.data.actions,key=lambda value:value.name)],
    }
    payload=(json.dumps(document,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode("utf-8")
    output.write_bytes(payload)
    print("SCENE_FINGERPRINT_OK")


if __name__=="__main__":
    main()
