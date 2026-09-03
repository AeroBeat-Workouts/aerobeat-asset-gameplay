#!/usr/bin/env python3
"""Shared fail-closed subprocess contract for Blender-backed asset operations."""
from __future__ import annotations

import subprocess

FATAL_SIGNATURES = (
    "Traceback (most recent call last):",
    "Error: Python:",
    "uncaught exception",
    "unhandled exception",
)


def run_checked(command, *, operation, marker, postcondition=None, env=None):
    """Require clean output, exact completion marker, and caller postcondition."""
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    output = completed.stdout or ""
    if completed.returncode != 0:
        raise RuntimeError(
            f"{operation}: subprocess returned {completed.returncode}\n{output}"
        )
    lowered = output.lower()
    found = [signature for signature in FATAL_SIGNATURES if signature.lower() in lowered]
    if found:
        raise RuntimeError(
            f"{operation}: fatal output signature {found[0]!r} with rc=0\n{output}"
        )
    marker_count = output.splitlines().count(marker)
    if marker_count != 1:
        raise RuntimeError(
            f"{operation}: expected exact completion marker once, found {marker_count}: {marker!r}\n{output}"
        )
    if postcondition is not None:
        try:
            result = postcondition()
        except Exception as exc:
            raise RuntimeError(f"{operation}: postcondition failed: {exc}") from exc
        if result is False:
            raise RuntimeError(f"{operation}: postcondition returned false")
    return output
