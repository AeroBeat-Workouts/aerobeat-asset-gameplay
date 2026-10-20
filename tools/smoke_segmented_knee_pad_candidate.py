#!/usr/bin/env python3
"""Smoke import wearable pad source/GLB in Blender 4.0.2."""
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
mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not mesh or any(not obj.data.polygons for obj in mesh):
    raise RuntimeError('Mesh geometry missing on import')
required = {'mat/shell_white', 'mat/padded_gray', 'mat/strap_gray',
            'mat/glove_match_tint', 'mat/front_blue_light'}
actual = {m.name for obj in mesh for m in obj.data.materials if m}
if actual != required:
    raise RuntimeError(f'Expected only five analytic pad materials, got {actual}')
if kind == 'source' and any(
    tuple(round(n, 6) for n in obj.rotation_euler) != (0, 0, 0) or
    tuple(round(n, 6) for n in obj.scale) != (1, 1, 1) for obj in mesh):
    raise RuntimeError('Source mesh transform is not identity')
print(f'SEGMENTED_PAD_SMOKE_OK {kind}')
