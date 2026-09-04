#!/usr/bin/env python3
"""Adversarial regression tests for Blender's exit-zero failure behavior."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from subprocess_contract import run_checked


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
        marker = "GENERATE_OK release=0.0.5 assets=7 sources=7 manifests=7 release_files=17 review_pngs=13 review_metadata=5"
        for scenario, expected in (
            ("traceback", "fatal output signature"),
            ("missing", "expected exact completion marker once, found 0"),
            ("wrong", "expected exact completion marker once, found 0"),
        ):
            env = base_env.copy(); env["FAKE_BLENDER_SCENARIO"] = scenario
            require_contract_failure([str(fake), "--operation"], f"fake generation {scenario}", marker, env, expected)
            completed = subprocess.run(
                [sys.executable, str(root / "tools/validate.py"), "--root", str(root), "--release", "0.0.5"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            if completed.returncode == 0 or expected not in completed.stdout:
                raise AssertionError(f"validator accepted fake Blender {scenario}:\n{completed.stdout}")
            reproduced = subprocess.run(
                [sys.executable, str(root / "tools/reproducibility.py"), "--root", str(root), "--release", "0.0.5"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            if reproduced.returncode == 0 or expected not in reproduced.stdout:
                raise AssertionError(f"reproducibility accepted fake Blender {scenario}:\n{reproduced.stdout}")
        env = base_env.copy(); env["FAKE_BLENDER_SCENARIO"] = "valid-marker"; env["FAKE_EXPECTED_MARKER"] = marker
        require_contract_failure([str(fake), "--operation"], "fake generation postcondition", marker, env, "postcondition returned false", postcondition=lambda: False)
    print("CONTRACT_TEST_OK adversarial=4 validator_fake_blender=3 reproducibility_fake_blender=3")


if __name__ == "__main__":
    main()
