#!/usr/bin/env python3
"""Build an additive 0.0.13 knee candidate in a NEW disposable root.

Only --promote from a separately validated staged root may write canonical
0.0.13. The ordinary build never writes tracked source or immutable releases.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

from subprocess_contract import run_checked

RELEASE = '0.0.13'
PREDECESSOR = '0.0.12'
IDENTITIES = {
    'knee-target': ('hover-shell-strike-v1', 'generate_hover_strike_candidate.py',
                    'validate_hover_strike_candidate.py', 'HOVER_STRIKE_CANDIDATE_OK'),
    'knee-pad': ('segmented-lightwrap-v1', 'generate_segmented_knee_pad_candidate.py',
                 'validate_segmented_knee_pad_candidate.py', 'SEGMENTED_PAD_CANDIDATE_OK'),
}


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(doc):
    return (json.dumps(doc, sort_keys=True, separators=(',', ':')) + '\n').encode()


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def authority(root):
    source_commit = git(root, 'rev-parse', 'HEAD')
    source_tree = git(root, 'rev-parse', 'HEAD^{tree}')
    check(not subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', 'tools/generate_hover_strike_candidate.py',
                              'tools/generate_segmented_knee_pad_candidate.py', 'tools/knee_mesh_order.py',
                              'tools/knee_png_metadata.py'], cwd=root).returncode,
          'Generator inputs differ from committed authority')
    return {'commit': source_commit, 'tree': source_tree}


def generate(root, output, blender):
    root = root.resolve(); output = output.resolve()
    check(root != output and not output.is_relative_to(root), 'Output must be a separate disposable root')
    check(not output.exists() or not any(output.iterdir()), 'Output root is not empty')
    check(not (root / f'release/raw/{RELEASE}').exists() and not (root / f'review/{RELEASE}').exists(),
          'Canonical successor already exists; never rebuild an immutable release')
    check(subprocess.check_output([blender, '--version'], text=True).splitlines()[0] == 'Blender 4.0.2',
          'Blender 4.0.2 required')
    predecessor = root / f'release/raw/{PREDECESSOR}'
    check(predecessor.is_dir(), 'Missing immutable predecessor')
    source_authority = authority(root)
    output.mkdir(parents=True, exist_ok=True)
    artifacts = output / 'candidates'
    artifacts.mkdir()
    for role, (variant, script, _validator, marker) in IDENTITIES.items():
        role_root = artifacts / role
        run_checked([blender, '--background', '--factory-startup', '--python', str(root / 'tools' / script),
                     '--', '--output-root', str(role_root)], operation=f'knee {role} generation', marker=marker,
                    postcondition=lambda r=role, v=variant: (artifacts / r / r / v / (v + '.glb')).is_file())
    raw = output / f'release/raw/{RELEASE}'
    review = output / f'review/{RELEASE}'
    shutil.copytree(predecessor, raw)
    for copied in (raw, *raw.rglob('*')):
        os.chmod(copied, 0o755 if copied.is_dir() else 0o644)
    (raw / 'inventory.v1.json').unlink()
    (raw / 'proof.v1.json').unlink()
    review.mkdir(parents=True)
    source = output / 'source'
    source.mkdir()
    source_fingerprints = {}
    for role, (variant, _script, _validator, _marker) in IDENTITIES.items():
        candidate = artifacts / role / role / variant
        identity = role + '/' + variant
        output_blend = source / role / variant / (variant + '.blend')
        output_blend.parent.mkdir(parents=True)
        shutil.copy2(candidate / (variant + '.blend'), output_blend)
        fingerprint = output / (role + '-scene.json')
        run_checked([blender, '--background', '--factory-startup', '--python',
                     str(root / 'tools/blender_scene_fingerprint.py'), '--', str(output_blend), str(fingerprint)],
                    operation=f'{identity} source fingerprint', marker='SCENE_FINGERPRINT_OK',
                    postcondition=lambda p=fingerprint: p.is_file())
        source_fingerprints[identity] = sha(fingerprint)
        fingerprint.unlink()
        (raw / role).mkdir()
        shutil.copy2(candidate / (variant + '.glb'), raw / role / (variant + '.glb'))
        for png in sorted((candidate / 'views').glob('*.png')):
            shutil.copy2(png, review / f'{role}--{variant}--{png.name}')
        info = json.loads((candidate / 'candidate-manifest.json').read_text())
        facts = info['geometry']
        material = info['materials']
        names = material['names']
        document = {
            'schema': 'aerobeat.gameplay-asset/v1', 'release': RELEASE,
            'identity': {'canonical_name': identity, 'role': role, 'variant': variant},
            'coordinates': {'handedness': 'right', 'up': '+Y', 'forward': '-Z'},
            'geometry': {'measured_aabb': facts['measured_aabb'],
                         'triangle_count': facts['triangle_count'], 'triangle_budget': facts['triangle_budget'],
                         'rotation_euler': [0, 0, 0], 'scale': [1, 1, 1]},
            'materials': {'names': names, 'analytic_only': True, 'textures': [],
                          'runtime_tintable': material['runtime_tintable']},
            'dependencies': [], 'rights': {'creator': 'AeroBeat / Gambit Games',
                                            'license': 'CC-BY-NC-4.0', 'third_party_content': False},
            'provenance': {'blender': '4.0.2', 'network': False,
                           'generator': 'tools/' + IDENTITIES[role][1],
                           'source_authority': source_authority},
            'source_authority': {'semantic_scene_sha256': source_fingerprints[identity],
                                  'blend_byte_determinism_claimed': False},
            'files': {'source': f'source/{identity}/{variant}.blend',
                      'release': f'release/raw/{RELEASE}/{identity}.glb',
                      'release_bytes': (raw / role / (variant + '.glb')).stat().st_size,
                      'release_sha256': sha(raw / role / (variant + '.glb'))},
        }
        target = raw / 'manifests' / role / f'{variant}.v1.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(json_bytes(document))
    set_path = raw / 'sets/default-v1.json'
    set_doc = json.loads(set_path.read_text())
    set_doc['release'] = RELEASE
    for role, (variant, *_rest) in IDENTITIES.items():
        set_doc['roles'][role] = variant
    set_path.write_bytes(json_bytes(set_doc))
    # Review manifest is SHA-bound but contains only stable, approved render bytes.
    views = sorted(p for p in review.glob('*.png'))
    (review / 'hashes.v1.json').write_bytes(json_bytes({
        'schema': 'aerobeat.knee-review-hashes/v1', 'release': RELEASE,
        'files': [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in views]}))
    payload = sorted(p for p in raw.rglob('*') if p.is_file())
    inventory = {'schema': 'aerobeat.gameplay-release-inventory/v1', 'release': RELEASE,
                 'immutable': True, 'expected_asset_count': 9,
                 'payload': [{'path': p.relative_to(raw).as_posix(), 'bytes': p.stat().st_size,
                              'sha256': sha(p)} for p in payload]}
    (raw / 'inventory.v1.json').write_bytes(json_bytes(inventory))
    proof = {'schema': 'aerobeat.knee-release-proof/v1', 'release': RELEASE,
             'predecessor': PREDECESSOR, 'source_authority': source_authority,
             'changed_identities': sorted(source_fingerprints),
             'byte_identical_predecessor_roles': sorted(set_doc['roles'] - IDENTITIES.keys()),
             'source_semantic_scene_sha256': source_fingerprints,
             'inventory_sha256': sha(raw / 'inventory.v1.json'),
             'review_hashes_sha256': sha(review / 'hashes.v1.json'),
             'blend_byte_determinism_claimed': False,
             'no_runtime_gameplay_claim': True}
    (raw / 'proof.v1.json').write_bytes(json_bytes(proof))
    print('KNEE_RELEASE_CANDIDATE_OK release=0.0.13 assets=9')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output-root', required=True, type=Path)
    parser.add_argument('--blender', default='blender')
    args = parser.parse_args()
    generate(args.root, args.output_root, args.blender)


if __name__ == '__main__':
    main()
