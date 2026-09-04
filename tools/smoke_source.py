#!/usr/bin/env python3
"""Factory-open one editable Blender source and prove its canonical identity."""
import sys

import bpy

path, canonical = sys.argv[sys.argv.index("--") + 1 :]
bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
mesh_objects = [obj for obj in bpy.data.objects if obj.type == "MESH"]
if len(mesh_objects) != 1 or mesh_objects[0].name != canonical:
    raise RuntimeError(
        f"source canonical identity mismatch: {[obj.name for obj in mesh_objects]} != {canonical}"
    )
obj = mesh_objects[0]
if any(abs(value) > 1e-7 for value in obj.location):
    raise RuntimeError("source non-identity location")
if any(abs(value) > 1e-7 for value in obj.rotation_euler):
    raise RuntimeError("source non-identity rotation")
if any(abs(value - 1) > 1e-7 for value in obj.scale):
    raise RuntimeError("source non-identity scale")
if not obj.data.polygons or not obj.data.materials:
    raise RuntimeError("source mesh/material inventory is empty")
if canonical == "athlete-marker/sphere-v1":
    if len(obj.data.polygons) != 168 or len(obj.data.vertices) != 86 or len(obj.data.materials) != 3:
        raise RuntimeError("source marker exact mesh/material counts failed")
    polygon_dots = [polygon.normal.dot(polygon.center) for polygon in obj.data.polygons]
    vertex_dots = [vertex.normal.dot(vertex.co.normalized()) for vertex in obj.data.vertices]
    if min(polygon_dots) <= 1e-5 or min(vertex_dots) <= .99:
        raise RuntimeError(f"source marker normals are not outward: polygon={min(polygon_dots)} vertex={min(vertex_dots)}")
    if any(not material.use_backface_culling for material in obj.data.materials):
        raise RuntimeError("source marker backface culling is disabled")
if bpy.data.images or bpy.data.fonts or bpy.data.libraries or bpy.data.cameras or bpy.data.actions:
    raise RuntimeError("source contains forbidden external/runtime datablocks")
print(f"SMOKE_OK kind=source identity={canonical}")
