#!/usr/bin/env python3
"""Validate isolated provisional knee assets; never finalizes a release."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess_contract

parser = argparse.ArgumentParser()
parser.add_argument('--candidate-root', type=Path, required=True)
parser.add_argument('--blender', default='blender')
parser.add_argument('--smoke', action='store_true')
args = parser.parse_args()
root = args.candidate_root.resolve()
roles = [('knee-pad', 'dome-strap-v1', 4),
         ('knee-target', 'open-prong-v1', 6),
         ('knee-target', 'chevron-v1', 6)]
if not root.is_dir():
    raise RuntimeError(f'Candidate root missing: {root}')
for role, variant, view_count in roles:
    base = root / role / variant
    manifest = json.loads((base / 'candidate-manifest.json').read_text())
    if manifest['status'] != 'UNAPPROVED_CANDIDATE' or (manifest['role'], manifest['variant']) != (role, variant):
        raise RuntimeError(f'Candidate identity/status mismatch: {base}')
    if manifest['blender_version'] != '4.0.2' or manifest['textures'] or manifest['external_dependencies']:
        raise RuntimeError(f'Candidate provenance/dependency mismatch: {base}')
    names = set(manifest['files'])
    required = {f'{variant}.blend', f'{variant}.glb'}
    required |= {f'views/{name}.png' for name in ('front', 'side', 'back', 'three-quarter')}
    if role == 'knee-target':
        required |= {'views/approach-32px.png', 'views/approach-64px.png'}
    if names != required or len(names) != view_count + 2:
        raise RuntimeError(f'Wrong candidate inventory: {base}: {names ^ required}')
    for rel, facts in manifest['files'].items():
        p = base / rel
        if p.stat().st_size != facts['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest() != facts['sha256']:
            raise RuntimeError(f'Candidate file digest mismatch: {p}')
        if p.suffix == '.png' and p.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
            raise RuntimeError(f'Review image not PNG: {p}')
    glb = (base / f'{variant}.glb').read_bytes()
    magic, version, length = struct.unpack_from('<III', glb)
    if (magic, version, length) != (0x46546c67, 2, len(glb)):
        raise RuntimeError(f'Malformed GLB header: {base}')
    json_len, json_type = struct.unpack_from('<II', glb, 12)
    if json_type != 0x4e4f534a:
        raise RuntimeError(f'Missing GLB JSON: {base}')
    data = json.loads(glb[20:20 + json_len])
    if data.get('images') or data.get('textures') or data.get('extensionsRequired') or data.get('buffers', [{}])[0].get('uri'):
        raise RuntimeError(f'GLB contains external dependency or texture: {base}')
    mats = {m['name']: m.get('extras', {}).get('aerobeat', {}) for m in data['materials']}
    if set(mats) != set(manifest['materials']) or {name for name, meta in mats.items() if meta.get('runtimeTintable')} != set(manifest['runtime_tintable']):
        raise RuntimeError(f'GLB material tint mismatch: {base}')
    if not all(m.get('structural') is (not m.get('runtimeTintable')) for m in mats.values()):
        raise RuntimeError(f'GLB material role mismatch: {base}')
    if not data['meshes'] or not all(all('NORMAL' in p['attributes'] for p in mesh['primitives']) for mesh in data['meshes']):
        raise RuntimeError(f'GLB mesh NORMAL missing: {base}')
    if manifest['triangles'] <= 0 or manifest['triangles'] > 5000:
        raise RuntimeError(f'Candidate triangle limit: {base}')
    if args.smoke:
        script = Path(__file__).with_name('smoke_knee_candidates.py').resolve()
        for kind, path in [('source', base / f'{variant}.blend'), ('glb', base / f'{variant}.glb')]:
            marker = f'KNEE_SMOKE_OK {kind} {role}/{variant}'
            subprocess_contract.run_checked(
                [args.blender, '--background', '--factory-startup', '--python', str(script), '--',
                 kind, str(path), role, variant], operation=f'knee {kind} smoke', marker=marker,
                postcondition=lambda: path.is_file() and path.stat().st_size > 0)
    print(f'VALIDATED_CANDIDATE {role}/{variant} ({manifest["triangles"]} triangles)')
print('KNEE_VALIDATION_OK')
