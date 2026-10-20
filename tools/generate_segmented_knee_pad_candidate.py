#!/usr/bin/env python3
"""Original additive wearable pad candidate, Blender 4.0.2 only.

Run with --output-root /new/empty/absolute/root. One art mesh is instanced
for both legs in disposable render-only poses; no leg appears in its GLB.
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
cli.add_argument('--output-root', type=Path, required=True)
args = cli.parse_args(sys.argv[sys.argv.index('--') + 1:])
if not args.output_root.is_absolute():
    raise RuntimeError('Require absolute output-root')
root = args.output_root.resolve()
if root == Path.cwd().resolve() or {'release', 'review'} & set(root.parts):
    raise RuntimeError('Do not generate into canonical release/review')
if root.exists() and any(root.iterdir()):
    raise RuntimeError('Output root must be new/empty; preserve prior candidates')
if bpy.app.version_string != '4.0.2':
    raise RuntimeError('Blender 4.0.2 required')
variant = 'segmented-lightwrap-v1'
base = root / 'knee-pad' / variant
views = base / 'views'
views.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, rgb, tint=False, opacity=1.0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, opacity)
    m.use_nodes = True
    m.use_backface_culling = True
    shader = m.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Metallic'].default_value = .16
    shader.inputs['Roughness'].default_value = .37
    if opacity < 1:
        m.blend_method = 'BLEND'
        shader.inputs['Alpha'].default_value = opacity
    if emission:
        shader.inputs['Emission Color'].default_value = (*rgb, 1)
        shader.inputs['Emission Strength'].default_value = emission
    m['aerobeat'] = {'runtimeTintable': tint, 'structural': not tint}
    return m

white = material('mat/shell_white', (.84, .90, .97))
gray = material('mat/padded_gray', (.24, .29, .36))
strap = material('mat/strap_gray', (.16, .20, .27))
tint = material('mat/glove_match_tint', (.04, .67, .98), tint=True, opacity=.88, emission=.19)
light = material('mat/front_blue_light', (.18, .80, 1), emission=.55)


def sphere(name, pos, radii, mat, segments=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    for face in ob.data.polygons:
        face.use_smooth = True
    return ob


def cube(name, pos, dims, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        ob.data.use_auto_smooth = True
        mod = ob.modifiers.new('physical rounded edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob


def line(name, points, mat, width, cyclic=False):
    c = bpy.data.curves.new(name, 'CURVE')
    c.dimensions = '3D'
    c.resolution_u = 1
    c.bevel_depth = width
    c.bevel_resolution = 2
    s = c.splines.new('POLY')
    s.points.add(len(points) - 1)
    for p, xyz in zip(s.points, points):
        p.co = (*xyz, 1)
    s.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    ob.data.materials.append(mat)
    return ob


# Leg center is an *empty* local tunnel. +Y up, shell faces incoming -Z.
# Side bolsters and two rear straps wrap the leg, leaving center rear open.
for x in (-.205, .205):
    sphere('soft leg-side wrap', (x, 0, .022), (.064, .306, .106), gray, 16, 8)
for y in (-.255, .255):
    cube('wide adjustable rear strap', (0, y, .160), (.44, .099, .035), strap, .014)
    for x in (-.224, .224):
        cube('white strap buckle', (x, y, .054), (.052, .116, .172), white, .010)
# Segmented white shell: three separate curved plates, generous gaps show
# colored underplate and a circular BLUE center. Do not copy concept geometry.
for x in (-.132, .132):
    sphere('side color accent beneath white frame', (x, .015, -.113), (.055, .240, .050), tint, 16, 8)
sphere('white central protective plate', (0, .014, -.152), (.123, .209, .059), white, 20, 10)
sphere('upper segmented white cap', (0, .207, -.145), (.214, .076, .062), white, 20, 10)
sphere('lower segmented white cap', (0, -.200, -.144), (.192, .069, .065), white, 20, 10)
for x in (-.200, .200):
    sphere('split white side plate', (x, .004, -.144), (.051, .178, .062), white, 20, 10)
    sphere('cyan side inset', (x * 1.06, .012, -.186), (.024, .143, .038), tint, 20, 10)
# Two long mirrored S-shaped rails intentionally stop short of the circular
# center light, leaving it legible against the white plate and tinted field.
for sign in (-1, 1):
    pts = []
    for i in range(17):
        t = i / 16
        y = .210 - .42 * t
        x = sign * (.115 + .055 * math.sin(math.pi * 1.55 * t))
        z = -.184 - .012 * math.sin(math.pi * t)
        pts.append((x, y, z))
    line('glove-color S curve', pts, tint, .014)
sphere('round white light bezel', (0, 0, -.214), (.106, .106, .031), white, 24, 10)
sphere('round blue frontal indicator', (0, 0, -.250), (.079, .079, .021), light, 24, 10)

mesh = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH']
canonicalize_all(mesh)
tris = 0
for ob in mesh:
    ob.data.calc_loop_triangles()
    tris += len(ob.data.loop_triangles)
if not 0 < tris <= 7000:
    raise RuntimeError(f'Provisional triangle count invalid: {tris}')
coords = [ob.matrix_world @ vertex.co for ob in mesh for vertex in ob.data.vertices]
aabb = [[round(min(v[i] for v in coords), 5) for i in range(3)],
        [round(max(v[i] for v in coords), 5) for i in range(3)]]

world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.095, .14, .21, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
for name, xyz, power, size in [('front softbox', (-2.2, 3.1, -2.6), 530, 3),
                                ('rear fill', (2, 1.4, 2.2), 280, 2.5)]:
    bpy.ops.object.light_add(type='AREA', location=xyz)
    bpy.context.object.name = name
    bpy.context.object.data.energy = power
    bpy.context.object.data.size = size
bpy.ops.object.camera_add(location=(0, 0, -4))
camera = bpy.context.object
camera.name = 'review camera'
camera.data.type = 'ORTHO'
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
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
bpy.ops.export_scene.gltf(filepath=str(base / (variant + '.glb')), export_format='GLB',
    use_selection=True, export_apply=False, export_yup=True, export_extras=True,
    export_materials='EXPORT', export_normals=True, export_texcoords=False)


def render(label, xyz, focus=(0, 0, 0), scale=1.14):
    camera.location = xyz
    camera.rotation_euler = (Vector(focus) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    scene.render.filepath = str(views / (label + '.png'))
    bpy.ops.render.render(write_still=True)
    normalize_png(views / (label + '.png'))

for name, xyz in [('front', (0, 0, -4)), ('side', (4, 0, 0)),
                  ('back', (0, 0, 4)), ('three-quarter', (2.6, .8, -3.2))]:
    render(name, xyz)

# Review-only leg stand-ins: untextured analytic cylinders; not modeled into
# the pad source/GLB, not evidence of body tracking or physical ergonomics.
legmat = material('review/neutral_leg_only', (.48, .52, .56))
leg_objects = []
for sign in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=.10, depth=1.65,
                                         location=(sign * .44, 0, .12), rotation=(math.pi / 2, 0, 0))
    ob = bpy.context.object
    ob.name = f'review-only {"left" if sign < 0 else "right"} leg cylinder'
    ob.data.materials.append(legmat)
    leg_objects.append(ob)
# To prove single geometry instanced twice, duplicate each mesh as a linked
# instance, parent to separate pose roots; only material slot tint differs.
pad_roots = []
for sign in (-1, 1):
    parent = bpy.data.objects.new('review-only pad left' if sign < 0 else 'review-only pad right', None)
    bpy.context.collection.objects.link(parent)
    parent.location.x = sign * .44
    pad_roots.append(parent)
    for ob in mesh:
        instance = ob.copy()
        instance.data = ob.data.copy()
        bpy.context.collection.objects.link(instance)
        instance.parent = parent
        instance.matrix_parent_inverse.identity()
        if sign > 0:
            for index, original in enumerate(instance.data.materials):
                if original and original.name == 'mat/glove_match_tint':
                    second = tint.copy()
                    second.name = 'review/right glove color'
                    shader = second.node_tree.nodes['Principled BSDF']
                    shader.inputs['Base Color'].default_value = (.87, .15, .58, 1)
                    shader.inputs['Emission Color'].default_value = (.87, .15, .58, 1)
                    instance.data.materials[index] = second
        instance.hide_render = False
for ob in mesh:
    ob.hide_render = True

def pose(label, tint_left, tint_right, raised):
    # Color pair A=cyan/magenta; pair B=yellow/lime vs royal blue.
    shader = tint.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*tint_left, 1)
    shader.inputs['Emission Color'].default_value = (*tint_left, 1)
    for parent in pad_roots:
        for child in parent.children:
            for material in child.data.materials:
                if material and material.name.startswith('review/right glove color'):
                    sh = material.node_tree.nodes['Principled BSDF']
                    sh.inputs['Base Color'].default_value = (*tint_right, 1)
                    sh.inputs['Emission Color'].default_value = (*tint_right, 1)
    for i, parent in enumerate(pad_roots):
        parent.location = ((i * 2 - 1) * .44, .0 if not raised else .17, 0 if not raised else -.18)
        parent.rotation_euler = (0 if not raised else -.48, 0, 0)
        leg_objects[i].location = ((i * 2 - 1) * .44, .0 if not raised else .17, .12 if not raised else -.18)
        leg_objects[i].rotation_euler = (math.pi / 2 if not raised else math.pi / 2 - .48, 0, 0)
    render(label + '-front', (0, .7, -4), scale=2.1)
    render(label + '-side', (4, .7, -1.5), scale=2.1)
    render(label + '-back', (0, .7, 4), scale=2.1)

pose('lowered-pair-a', (.04, .67, .98), (.87, .15, .58), False)
pose('raised-pair-a', (.04, .67, .98), (.87, .15, .58), True)
pose('lowered-pair-b', (.91, .82, .06), (.15, .38, .99), False)
pose('raised-pair-b', (.91, .82, .06), (.15, .38, .99), True)

files = {}
for path in sorted(base.rglob('*')):
    if path.is_file():
        files[str(path.relative_to(base))] = {'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
manifest = {
    'status': 'UNAPPROVED_CANDIDATE', 'identity': {'role': 'knee-pad', 'variant': variant},
    'blender_version': bpy.app.version_string,
    'coordinates': '+Y up, local forward -Z, pad front faces incoming -Z',
    'geometry': {'triangle_count': tris, 'triangle_budget': 7000, 'measured_aabb': aabb},
    'materials': {'runtime_tintable': ['mat/glove_match_tint'],
                  'names': sorted({m.name for ob in mesh for m in ob.data.materials}),
                  'textures': [], 'external_dependencies': []},
    'reuse': 'one equipment mesh intended for left/right knee instances; song glove colors per instance',
    'reviews': 'paired lowered/raised leg cylinders are illustrative review-only, excluded from GLB and blend',
    'rights': 'Original procedural AeroBeat/Gambit Games work; CC BY-NC 4.0',
    'files': files,
}
(base / 'candidate-manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
print(f'SEGMENTED_PAD_CANDIDATE {variant} triangles={tris} aabb={aabb}')
print('SEGMENTED_PAD_CANDIDATE_OK')
