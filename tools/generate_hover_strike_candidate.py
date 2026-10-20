#!/usr/bin/env python3
"""Generate one original, isolated floating knee-strike target candidate.

Blender 4.0.2. Pass --output-root to a NEW empty absolute directory. The art
is analytic mesh/material only; no concept pixels, brand text or person.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from knee_mesh_order import canonicalize_all
from knee_png_metadata import normalize_png

cli = argparse.ArgumentParser()
cli.add_argument('--output-root', required=True, type=Path)
arguments = cli.parse_args(sys.argv[sys.argv.index('--') + 1:])
if not arguments.output_root.is_absolute():
    raise RuntimeError('output-root must be absolute')
root = arguments.output_root.resolve()
if root == Path.cwd().resolve() or {'release', 'review'} & set(root.parts):
    raise RuntimeError('Never write canonical release or review trees')
if root.exists() and any(root.iterdir()):
    raise RuntimeError('Output root is not empty; existing candidates must be preserved')
if bpy.app.version_string != '4.0.2':
    raise RuntimeError('Blender 4.0.2 required')
variant = 'hover-shell-strike-v1'
base = root / 'knee-target' / variant
views = base / 'views'
views.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def mat(name, rgb, tint=False, alpha=1.0, emit=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, alpha)
    m.use_nodes = True
    m.use_backface_culling = True
    shader = m.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = .37
    shader.inputs['Metallic'].default_value = .11
    if alpha < 1:
        m.blend_method = 'BLEND'
        m.use_nodes = True
        shader.inputs['Alpha'].default_value = alpha
    if emit:
        shader.inputs['Emission Color'].default_value = (*rgb, 1)
        shader.inputs['Emission Strength'].default_value = emit
    m['aerobeat'] = {'runtimeTintable': tint, 'structural': not tint}
    return m

white = mat('mat/shell_white', (.89, .94, .98))
charcoal = mat('mat/shadow_charcoal', (.045, .090, .14))
cyan = mat('mat/cyan_rim', (.075, .88, .97), alpha=.82, emit=.35)
strike = mat('mat/strike_lime', (.72, .99, .075), emit=.65)


def ellipsoid(name, pos, radius, material, segments=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.scale = radius
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    for face in ob.data.polygons:
        face.use_smooth = True
    return ob


def band(name, pts, material, thickness, closed=True):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = thickness
    data.bevel_resolution = 2
    data.resolution_u = 1
    line = data.splines.new('POLY')
    line.points.add(len(pts) - 1)
    for vertex, pos in zip(line.points, pts):
        vertex.co = (*pos, 1)
    line.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob.data.materials.append(material)
    return ob

# White top is seen from +Z (toward the distant approach camera); the bright
# impact underside is on -Y. This is a FLOATING BEAT TARGET, not a strap-on pad.
# In front elevation, a white low dome crowns a thick cyan horizontal lip;
# lime underside remains a large visible lower segment even at small sizes.
# Contrasting large regions, not micro lighting lines, carry recognition.
ellipsoid('floating white rounded upper shell', (0, .109, -.047), (.285, .181, .148), white)
ellipsoid('dark seam between shell and strike face', (0, -.033, -.052), (.283, .058, .151), charcoal)
ellipsoid('cyan broad perimeter lip', (0, -.062, -.055), (.311, .079, .161), cyan, 40, 12)
ellipsoid('downward-facing lime impact underside', (0, -.132, -.073), (.250, .115, .174), strike, 32, 16)
# A white top cap remains wide and unmarked; no fonts, markings or labels.
# The lime face projects below the crown, with cyan rim outlining it.
pts = []
for i in range(48):
    theta = 2 * math.pi * i / 48
    pts.append((.277 * math.cos(theta), -.070 + .047 * math.sin(theta),
                -.166 + .015 * math.sin(theta)))
band('bright cyan lip edge', pts, cyan, .012)

mesh = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH']
canonicalize_all(mesh)
triangles = 0
for ob in mesh:
    ob.data.calc_loop_triangles()
    triangles += len(ob.data.loop_triangles)
if not mesh or triangles > 5000:
    raise RuntimeError(f'Unexpected triangle count {triangles}')
coords = [ob.matrix_world @ vertex.co for ob in mesh for vertex in ob.data.vertices]
bounds = [[round(min(v[i] for v in coords), 5) for i in range(3)],
          [round(max(v[i] for v in coords), 5) for i in range(3)]]

world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.055, .095, .155, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
for label, xyz, energy, size in [('front softbox', (-2.1, 3.0, -2.5), 470, 2.5),
                                 ('rear fill', (1.8, 1.0, 2.4), 290, 2.3)]:
    bpy.ops.object.light_add(type='AREA', location=xyz)
    lamp = bpy.context.object
    lamp.name = label
    lamp.data.energy = energy
    lamp.data.size = size
bpy.ops.object.camera_add(location=(0, 0, -4))
camera = bpy.context.object
camera.name = 'review camera'
camera.data.type = 'ORTHO'
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.cycles.seed = 12
scene.cycles.use_animated_seed = False
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'

bpy.ops.wm.save_as_mainfile(filepath=str(base / (variant + '.blend')), compress=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in mesh:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(base / (variant + '.glb')),
    export_format='GLB', use_selection=True, export_apply=False, export_yup=True,
    export_extras=True, export_materials='EXPORT', export_normals=True,
    export_texcoords=False)


def render(label, xyz, scale=1.1):
    camera.location = xyz
    camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    scene.render.filepath = str(views / (label + '.png'))
    bpy.ops.render.render(write_still=True)
    normalize_png(views / (label + '.png'))

# Camera deliberately lower for front/three-quarter, so the *underside*
# impact face is visible rather than hidden by a straight-on top view.
for name, xyz in [('front', (0, -.75, 4)), ('side', (4, -.55, 0)),
                  ('back', (0, -.75, -4)), ('underside', (0, -4, -.8)),
                  ('three-quarter', (2.7, -1.75, 3.0))]:
    render(name, xyz)
for size in (32, 64):
    render(f'approach-{size}px', (0, -.75, 4), .66 * 640 / size)

files = {}
for path in sorted(base.rglob('*')):
    if path.is_file():
        files[str(path.relative_to(base))] = {
            'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
manifest = {
    'status': 'UNAPPROVED_CANDIDATE', 'identity': {'role': 'knee-target', 'variant': variant},
    'blender_version': bpy.app.version_string,
    'coordinates': '+Y up, forward -Z; review camera sees white upper shell from +Z and -Y underside',
    'geometry': {'triangle_count': triangles, 'triangle_budget': 5000, 'measured_aabb': bounds},
    'materials': {'names': sorted({m.name for ob in mesh for m in ob.data.materials}),
                  'runtime_tintable': [], 'texture_dependencies': [],
                  'note': 'lime strike face fixed contrast; cyan analytic blend, no texture'},
    'source': 'original local procedural primitives; no copied concept image/text/person',
    'rights': 'Original AeroBeat/Gambit Games art, CC BY-NC 4.0',
    'files': files,
}
(base / 'candidate-manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
print(f'HOVER_STRIKE_CANDIDATE {variant} triangles={triangles} aabb={bounds}')
print('HOVER_STRIKE_CANDIDATE_OK')
