#!/usr/bin/env python3
"""Make one ADDITIVE provisional turtle-shell-and-strap knee strike target.

Blender 4.0.2 only. An empty absolute output root is required; the only identity
created is knee-target/turtle-shell-strap-v1. Never writes existing candidates.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

cli = argparse.ArgumentParser()
cli.add_argument('--output-root', type=Path, required=True)
args = cli.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = args.output_root.resolve()
if (not args.output_root.is_absolute() or root == Path.cwd().resolve() or
        {'release', 'review'} & set(root.parts)):
    raise RuntimeError('Use a separate absolute candidate root, not a release/review path')
if bpy.app.version_string != '4.0.2':
    raise RuntimeError('Blender 4.0.2 required')
if root.exists() and any(root.iterdir()):
    raise RuntimeError('Candidate root must be empty: existing files stay untouched')
base = root / 'knee-target' / 'turtle-shell-strap-v1'
views = base / 'views'
views.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, rgb, tint=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    m.use_backface_culling = True
    shader = m.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = .43
    m['aerobeat'] = {'runtimeTintable': tint, 'structural': not tint}
    return m


shell = material('mat/target_tint', (.035, .66, .93), True)
edge = material('mat/white', (.84, .91, .97))
strap = material('mat/charcoal', (.025, .045, .078))


def cube(name, xyz, dims, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        obj.data.use_auto_smooth = True
        mod = obj.modifiers.new('rounded edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def ellipsoid(name, xyz, radii, mat, segments=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def polyline(name, points, radius, mat, closed=False):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for vertex, xyz in zip(spline.points, points):
        vertex.co = (*xyz, 1)
    spline.use_cyclic_u = closed
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    obj.data.materials.append(mat)
    return obj


# Local +Y up, incoming beats face -Z. No leg is modeled. The full front is
# ONE broad domed outer shell, not a ring/disc/pin or two raised prongs.
# Rear straps deliberately sit beyond the invisible leg's open back (+Z).
ellipsoid('one domed outer kneecap shield', (0, .017, -.126), (.278, .293, .104), shell)
# Thick white keyline follows a continuous rounded shell boundary in front.
edge_points = []
for i in range(48):
    angle = 2 * math.pi * i / 48
    x, y = .270 * math.cos(angle), .017 + .281 * math.sin(angle)
    # Perimeter is deliberately forward of the dome silhouette at its edge.
    edge_points.append((x, y, -.134 - .045 * max(0, 1 - (x / .278) ** 2)))
polyline('continuous shell trim', edge_points, .014, edge, True)
# A wide horizontal strap visibly crosses the shell BELOW its equator.
# It wraps behind the empty leg as a matching band, not a dangling icon tail.
cube('front cross-knee strap', (0, -.160, -.213), (.50, .076, .037), strap, .015)
cube('front strap reflective seam', (0, -.160, -.235), (.41, .010, .009), edge, .004)
cube('back of wraparound strap', (0, -.160, .162), (.50, .076, .040), strap, .015)
for x in (-.246, .246):
    cube('strap side return', (x, -.160, -.016), (.035, .076, .365), strap, .010)
    cube('strap clasp on side', (x * 1.075, -.160, -.085), (.024, .093, .084), edge, .007)
# Side contact padding floats against the empty leg without filling its rear.
for x in (-.176, .176):
    ellipsoid('leg-side padded bolsters', (x, .095, .075), (.053, .128, .050), strap, 16, 8)

mesh = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH']
triangles = 0
for obj in mesh:
    obj.data.calc_loop_triangles()
    triangles += len(obj.data.loop_triangles)
if triangles >= 5000:
    raise RuntimeError(f'Candidate geometry exceeds provisional budget: {triangles}')
coords = [obj.matrix_world @ vertex.co for obj in mesh for vertex in obj.data.vertices]
bounds = [[round(min(p[i] for p in coords), 5) for i in range(3)],
          [round(max(p[i] for p in coords), 5) for i in range(3)]]

world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.10, .16, .24, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
for name, xyz, energy, size in [('large softbox', (-2.4, 3.2, -3), 500, 3),
                                ('side fill', (2, 1, 2), 320, 2.5)]:
    bpy.ops.object.light_add(type='AREA', location=xyz)
    lamp = bpy.context.object
    lamp.name = name
    lamp.data.energy = energy
    lamp.data.size = size
bpy.ops.object.camera_add(location=(0, 0, -4))
camera = bpy.context.object
camera.name = 'review camera'
scene = bpy.context.scene
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.05
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

variant = 'turtle-shell-strap-v1'
bpy.ops.wm.save_as_mainfile(filepath=str(base / f'{variant}.blend'), compress=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in mesh:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(base / f'{variant}.glb'), export_format='GLB',
    use_selection=True, export_apply=False, export_yup=True, export_extras=True,
    export_materials='EXPORT', export_normals=True, export_texcoords=False)

def render(position, filename, size=1.05):
    camera.location = position
    camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = size
    scene.render.filepath = str(views / filename)
    bpy.ops.render.render(write_still=True)

for label, pos in [('front', (0, 0, -4)), ('side', (4, 0, 0)),
                   ('back', (0, 0, 4)), ('three-quarter', (2.8, 1.05, -3.5))]:
    render(pos, label + '.png')
for px in (32, 64):
    render((0, 0, -4), f'approach-{px}px.png', .72 * 640 / px)

files = {}
for path in sorted(base.rglob('*')):
    if path.is_file():
        files[str(path.relative_to(base))] = {
            'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
manifest = {
    'status': 'UNAPPROVED_CANDIDATE', 'role': 'knee-target', 'variant': variant,
    'coordinate_contract': '+Y up, local forward -Z, outer shell faces -Z',
    'source_object_rotation_scale': 'identity',
    'meaning': 'one kneecap shield and a front-to-back wraparound strap around an invisible leg',
    'materials': ['mat/charcoal', 'mat/target_tint', 'mat/white'],
    'runtime_tintable': ['mat/target_tint'], 'textures': [], 'external_dependencies': [],
    'bounds': bounds, 'triangles': triangles, 'blender_version': bpy.app.version_string,
    'rights': 'Original procedural AeroBeat/Gambit Games artwork; CC BY-NC 4.0',
    'files': files,
}
(base / 'candidate-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print(f'CANDIDATE knee-target/{variant}: {triangles} triangles {bounds}')
print('KNEE_SHELL_STRAP_OK')
