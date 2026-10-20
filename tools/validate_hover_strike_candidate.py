#!/usr/bin/env python3
"""First-generation structural/hash validation for one unapproved hover target."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from subprocess_contract import run_checked

parser = argparse.ArgumentParser()
parser.add_argument('--candidate-root', required=True, type=Path)
parser.add_argument('--blender', default='blender')
parser.add_argument('--smoke', action='store_true')
args = parser.parse_args()
base = args.candidate_root.resolve() / 'knee-target' / 'hover-shell-strike-v1'
variant = 'hover-shell-strike-v1'
m = json.loads((base / 'candidate-manifest.json').read_text())
if m['status'] != 'UNAPPROVED_CANDIDATE' or m['identity'] != {'role': 'knee-target', 'variant': variant}:
    raise RuntimeError('Unexpected candidate identity or approval status')
if m['blender_version'] != '4.0.2' or m['materials']['texture_dependencies']:
    raise RuntimeError('Invalid Blender/dependency contract')
expected = {f'{variant}.blend', f'{variant}.glb'} | {
    f'views/{v}.png' for v in ('front', 'side', 'back', 'underside', 'three-quarter',
                               'approach-32px', 'approach-64px')}
if set(m['files']) != expected:
    raise RuntimeError('Missing or extra candidate files')
for rel, facts in m['files'].items():
    data = (base / rel).read_bytes()
    if len(data) != facts['bytes'] or hashlib.sha256(data).hexdigest() != facts['sha256']:
        raise RuntimeError(f'Candidate hash mismatch: {rel}')
    if rel.endswith('.png') and (data[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II', data, 16) != (640, 640)):
        raise RuntimeError(f'Invalid review PNG: {rel}')
glb = (base / (variant + '.glb')).read_bytes()
if struct.unpack_from('<III', glb) != (0x46546c67, 2, len(glb)):
    raise RuntimeError('GLB header mismatch')
n, chunk_type = struct.unpack_from('<II', glb, 12)
if chunk_type != 0x4e4f534a:
    raise RuntimeError('Missing GLB JSON chunk')
g = json.loads(glb[20:20+n])
if any(g.get(x) for x in ('textures', 'images', 'extensionsRequired')) or any(b.get('uri') for b in g['buffers']):
    raise RuntimeError('External dependencies/textures not allowed')
materials = {o['name']: o for o in g['materials']}
if set(materials) != set(m['materials']['names']) or m['materials']['runtime_tintable']:
    raise RuntimeError('Materials differ from provisional manifest')
if any(o.get('extras', {}).get('aerobeat', {}).get('runtimeTintable') for o in materials.values()):
    raise RuntimeError('Unexpected runtime tint')
if materials['mat/cyan_rim']['alphaMode'] != 'BLEND' or not all(
    'NORMAL' in p['attributes'] for mesh in g['meshes'] for p in mesh['primitives']):
    raise RuntimeError('Missing translucent rim or mesh normals')
if not 0 < m['geometry']['triangle_count'] <= m['geometry']['triangle_budget']:
    raise RuntimeError('Geometry outside provisional budget')
if args.smoke:
    script = Path(__file__).with_name('smoke_hover_strike_candidate.py')
    for kind, suffix in [('source', '.blend'), ('glb', '.glb')]:
        path = base / (variant + suffix)
        marker = f'HOVER_STRIKE_SMOKE_OK {kind}'
        run_checked([args.blender, '--background', '--factory-startup', '--python', str(script),
                     '--', kind, str(path)],
                    operation=f'hover strike {kind} import', marker=marker,
                    postcondition=lambda: path.is_file() and path.stat().st_size > 0)
        print(marker)
print('HOVER_STRIKE_VALIDATION_OK')
