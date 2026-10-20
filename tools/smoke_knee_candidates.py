#!/usr/bin/env python3
"""Smoke import a knee source or GLB inside Blender 4.0.2."""
import sys
from pathlib import Path
import bpy

kind, file, role, variant = sys.argv[sys.argv.index('--') + 1:]
if bpy.app.version_string != '4.0.2':
    raise RuntimeError('Wrong Blender version')
path = Path(file)
if kind == 'source':
    bpy.ops.wm.open_mainfile(filepath=str(path))
else:
    bpy.ops.import_scene.gltf(filepath=str(path))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
if not meshes or any(not obj.data.polygons for obj in meshes):
    raise RuntimeError('Missing imported geometry')
materials = {mat.name for obj in meshes for mat in obj.data.materials if mat}
required = {'mat/knee_tint'} if role == 'knee-pad' else {'mat/target_tint'}
if not required <= materials:
    raise RuntimeError(f'Missing tint material: {materials}')
if kind == 'source':
    if any(tuple(round(v, 6) for v in obj.rotation_euler) != (0, 0, 0) or
           tuple(round(v, 6) for v in obj.scale) != (1, 1, 1) for obj in meshes):
        raise RuntimeError('Nonidentity source object rotation or scale')
print(f'KNEE_SMOKE_OK {kind} {role}/{variant}')
