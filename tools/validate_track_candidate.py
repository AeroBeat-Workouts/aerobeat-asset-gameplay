#!/usr/bin/env python3
"""Strict geometry, material, custody, review and Blender smoke gate for 0.0.12."""
from __future__ import annotations
import argparse, hashlib, json, math, shutil, struct, subprocess
from collections import Counter
from pathlib import Path
from subprocess_contract import run_checked

RELEASE = "0.0.12"
PREDECESSOR = "0.0.11"
ROLES = {"directional-arrow": "rounded-outline-v1", "any-note": "outlined-circle-v1", "guard": "outlined-shield-v1", "bomb": "urchin-v1", "wall": "red-glass-v1", "track": "blue-glass-v1", "athlete-marker": "sphere-v1"}
UNCHANGED = tuple(role for role in ROLES if role != "track")
RAILS = (-2, -1, 0, 1, 2)


def check(condition, message):
    if not condition: raise AssertionError(message)


def load(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(root):
    files = sorted(p for p in root.rglob("*") if p.is_file())
    rows = "".join(f"{p.relative_to(root).as_posix()}\0{p.stat().st_size}\0{sha(p)}\n" for p in files)
    return len(files), sum(p.stat().st_size for p in files), hashlib.sha256(rows.encode()).hexdigest()


def parse_glb(path):
    data = path.read_bytes()
    check(len(data) >= 28 and struct.unpack_from("<4sII", data) == (b"glTF", 2, len(data)), "GLB header")
    size, kind = struct.unpack_from("<I4s", data, 12)
    check(kind == b"JSON", "GLB JSON chunk")
    doc = json.loads(data[20:20 + size].decode().rstrip(" \0"))
    offset = 20 + size
    binary_size, binary_kind = struct.unpack_from("<I4s", data, offset)
    check(binary_kind == b"BIN\0" and offset + 8 + binary_size == len(data), "GLB binary chunk")
    check(not doc.get("images") and not doc.get("textures") and not any("uri" in v for v in doc.get("buffers", [])), "GLB external dependency or image")
    check(doc["buffers"] == [{"byteLength": binary_size}], "GLB buffer declaration")
    return doc, data[offset + 8:]


def accessor(doc, binary, index):
    a = doc["accessors"][index]; view = doc["bufferViews"][a["bufferView"]]
    start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
    if a["componentType"] == 5126 and a["type"] == "VEC3":
        return [struct.unpack_from("<fff", binary, start + i * 12) for i in range(a["count"])]
    fmt, width = {5123: ("<H", 2), 5125: ("<I", 4)}[a["componentType"]]
    check(a["type"] == "SCALAR", "index accessor type")
    return [struct.unpack_from(fmt, binary, start + i * width)[0] for i in range(a["count"])]


def close(a, b, tol=1e-5): return abs(a - b) <= tol


def validate_track(path, predecessor):
    doc, binary = parse_glb(path); old, _ = parse_glb(predecessor)
    check(doc["nodes"] == [{"mesh": 0, "name": "track/blue-glass-v1"}] and len(doc["meshes"]) == 1, "canonical node and one mesh")
    check(doc["meshes"][0]["name"] == "track/blue-glass-v1/mesh", "canonical mesh name")
    materials = doc.get("materials", []); old_materials = old.get("materials", [])
    check(materials == old_materials and [m["name"] for m in materials] == ["mat/blue_glass", "mat/cyan_edge"], "materials must be byte-equivalent semantics to predecessor")
    check(materials[0]["alphaMode"] == "BLEND" and materials[0]["pbrMetallicRoughness"]["baseColorFactor"] == [0.1, 0.58, 0.92, 0.52], "translucent blue glass")
    check(materials[0]["extras"]["aerobeat"] == {"blend": "alpha", "cull": "back", "depthTest": True, "depthWrite": False, "order": "after-grid-before-wall"}, "glass depth/blend semantics")
    check(materials[1]["pbrMetallicRoughness"]["baseColorFactor"] == [0.05, 0.8, 1.0, 1] and materials[1]["extras"]["aerobeat"]["depthWrite"] is True, "opaque cyan edge semantics")
    primitives = doc["meshes"][0]["primitives"]
    check(len(primitives) == 2 and [p["material"] for p in primitives] == [0, 1], "glass plus rails primitives")
    attrs = primitives[0]["attributes"]
    check(attrs == {"POSITION": 0} and all(p["attributes"] == attrs and p["mode"] == 4 for p in primitives), "primitive layout")
    points = accessor(doc, binary, 0)
    check(len(points) == 48, "one box and exactly five rail boxes")
    faces = []
    for primitive in primitives:
        indices = accessor(doc, binary, primitive["indices"])
        check(len(indices) % 3 == 0 and all(0 <= i < len(points) for i in indices), "triangle indices")
        faces.append([tuple(indices[i:i + 3]) for i in range(0, len(indices), 3)])
    check([len(f) for f in faces] == [12, 60], "one glass box plus five continuous rails, no segmented joins")
    glass_points = points[:8]
    def point_set(values): return {tuple(round(x, 5) for x in point) for point in values}
    def corners(x0, x1, y0, y1): return {(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (-36, 36)}
    check(point_set(glass_points) == corners(-2.1, 2.1, -0.06, 0), "glass exact 4.2WU width, 0.06 height, continuous ±36 depth")
    expected = [corners(x - .012, x + .012, -.006, 0) for x in RAILS]
    check([point_set(points[8 + 8*i:16 + 8*i]) for i in range(5)] == expected, "five rails at canonical beat boundaries ±2, ±1, 0")
    for material_index, group in enumerate(faces):
        expected_groups = [(0, 8)] if material_index == 0 else [(8 + 8*i, 16 + 8*i) for i in range(5)]
        seen = set()
        for first, last in expected_groups:
            group_faces = [tri for tri in group if all(first <= index < last for index in tri)]
            check(len(group_faces) == 12, "one closed box per continuous component")
            seen.update(group_faces)
            edges = Counter(tuple(sorted(edge)) for a, b, c in group_faces for edge in ((a, b), (b, c), (c, a)))
            check(len(edges) == 18 and set(edges.values()) == {2}, "closed nonsegmented two-manifold component")
            for tri in group_faces:
                a, b, c = (points[index] for index in tri)
                u = [b[k] - a[k] for k in range(3)]; v = [c[k] - a[k] for k in range(3)]
                normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
                check(math.sqrt(sum(n*n for n in normal)) > 1e-7, "nondegenerate triangle")
        check(len(seen) == len(group), "no cross-component or duplicate faces")
    lo = [min(p[i] for p in points) for i in range(3)]; hi = [max(p[i] for p in points) for i in range(3)]
    check(all(close(lo[i], [-2.1, -.06, -36][i]) and close(hi[i], [2.1, 0, 36][i]) for i in range(3)), "track exact AABB")
    check(sha(path) != sha(predecessor), "new track must differ from 0.0.11")
    return {"sha256": sha(path), "bytes": path.stat().st_size, "triangles": sum(map(len, faces)), "glass_triangles": 12, "rail_triangles": 60, "rail_centers_x": list(RAILS), "aabb": [lo, hi]}


def smoke(blender, authority, candidate):
    check(shutil.which(blender) is not None, "Blender 4.0.2 unavailable")
    version = subprocess.check_output([blender, "--version"], text=True).splitlines()[0]
    check(version == "Blender 4.0.2", f"wrong Blender version: {version}")
    identity = "track/blue-glass-v1"
    for kind, script, target in (
        ("source", "smoke_source.py", candidate / "source/track/blue-glass-v1/blue-glass-v1.blend"),
        ("glb", "smoke_import.py", candidate / f"release/raw/{RELEASE}/track/blue-glass-v1.glb"),
    ):
        marker = f"SMOKE_OK kind={kind} identity={identity}"
        run_checked([blender, "--background", "--factory-startup", "--python", str(authority / "tools" / script), "--", str(target), identity], operation=f"track {kind} smoke", marker=marker, postcondition=lambda: target.is_file())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-root", required=True); parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--source-commit", required=True); parser.add_argument("--source-tree", required=True)
    parser.add_argument("--canonical", action="store_true"); parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    authority = Path(args.authority_root).resolve(); candidate = Path(args.candidate_root).resolve()
    raw = candidate / f"release/raw/{RELEASE}"; review = candidate / f"review/{RELEASE}"
    check(raw.is_dir() and review.is_dir(), "release and review trees required")
    check(candidate == authority if args.canonical else not raw.is_relative_to(authority / "release/raw"), "canonical/candidate separation")
    expected_raw = {"inventory.v1.json", "proof.v1.json", "sets/default-v1.json"}
    for role, variant in ROLES.items(): expected_raw.update((f"{role}/{variant}.glb", f"manifests/{role}/{variant}.v1.json"))
    check({p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file()} == expected_raw, "exact 17-file release inventory")
    inventory = load(raw / "inventory.v1.json"); proof = load(raw / "proof.v1.json")
    check(inventory["release"] == RELEASE and inventory["immutable"] is True and inventory["expected_asset_count"] == 7, "release inventory header")
    payload = {entry["path"]: entry for entry in inventory["payload"]}
    check(set(payload) == expected_raw - {"inventory.v1.json", "proof.v1.json"}, "inventory payload paths")
    for name, entry in payload.items():
        check(entry["bytes"] == (raw / name).stat().st_size and entry["sha256"] == sha(raw / name), f"payload hash: {name}")
    check(proof["release"] == RELEASE and proof["inventory_sha256"] == sha(raw / "inventory.v1.json"), "release proof binding")
    check(proof["source_authority"] == {"commit": args.source_commit, "tree": args.source_tree}, "release proof source authority")
    claims = proof["claims"]
    check(claims["changed_identities"] == ["track/blue-glass-v1"] and claims["byte_identical_predecessor_roles"] == list(UNCHANGED), "track-only scope proof")
    check(claims["track"]["rail_centers_x"] == list(RAILS) and claims["track"]["continuous_depth"] == 72 and claims["track"]["segment_joins"] is False, "track release proof")
    for role in UNCHANGED:
        variant = ROLES[role]
        for relative in (f"{role}/{variant}.glb", f"manifests/{role}/{variant}.v1.json"):
            check((raw / relative).read_bytes() == (authority / f"release/raw/{PREDECESSOR}" / relative).read_bytes(), f"predecessor byte identity {relative}")
    track_file = raw / "track/blue-glass-v1.glb"
    track = validate_track(track_file, authority / f"release/raw/{PREDECESSOR}/track/blue-glass-v1.glb")
    source_manifest = load(candidate / "manifests/track/blue-glass-v1.v1.json")
    release_manifest = load(raw / "manifests/track/blue-glass-v1.v1.json")
    source_file = candidate / "source/track/blue-glass-v1/blue-glass-v1.blend"
    for doc in (source_manifest, release_manifest):
        check(doc["release"] == RELEASE and doc["identity"]["canonical_name"] == "track/blue-glass-v1", "manifest identity")
        geo = doc["geometry"]
        check(geo["dimensions"] == [4.2, .06, 72] and geo["pivot"] == [0, .03, 0] and geo["triangle_count"] == 72 and geo["triangle_budget"] == 160, "track manifest dimensions, pivot, budget")
        check(geo["collision_free_bound"] == [[-2.14,-.04,-36.04],[2.14,.08,36.04]], "track collision-free bounds")
        check(all(close(geo["measured_aabb"][j][i], track["aabb"][j][i]) for j in range(2) for i in range(3)), "track measured AABB")
        check(doc["files"]["release_sha256"] == track["sha256"] and doc["files"]["release_bytes"] == track["bytes"], "track manifest payload hash")
        check(doc["materials"]["names"] == ["mat/blue_glass", "mat/cyan_edge"] and doc["materials"]["analytic_only"] is True and doc["materials"]["textures"] == [], "track analytic material manifest")
        contract = doc["materials"]["contract"]
        check(contract["rail_centers_x"] == list(RAILS) and contract["continuous_depth"] == 72 and contract["segment_joins"] is False and contract["opacity"] == .52 and contract["depth_write"] is False, "track material/reuse contract")
        check(doc["reuse"] == "one continuous 72-unit mesh; renderer shifts the near edge by frame extension without segment reuse or width scaling", "track reuse description")
    check(source_manifest["files"]["source_sha256"] == sha(source_file) and source_manifest["files"]["source_bytes"] == source_file.stat().st_size, "source snapshot hash")
    check("source_sha256" not in release_manifest["files"] and "source_bytes" not in release_manifest["files"], "release manifest omits nondeterministic source hash")
    check(source_manifest["provenance"]["blender"] == "4.0.2" and source_manifest["rights"]["license"] == "CC-BY-NC-4.0", "toolchain and rights")
    setdoc = load(raw / "sets/default-v1.json")
    check(setdoc["release"] == RELEASE and setdoc["roles"] == ROLES and (raw / "sets/default-v1.json").read_bytes() == (candidate / "sets/default-v1.json").read_bytes(), "seven-role set")
    review_files = {p.name for p in review.iterdir() if p.is_file()}
    expected_review_json = {"hashes.v1.json", "layout.v1.json", "visibility.v1.json", "contrast.v1.json", "wall-grid.v1.json"}
    pngs = {name for name in review_files if name.endswith(".png")}
    check(len(pngs) == 83 and review_files == pngs | expected_review_json, "review inventory 83 PNG + 5 JSON")
    hashes = load(review / "hashes.v1.json")
    check(hashes["release"] == RELEASE and {record["path"] for record in hashes["files"]} == pngs, "review hashes inventory")
    for record in hashes["files"]:
        path = review / record["path"]
        check(record["bytes"] == path.stat().st_size and record["sha256"] == sha(path), f"review PNG hash {path.name}")
    for key, name in (("layout", "layout.v1.json"), ("visibility", "visibility.v1.json"), ("contrast", "contrast.v1.json"), ("wall_grid", "wall-grid.v1.json")):
        check(hashes[key] == {"path": name, "bytes": (review / name).stat().st_size, "sha256": sha(review / name)}, f"review metadata hash {name}")
    if args.smoke: smoke(shutil.which("blender") or "blender", authority, candidate)
    print(json.dumps({"release": RELEASE, "track": track, "raw": digest(raw), "review": digest(review), "unchanged_glbs": list(UNCHANGED), "blender_smoke": args.smoke, "pass": True}, sort_keys=True))


if __name__ == "__main__": main()
