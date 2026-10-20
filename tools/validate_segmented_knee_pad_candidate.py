#!/usr/bin/env python3
"""Provisional hashes, Blender smoke and GLB checks for one wearable pad."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from subprocess_contract import run_checked

cli = argparse.ArgumentParser()
cli.add_argument('--candidate-root', type=Path, required=True)
cli.add_argument('--smoke', action='store_true')
cli.add_argument('--blender', default='blender')
args = cli.parse_args()
variant = 'segmented-lightwrap-v1'
base = args.candidate_root.resolve() / 'knee-pad' / variant
manifest = json.loads((base / 'candidate-manifest.json').read_text())
if manifest['status'] != 'UNAPPROVED_CANDIDATE' or manifest['identity'] != {'role': 'knee-pad', 'variant': variant}:
    raise RuntimeError('Unexpected candidate status or identity')
if manifest['blender_version'] != '4.0.2' or manifest['materials']['textures'] or manifest['materials']['external_dependencies']:
    raise RuntimeError('Invalid Blender version or external dependencies')
views = ('front', 'side', 'back', 'three-quarter')
views += tuple(f'{pose}-pair-{pair}-{angle}' for pose in ('lowered', 'raised')
               for pair in ('a', 'b') for angle in ('front', 'side', 'back'))
expected = {f'{variant}.blend', f'{variant}.glb'} | {f'views/{v}.png' for v in views}
if set(manifest['files']) != expected:
    raise RuntimeError(f'Missing or extra pad artifacts: {set(manifest["files"]) ^ expected}')
for rel, facts in manifest['files'].items():
    content = (base / rel).read_bytes()
    if len(content) != facts['bytes'] or hashlib.sha256(content).hexdigest() != facts['sha256']:
        raise RuntimeError(f'Candidate file changed: {rel}')
    if rel.endswith('.png') and (content[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack_from('>II', content, 16) != (640, 640)):
        raise RuntimeError(f'Invalid review PNG: {rel}')
glb = (base / (variant + '.glb')).read_bytes()
if struct.unpack_from('<III', glb) != (0x46546c67, 2, len(glb)):
    raise RuntimeError('GLB header/length mismatch')
n, chunk_type = struct.unpack_from('<II', glb, 12)
if chunk_type != 0x4e4f534a:
    raise RuntimeError('No GLB JSON chunk')
data = json.loads(glb[20:20 + n])
if any(data.get(x) for x in ('textures', 'images', 'extensionsRequired')) or any(b.get('uri') for b in data['buffers']):
    raise RuntimeError('External assets in GLB')
if any('review' in o.get('name', '').lower() for o in data['nodes']):
    raise RuntimeError('Review-only posed leg leaked into GLB')
mats = {m['name']: m for m in data['materials']}
if set(mats) != set(manifest['materials']['names']):
    raise RuntimeError('GLB material names mismatch')
tint = {name for name, mat in mats.items() if mat.get('extras', {}).get('aerobeat', {}).get('runtimeTintable')}
if tint != {'mat/glove_match_tint'} or tint != set(manifest['materials']['runtime_tintable']):
    raise RuntimeError('Expected one glove-color runtime tint material')
if mats['mat/glove_match_tint'].get('alphaMode') != 'BLEND' or not all(
    'NORMAL' in p['attributes'] for mesh in data['meshes'] for p in mesh['primitives']):
    raise RuntimeError('Missing analytic translucent accent or normals')
geometry = manifest['geometry']
if not 0 < geometry['triangle_count'] <= geometry['triangle_budget']:
    raise RuntimeError('Pad triangle budget exceeded')
if args.smoke:
    script = Path(__file__).with_name('smoke_segmented_knee_pad_candidate.py').resolve()
    for kind, ext in [('source', 'blend'), ('glb', 'glb')]:
        file = base / f'{variant}.{ext}'
        marker = f'SEGMENTED_PAD_SMOKE_OK {kind}'
        run_checked([args.blender, '--background', '--factory-startup', '--python', str(script),
                     '--', kind, str(file)], operation=f'pad {kind} import', marker=marker,
                    postcondition=lambda: file.is_file() and file.stat().st_size > 0)
        print(marker)
print('SEGMENTED_PAD_VALIDATION_OK')
