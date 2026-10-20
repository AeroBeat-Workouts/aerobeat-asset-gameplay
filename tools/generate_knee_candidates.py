#!/usr/bin/env python3
"""Generate isolated, unapproved knee artwork with Blender 4.0.2.

Usage: blender --background --factory-startup --python tools/generate_knee_candidates.py -- --output-root /absolute/candidate/root
Never writes canonical source, manifests, releases or reviews.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--output-root', type=Path, required=True)
args = parser.parse_args(__import__('sys').argv[__import__('sys').argv.index('--') + 1:])
root = args.output_root.resolve()
if not root.is_absolute() or root == Path.cwd().resolve() or 'release' in root.parts or 'review' in root.parts:
    raise RuntimeError('Use a separate absolute candidate root, not a canonical release/review directory')
if bpy.app.version_string != '4.0.2':
    raise RuntimeError('Blender 4.0.2 is required')
if root.exists() and any(root.iterdir()):
    raise RuntimeError('Candidate root must be new or empty; existing candidates are not overwritten')
root.mkdir(parents=True, exist_ok=True)

VIEWS = {'front': (0, 0, -4), 'side': (4, 0, 0), 'back': (0, 0, 4), 'three-quarter': (2.8, 1.05, -3.5)}


def material(name, rgb, tint=False, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    mat.use_backface_culling = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Metallic'].default_value = .18
    shader.inputs['Roughness'].default_value = .43
    if emission:
        shader.inputs['Emission Color'].default_value = (*rgb, 1)
        shader.inputs['Emission Strength'].default_value = emission
    mat['aerobeat'] = {'runtimeTintable': tint, 'structural': not tint}
    return mat


def assign(obj, mat, bevel=0):
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('rounded physical edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.data.use_auto_smooth = True
        mod = obj.modifiers.new('weighted corner normals', 'WEIGHTED_NORMAL')
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def cube(name, pos, scale, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return assign(obj, mat, bevel)


def sphere(name, pos, scale, mat, segments=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def torus(name, pos, major, minor, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=40, minor_segments=6, location=pos,
        rotation=rotation, major_radius=major, minor_radius=minor)
    obj = bpy.context.object
    obj.name = name
    return assign(obj, mat)


def curve_band(name, points, mat, radius=.010, cyclic=False):
    crv = bpy.data.curves.new(name, 'CURVE')
    crv.dimensions = '3D'
    crv.resolution_u = 1
    crv.bevel_depth = radius
    crv.bevel_resolution = 2
    path = crv.splines.new('POLY')
    path.points.add(len(points) - 1)
    for p, xyz in zip(path.points, points):
        p.co = (*xyz, 1)
    path.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, crv)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target='MESH')
    return assign(bpy.context.object, mat)


def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def pad():
    reset()
    charcoal = material('mat/charcoal', (.035, .055, .09))
    padding = material('mat/padding', (.20, .25, .32))
    white = material('mat/white', (.78, .84, .90))
    tint = material('mat/knee_tint', (.04, .62, .98), tint=True)
    # The invisible leg is centered at origin; the shield faces incoming -Z beats.
    # Two rear straps pass behind the invisible leg, instead of capping its open sides.
    # Open side pads do not occlude the rear strap opening for the invisible leg.
    for x in (-.205, .205):
        sphere('side padded bolster', (x, 0, .005), (.060, .304, .103), padding)
    sphere('domed turtle shield', (0, .018, -.143), (.242, .257, .116), tint, 32, 16)
    sphere('floating lower bumper', (0, -.236, -.114), (.205, .065, .058), white)
    for y in (-.27, .265):
        cube('rear wrap strap', (0, y, .128), (.423, .086, .036), charcoal, .014)
        for x in (-.20, .20):
            cube('strap side anchor', (x, y, .035), (.050, .098, .151), white, .015)
    for x in (-.24, .24):
        sphere('hinge button', (x, -.11, -.08), (.035, .056, .036), white, 16, 8)
    # Thin analytic trim frames the dome without competing with the tint field.
    points = [(math.cos(t * 2 * math.pi / 48) * .242,
               .018 + math.sin(t * 2 * math.pi / 48) * .264,
               -.150 - .043 * max(0, 1 - (math.cos(t * 2 * math.pi / 48) / .242) ** 2))
              for t in range(48)]
    curve_band('shell perimeter keyline', points, white, .010, True)
    return 'knee-pad', 'dome-strap-v1', ['mat/knee_tint']


def target(kind):
    reset()
    dark = material('mat/charcoal', (.029, .049, .091))
    white = material('mat/white', (.82, .90, .97))
    tint = material('mat/target_tint', (.04, .62, .98), tint=True, emission=.35)
    if kind == 'split':
        # Approach-size cue: broad colored horseshoe with open top, a bright kneecap.
        # Intentionally unlike glove punches and the outlined shield guard.
        sphere('forward kneecap', (0, -.055, -.065), (.212, .185, .064), tint)
        sphere('kneecap white keyline', (0, -.055, -.009), (.158, .132, .032), white)
        sphere('kneecap inner disc', (0, -.055, -.038), (.121, .103, .045), tint)
        for x in (-.222, .222):
            sphere('paired thigh prong', (x, .178, -.018), (.066, .132, .054), tint, 20, 10)
            sphere('prong dark backing', (x, .173, .020), (.085, .150, .024), dark, 20, 10)
        curve_band('left opening edge', [(-.225, .235, -.035), (-.210, .09, -.055), (-.160, -.115, -.073)], white, .018)
        curve_band('right opening edge', [(.225, .235, -.035), (.210, .09, -.055), (.160, -.115, -.073)], white, .018)
        return 'knee-target', 'open-prong-v1', ['mat/target_tint']
    # Alternate silhouette: compact boot/kneecap, downward chevron tail.
    sphere('armored kneecap', (0, .096, -.054), (.218, .173, .070), tint)
    torus('kneecap contrast ring', (0, .096, -.106), .136, .018, white)
    sphere('inner dark kneecap', (0, .096, -.112), (.107, .092, .020), dark)
    curve_band('downward knee chevron', [(-.183, -.065, -.06), (0, -.315, -.06), (.183, -.065, -.06)], tint, .056)
    curve_band('chevron white inset', [(-.145, -.065, -.125), (0, -.266, -.125), (.145, -.065, -.125)], white, .013)
    return 'knee-target', 'chevron-v1', ['mat/target_tint']


def cameras_and_lights():
    world = bpy.context.scene.world
    world.color = (.10, .10, .10)
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.10, .16, .24, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
    bpy.ops.object.light_add(type='AREA', location=(-2.4, 3.2, -3))
    bpy.context.object.name = 'softbox main'
    bpy.context.object.data.energy = 480
    bpy.context.object.data.shape = 'DISK'
    bpy.context.object.data.size = 3
    bpy.ops.object.light_add(type='AREA', location=(2, 1, 2))
    bpy.context.object.name = 'softbox rim'
    bpy.context.object.data.energy = 320
    bpy.context.object.data.size = 2.5
    bpy.ops.object.camera_add(location=(0, 0, -4))
    bpy.context.object.name = 'review camera'
    bpy.context.scene.camera = bpy.context.object
    bpy.context.object.data.type = 'ORTHO'
    bpy.context.object.data.ortho_scale = 1.05
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = False
    scene.cycles.seed = 12
    scene.cycles.use_animated_seed = False
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'


def write_candidate(builder, label):
    role, variant, tint_names = builder()
    base = root / role / variant
    base.mkdir(parents=True, exist_ok=True)
    meshes = [ob for ob in bpy.context.scene.objects if ob.type == 'MESH']
    # loop_triangles are lazy until calc_loop_triangles is invoked.
    triangles = 0
    for ob in meshes:
        ob.data.calc_loop_triangles()
        triangles += len(ob.data.loop_triangles)
    (base / 'views').mkdir()
    cameras_and_lights()
    bpy.ops.wm.save_as_mainfile(filepath=str(base / f'{variant}.blend'), compress=True)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in meshes:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(base / f'{variant}.glb'), export_format='GLB',
                               use_selection=True, export_apply=False, export_yup=True,
                               export_extras=True, export_materials='EXPORT', export_normals=True,
                               export_texcoords=False, export_keep_originals=False)
    for name, position in VIEWS.items():
        camera = bpy.context.scene.camera
        camera.location = position
        camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.render.filepath = str(base / 'views' / (name + '.png'))
        bpy.ops.render.render(write_still=True)
    if role == 'knee-target':
        camera.location = (0, 0, -4)
        camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        for px in (32, 64):
            camera.data.ortho_scale = .72 * 640 / px
            bpy.context.scene.render.filepath = str(base / 'views' / f'approach-{px}px.png')
            bpy.ops.render.render(write_still=True)
    # Extents from evaluated mesh data, excluding presentation camera and lights.
    xyz = [ob.matrix_world @ Vector(corner) for ob in meshes for corner in ob.bound_box]
    bounds = [[round(min(p[i] for p in xyz), 5) for i in range(3)],
              [round(max(p[i] for p in xyz), 5) for i in range(3)]]
    files = {}
    for path in sorted(base.rglob('*')):
        if path.is_file():
            files[str(path.relative_to(base))] = {'bytes': path.stat().st_size,
                                                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest = {'status': 'UNAPPROVED_CANDIDATE', 'role': role, 'variant': variant,
                'coordinate_contract': '+Y up, local forward -Z, front faces -Z',
                'source_object_rotation_scale': 'identity', 'left_right': 'one pad geometry instanced twice; tint per instance to glove colors',
                'materials': sorted({m.name for ob in meshes for m in ob.data.materials}),
                'runtime_tintable': tint_names, 'textures': [], 'external_dependencies': [],
                'bounds': bounds, 'triangles': triangles, 'blender_version': bpy.app.version_string,
                'rights': 'Original procedural AeroBeat/Gambit Games artwork; CC BY-NC 4.0',
                'files': files}
    (base / 'candidate-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print(f'CANDIDATE {role}/{variant}: {triangles} triangles {bounds}')


write_candidate(pad, 'pad')
write_candidate(lambda: target('split'), 'open prong')
write_candidate(lambda: target('chevron'), 'chevron')
print('KNEE_CANDIDATES_OK')
