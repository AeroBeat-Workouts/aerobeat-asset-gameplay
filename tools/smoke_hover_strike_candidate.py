#!/usr/bin/env python3
"""Blender 4.0.2 source/GLB import check for the fixed-color strike target."""
import sys
from pathlib import Path
import bpy

kind, filename = sys.argv[sys.argv.index('--') + 1:]
if bpy.app.version_string != '4.0.2':
    raise RuntimeError('Blender 4.0.2 required')
path = Path(filename)
if kind == 'source':
    bpy.ops.wm.open_mainfile(filepath=str(path))
else:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(path))
mesh = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH']
if not mesh or any(not ob.data.polygons for ob in mesh):
    raise RuntimeError('Missing mesh polygons')
materials = {m.name for ob in mesh for m in ob.data.materials if m}
required = {'mat/shell_white', 'mat/shadow_charcoal', 'mat/cyan_rim', 'mat/strike_lime'}
if materials != required:
    raise RuntimeError(f'Unexpected material set: {materials}')
if kind == 'source' and any(
    tuple(round(v, 6) for v in ob.rotation_euler) != (0, 0, 0) or
    tuple(round(v, 6) for v in ob.scale) != (1, 1, 1) for ob in mesh
):
    raise RuntimeError('Source mesh transforms must be identity')
print(f'HOVER_STRIKE_SMOKE_OK {kind}')
