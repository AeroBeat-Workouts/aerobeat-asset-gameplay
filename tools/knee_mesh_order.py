"""Stable original-face ordering for provisional Blender knee assets.

Blender 4.0.2's UV sphere operator emits stable vertex coordinates but schedules
face/edge/loop order differently across processes. This rebuilds each *original*
polygon in a fixed vertex-index order without moving vertices or merging faces.
Only call before saving/exporting candidate sources, never on finalized assets.
"""

import bpy


def canonicalize_mesh(obj):
    if obj.type != 'MESH':
        raise TypeError('Only mesh objects can be canonicalized')
    source = obj.data
    faces = [tuple(poly.vertices) for poly in source.polygons]
    if len({tuple(sorted(face)) for face in faces}) != len(faces):
        raise RuntimeError(f'Refuse duplicate coincident faces in {obj.name}')
    ordered = sorted(range(len(faces)), key=lambda i: (tuple(sorted(faces[i])), faces[i]))
    if ordered == list(range(len(faces))):
        return
    result = bpy.data.meshes.new(source.name + '_ordered')
    result.from_pydata([tuple(v.co) for v in source.vertices], [], [faces[i] for i in ordered])
    result.update()
    for mat in source.materials:
        result.materials.append(mat)
    for index, original in enumerate(ordered):
        old, new = source.polygons[original], result.polygons[index]
        new.material_index = old.material_index
        new.use_smooth = old.use_smooth
    # The current knee generators use no external texture assets. Reorder any
    # procedural UV loops by the same face/vertex corner rather than discard UVs.
    for layer in source.uv_layers:
        target = result.uv_layers.new(name=layer.name)
        for index, original in enumerate(ordered):
            old, new = source.polygons[original], result.polygons[index]
            corners = {source.loops[i].vertex_index: tuple(layer.data[i].uv) for i in old.loop_indices}
            for i in new.loop_indices:
                target.data[i].uv = corners[result.loops[i].vertex_index]
    obj.data = result
    if source.users == 0:
        bpy.data.meshes.remove(source)


def canonicalize_all(meshes):
    for ob in sorted(meshes, key=lambda item: item.name):
        canonicalize_mesh(ob)
