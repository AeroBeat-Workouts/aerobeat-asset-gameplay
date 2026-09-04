#!/usr/bin/env python3
"""Adversarial regression tests for Blender's exit-zero failure behavior."""
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from subprocess_contract import run_checked
from validate import assert_marker_geometry


def assert_inward_marker_rejected(root):
    source = root / "release/raw/0.0.7/athlete-marker/sphere-v1.glb"
    data = bytearray(source.read_bytes())
    json_size, json_type = struct.unpack_from("<I4s", data, 12)
    if json_type != b"JSON":
        raise AssertionError("marker fixture lacks JSON chunk")
    doc = json.loads(data[20 : 20 + json_size].decode("utf-8").rstrip(" \x00"))
    binary_start = 20 + json_size + 8
    for primitive in doc["meshes"][0]["primitives"]:
        accessor = doc["accessors"][primitive["indices"]]
        view = doc["bufferViews"][accessor["bufferView"]]
        start = binary_start + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        code, size = {5123: ("H", 2), 5125: ("I", 4)}[accessor["componentType"]]
        for index in range(0, accessor["count"], 3):
            second = start + (index + 1) * size
            third = start + (index + 2) * size
            b = struct.unpack_from("<" + code, data, second)[0]
            c = struct.unpack_from("<" + code, data, third)[0]
            struct.pack_into("<" + code, data, second, c)
            struct.pack_into("<" + code, data, third, b)
    with tempfile.TemporaryDirectory(prefix="aerobeat-inward-marker-") as temp:
        fixture = Path(temp) / "inward.glb"
        fixture.write_bytes(data)
        try:
            assert_marker_geometry(fixture)
        except AssertionError as exc:
            if "inward/non-outward winding" not in str(exc):
                raise AssertionError(f"wrong inward marker rejection: {exc}") from exc
        else:
            raise AssertionError("validator accepted inward-wound marker mutation")


def require_contract_failure(command, operation, marker, env, expected, postcondition=None):
    try:
        run_checked(
            command,
            operation=operation,
            marker=marker,
            env=env,
            postcondition=postcondition,
        )
    except RuntimeError as exc:
        if expected not in str(exc):
            raise AssertionError(f"wrong failure for {operation}: {exc}") from exc
        return
    raise AssertionError(f"{operation} unexpectedly passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    assert_inward_marker_rejected(root)
    with tempfile.TemporaryDirectory(prefix="aerobeat-fake-blender-") as temp:
        fake = Path(temp) / "blender"
        fake.write_text(
            """#!/usr/bin/env python3
import os, sys
if '--version' in sys.argv:
    print('Blender 4.0.2')
    raise SystemExit(0)
scenario=os.environ.get('FAKE_BLENDER_SCENARIO','missing')
if scenario=='traceback':
    print('Traceback (most recent call last):')
    print('RuntimeError: QA_MASKED_FAILURE')
elif scenario=='wrong':
    print('SMOKE_OK kind=glb identity=wrong')
elif scenario=='valid-marker':
    print(os.environ['FAKE_EXPECTED_MARKER'])
raise SystemExit(0)
""",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        base_env = os.environ.copy()
        base_env["PATH"] = temp + os.pathsep + base_env.get("PATH", "")
        marker = "GENERATE_OK release=0.0.7 assets=7 sources=7 manifests=7 release_files=17 review_pngs=23 review_metadata=5"
        for scenario, expected in (
            ("traceback", "fatal output signature"),
            ("missing", "expected exact completion marker once, found 0"),
            ("wrong", "expected exact completion marker once, found 0"),
        ):
            env = base_env.copy(); env["FAKE_BLENDER_SCENARIO"] = scenario
            require_contract_failure([str(fake), "--operation"], f"fake generation {scenario}", marker, env, expected)
            completed = subprocess.run(
                [sys.executable, str(root / "tools/validate.py"), "--root", str(root), "--release", "0.0.7"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            if completed.returncode == 0 or expected not in completed.stdout:
                raise AssertionError(f"validator accepted fake Blender {scenario}:\n{completed.stdout}")
            reproduced = subprocess.run(
                [sys.executable, str(root / "tools/reproducibility.py"), "--root", str(root), "--release", "0.0.7"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            if reproduced.returncode == 0 or expected not in reproduced.stdout:
                raise AssertionError(f"reproducibility accepted fake Blender {scenario}:\n{reproduced.stdout}")
        env = base_env.copy(); env["FAKE_BLENDER_SCENARIO"] = "valid-marker"; env["FAKE_EXPECTED_MARKER"] = marker
        require_contract_failure([str(fake), "--operation"], "fake generation postcondition", marker, env, "postcondition returned false", postcondition=lambda: False)
    print("CONTRACT_TEST_OK adversarial=5 inward_marker_mutation=1 validator_fake_blender=3 reproducibility_fake_blender=3")


if __name__ == "__main__":
    main()
