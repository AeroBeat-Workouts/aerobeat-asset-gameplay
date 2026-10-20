#!/usr/bin/env python3
"""Fail-closed structural/hash/import gate for additive knee release 0.0.13."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from subprocess_contract import run_checked

RELEASE = '0.0.13'
OLD = '0.0.12'
ROLES = {'knee-target': ('hover-shell-strike-v1', 5000, 4528,
                         ['mat/cyan_rim', 'mat/shadow_charcoal', 'mat/shell_white', 'mat/strike_lime'], []),
         'knee-pad': ('segmented-lightwrap-v1', 7000, 5440,
                      ['mat/front_blue_light', 'mat/glove_match_tint', 'mat/padded_gray', 'mat/shell_white', 'mat/strap_gray'],
                      ['mat/glove_match_tint'])}
VIEWS = {'knee-target': ('front', 'side', 'back', 'underside', 'three-quarter', 'approach-32px', 'approach-64px'),
         'knee-pad': ('front', 'side', 'back', 'three-quarter', *(
             f'{pose}-pair-{pair}-{angle}' for pose in ('lowered', 'raised')
             for pair in ('a', 'b') for angle in ('front', 'side', 'back')))}


def check(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def tree(base):
    files = sorted(p for p in base.rglob('*') if p.is_file())
    rows = ''.join(f'{p.relative_to(base).as_posix()}\0{p.stat().st_size}\0{sha(p)}\n' for p in files)
    return len(files), sum(p.stat().st_size for p in files), hashlib.sha256(rows.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--authority-root', required=True, type=Path)
    parser.add_argument('--candidate-root', required=True, type=Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--source-tree', required=True)
    parser.add_argument('--blender', default='blender')
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    authority = args.authority_root.resolve(); candidate = args.candidate_root.resolve()
    raw = candidate / f'release/raw/{RELEASE}'; review = candidate / f'review/{RELEASE}'
    check(raw.is_dir() and review.is_dir(), 'Missing 0.0.13 release or review')
    check(subprocess.check_output(['git', 'rev-parse', f'{args.source_commit}^{{tree}}'],
                                  cwd=authority, text=True).strip() == args.source_tree,
          'Invalid source authority commit/tree')
    committed_predecessor = subprocess.check_output(['git', 'rev-parse', f'HEAD:release/raw/{OLD}'],
                                                     cwd=authority, text=True).strip()
    check(subprocess.check_output(['git', 'rev-parse', f'{args.source_commit}:release/raw/{OLD}'],
                                  cwd=authority, text=True).strip() == committed_predecessor,
          'Source authority changed predecessor Git tree')
    old = authority / f'release/raw/{OLD}'
    check(old.is_dir(), 'Missing predecessor')
    inventory = load(raw / 'inventory.v1.json'); proof = load(raw / 'proof.v1.json')
    check(inventory['release'] == RELEASE and inventory['immutable'] is True and
          inventory['expected_asset_count'] == 9, 'Inventory release header')
    check(proof['release'] == RELEASE and proof['predecessor'] == OLD and
          proof['source_authority'] == {'commit': args.source_commit, 'tree': args.source_tree} and
          proof['inventory_sha256'] == sha(raw / 'inventory.v1.json') and
          proof['review_hashes_sha256'] == sha(review / 'hashes.v1.json') and
          proof['blend_byte_determinism_claimed'] is False and proof['no_runtime_gameplay_claim'] is True,
          'Invalid release proof binding or semantic source contract')
    old_files = {p.relative_to(old).as_posix() for p in old.rglob('*') if p.is_file()}
    old_payload = old_files - {'inventory.v1.json', 'proof.v1.json', 'sets/default-v1.json'}
    predecessor_set = load(old / 'sets/default-v1.json')
    unchanged_roles = set(predecessor_set['roles'])
    check(set(proof['byte_identical_predecessor_roles']) == unchanged_roles and
          set(proof['changed_identities']) == {r + '/' + info[0] for r, info in ROLES.items()},
          'Incorrect changed/predecessor identities')
    expected = set(old_files)
    expected.update({f'{role}/{variant}.glb' for role, (variant, *_rest) in ROLES.items()})
    expected.update({f'manifests/{role}/{variant}.v1.json' for role, (variant, *_rest) in ROLES.items()})
    actual = {p.relative_to(raw).as_posix() for p in raw.rglob('*') if p.is_file()}
    check(actual == expected and len(actual) == 21, f'Unexpected raw contents: {actual ^ expected}')
    for path in old_payload:
        check((raw / path).read_bytes() == (old / path).read_bytes(), f'Predecessor byte drift: {path}')
    set_doc = load(raw / 'sets/default-v1.json')
    expected_roles = {**predecessor_set['roles'], **{role: data[0] for role, data in ROLES.items()}}
    check(set_doc == {**predecessor_set, 'release': RELEASE, 'roles': expected_roles}, 'Set not strictly additive')
    payload = {row['path']: row for row in inventory['payload']}
    check(set(payload) == actual - {'inventory.v1.json', 'proof.v1.json'}, 'Inventory path mismatch')
    for path, fact in payload.items():
        check(fact == {'path': path, 'bytes': (raw / path).stat().st_size, 'sha256': sha(raw / path)},
              f'Inventory hash mismatch: {path}')
    review_doc = load(review / 'hashes.v1.json')
    expected_views = {f'{role}--{data[0]}--{view}.png'
                      for role, data in ROLES.items() for view in VIEWS[role]}
    review_files = {p.name for p in review.iterdir() if p.is_file()}
    check(review_files == expected_views | {'hashes.v1.json'} and
          review_doc['release'] == RELEASE and review_doc['schema'] == 'aerobeat.knee-review-hashes/v1',
          'Review inventory/layout mismatch')
    views = {row['path']: row for row in review_doc['files']}
    check(set(views) == expected_views and len(views) == 23, 'Review hash entries missing')
    for name, fact in views.items():
        p = review / name
        check(fact == {'path': name, 'bytes': p.stat().st_size, 'sha256': sha(p)},
              f'Review PNG hash mismatch: {name}')
        data = p.read_bytes()
        check(data[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', data, 16) == (640, 640),
              f'Invalid review PNG dimensions: {name}')
    for role, (variant, budget, triangles, materials, tint) in ROLES.items():
        identity = role + '/' + variant
        rel = f'{role}/{variant}.glb'; glb = raw / rel
        document = load(raw / 'manifests' / role / f'{variant}.v1.json')
        check(document['schema'] == 'aerobeat.gameplay-asset/v1' and document['release'] == RELEASE and
              document['identity'] == {'canonical_name': identity, 'role': role, 'variant': variant},
              f'Identity contract: {identity}')
        check(document['coordinates'] == {'handedness': 'right', 'up': '+Y', 'forward': '-Z'} and
              document['geometry']['triangle_count'] == triangles and
              document['geometry']['triangle_budget'] == budget and
              document['geometry']['rotation_euler'] == [0, 0, 0] and
              document['geometry']['scale'] == [1, 1, 1] and
              document['materials'] == {'names': materials, 'analytic_only': True,
                                       'textures': [], 'runtime_tintable': tint} and
              document['dependencies'] == [] and not document['rights']['third_party_content'],
              f'Geometry/material/provenance contract: {identity}')
        check(document['files'] == {'source': f'source/{identity}/{variant}.blend',
                                    'release': f'release/raw/{RELEASE}/{rel}',
                                    'release_bytes': glb.stat().st_size, 'release_sha256': sha(glb)},
              f'Manifest source/GLB SHA: {identity}')
        check(document['source_authority'] == {
            'semantic_scene_sha256': proof['source_semantic_scene_sha256'][identity],
            'blend_byte_determinism_claimed': False} and
            document['provenance']['source_authority'] == proof['source_authority'] and
            document['provenance']['blender'] == '4.0.2' and
            document['provenance']['network'] is False, f'Manifest authority: {identity}')
        data = glb.read_bytes()
        check(struct.unpack_from('<4sII', data) == (b'glTF', 2, len(data)), 'Bad GLB header')
        n, marker = struct.unpack_from('<I4s', data, 12)
        check(marker == b'JSON', 'Missing GLB JSON chunk')
        scene = json.loads(data[20:20 + n])
        check(not any(scene.get(k) for k in ('textures', 'images', 'extensionsRequired')) and
              not any('uri' in row for row in scene['buffers']) and
              len(scene['materials']) == len(materials) and
              {m['name'] for m in scene['materials']} == set(materials) and
              not any('review' in node.get('name', '').lower() for node in scene['nodes']),
              f'GLB dependency/material/review geometry: {identity}')
        tint_names = {m['name'] for m in scene['materials']
                      if m.get('extras', {}).get('aerobeat', {}).get('runtimeTintable')}
        check(tint_names == set(tint) and all('NORMAL' in p['attributes']
                                            for mesh in scene['meshes'] for p in mesh['primitives']),
              f'GLB tint and normals: {identity}')
        source = candidate / 'source' / role / variant / f'{variant}.blend'
        check(source.is_file(), f'Missing editable source: {identity}')
        if args.smoke:
            script = authority / 'tools/blender_scene_fingerprint.py'
            output = candidate / (role + '-validator-scene.json')
            run_checked([args.blender, '--background', '--factory-startup', '--python', str(script),
                         '--', str(source), str(output)], operation=f'{identity} fingerprint',
                        marker='SCENE_FINGERPRINT_OK', postcondition=lambda: output.is_file())
            check(sha(output) == proof['source_semantic_scene_sha256'][identity],
                  f'Source semantic fingerprint mismatch: {identity}')
            output.unlink()
            smoke = authority / 'tools' / ('smoke_hover_strike_candidate.py' if role == 'knee-target'
                                          else 'smoke_segmented_knee_pad_candidate.py')
            for kind, path in (('source', source), ('glb', glb)):
                marker = ('HOVER_STRIKE_SMOKE_OK' if role == 'knee-target' else 'SEGMENTED_PAD_SMOKE_OK') + ' ' + kind
                run_checked([args.blender, '--background', '--factory-startup', '--python', str(smoke),
                             '--', kind, str(path)], operation=f'{identity} {kind} smoke', marker=marker,
                            postcondition=lambda p=path: p.is_file() and p.stat().st_size > 0)
    check(tree(old) == tree(authority / f'release/raw/{OLD}'), 'Immutable predecessor drift')
    print(json.dumps({'pass': True, 'release': RELEASE, 'raw': tree(raw), 'review': tree(review),
                      'blender_smoke': args.smoke, 'source_semantic_scene_sha256': proof['source_semantic_scene_sha256']},
                     sort_keys=True))
    print('KNEE_RELEASE_VALIDATION_OK')


if __name__ == '__main__':
    main()
