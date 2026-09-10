#!/usr/bin/env python3
"""Fail-closed structural validator for isolated tint-dominant 0.0.11 marker candidates."""
from __future__ import annotations
import argparse, hashlib, json, math, struct
from collections import Counter
from pathlib import Path

RELEASE = "0.0.11"
PREDECESSOR = "0.0.10"
ROLES = {"directional-arrow": "rounded-outline-v1", "any-note": "outlined-circle-v1", "guard": "outlined-shield-v1", "bomb": "urchin-v1", "wall": "red-glass-v1", "track": "blue-glass-v1", "athlete-marker": "sphere-v1"}
UNCHANGED = tuple(role for role in ROLES if role != "athlete-marker")
# Expected measured geometry of the re-authored 0.0.11 marker (47-ring x 12-segment UV sphere).
MARKER = {
    "triangles": 1128,
    "vertices_welded": 566,
    "material_triangle_counts": {"mat/charcoal": 120, "mat/white": 48, "mat/tint_base": 960},
    "materials": ["mat/charcoal", "mat/white", "mat/tint_base"],
}


def fail(message): raise AssertionError(message)
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_glb(path):
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    if (magic, version, total) != (b"glTF", 2, len(data)): fail("marker GLB header")
    size, kind = struct.unpack_from("<I4s", data, 12)
    if kind != b"JSON": fail("marker GLB JSON chunk")
    doc = json.loads(data[20:20 + size].decode().rstrip(" \0"))
    offset = 20 + size
    binary_size, binary_kind = struct.unpack_from("<I4s", data, offset)
    if binary_kind != b"BIN\0" or doc.get("images") or doc.get("textures") or any("uri" in value for value in doc.get("buffers", [])): fail("marker GLB must be self-contained")
    return doc, data[offset + 8:offset + 8 + binary_size]


def accessor(doc, binary, index):
    value = doc["accessors"][index]; view = doc["bufferViews"][value["bufferView"]]; start = view.get("byteOffset", 0) + value.get("byteOffset", 0)
    if value["componentType"] == 5126 and value["type"] == "VEC3": return [struct.unpack_from("<fff", binary, start + i * 12) for i in range(value["count"])]
    fmt, width = {5123: ("<H", 2), 5125: ("<I", 4)}[value["componentType"]]
    return [struct.unpack_from(fmt, binary, start + i * width)[0] for i in range(value["count"])]


def validate_marker(path):
    doc, binary = parse_glb(path)
    if len(doc.get("meshes", [])) != 1: fail("marker must have one mesh")
    primitives = doc["meshes"][0]["primitives"]
    if len(primitives) != 3: fail("marker must partition into exactly three material primitives")
    materials = doc.get("materials", [])
    if [m.get("name") for m in materials] != MARKER["materials"]: fail("marker exact ordered material names")
    # All three materials OPAQUE, single-sided, alpha 1, correct aerobeat extras.
    for spec in materials:
        name = spec["name"]
        if spec.get("alphaMode") != "OPAQUE" or spec.get("doubleSided") is not False: fail(f"{name}: must be opaque single-sided")
        factor = spec.get("pbrMetallicRoughness", {}).get("baseColorFactor", [])
        if len(factor) != 4 or factor[3] != 1: fail(f"{name}: base color alpha must be 1")
        expected_extra = {"blend": "opaque", "cull": "back", "depthTest": True, "depthWrite": True, "runtimeTintable": name == "mat/tint_base", "structural": name in ("mat/white", "mat/charcoal")}
        if spec.get("extras", {}).get("aerobeat") != expected_extra: fail(f"{name}: runtime semantics {spec.get('extras')}")
    # Shared POSITION/NORMAL attributes across all primitives; explicit unit radial normals.
    attrs = primitives[0]["attributes"]
    if set(attrs) != {"POSITION", "NORMAL"}: fail("marker primitive attributes must be POSITION+NORMAL")
    if any(p["attributes"] != attrs for p in primitives): fail("marker primitives share POSITION/NORMAL")
    positions = accessor(doc, binary, attrs["POSITION"]); normals = accessor(doc, binary, attrs["NORMAL"])
    if len(positions) != len(normals): fail("marker normal count")
    for position, normal in zip(positions, normals):
        pl = math.sqrt(sum(x * x for x in position)); nl = math.sqrt(sum(x * x for x in normal))
        if abs(nl - 1) > 1e-5 or pl < 1e-9: fail("marker non-unit normal / degenerate vertex")
        # Outward hemisphere sanity: explicit normal must point away from the center.
        if sum(normal[i] * position[i] for i in range(3)) <= 0: fail("marker normal points inward")
    # Reconstruct closed manifold with outward CCW winding and geometric/normal agreement.
    # Split-corner positions are welded back to unique points before topology checks.
    point_map = {}
    def weld(pt):
        key = tuple(round(x, 6) for x in pt)
        if key not in point_map:
            point_map[key] = len(point_map)
        return point_map[key]
    edges = {}; triangles = set(); by_material = {name: [] for name in MARKER["materials"]}
    min_winding = float("inf"); min_agree = 1.0
    for primitive, name in zip(primitives, MARKER["materials"]):
        indices = accessor(doc, binary, primitive["indices"])
        for i in range(0, len(indices), 3):
            tri = tuple(indices[i:i + 3]); wtri = tuple(weld(positions[k]) for k in tri)
            key = tuple(sorted(wtri))
            if key in triangles: fail("marker duplicate/coplanar overlapping face")
            triangles.add(key); by_material[name].append(tri)
            a, b, c = (positions[index] for index in tri)
            u = tuple(b[j] - a[j] for j in range(3)); v = tuple(c[j] - a[j] for j in range(3))
            geo = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            centroid = tuple((a[j] + b[j] + c[j]) / 3 for j in range(3))
            outward = sum(geo[j] * centroid[j] for j in range(3))
            if outward <= 1e-8: fail(f"marker inward/non-outward winding {outward}")
            length = math.sqrt(sum(g * g for g in geo))
            if length <= 1e-12: fail("marker degenerate face")
            unit = tuple(g / length for g in geo)
            for index in tri:
                dotprod = sum(unit[j] * normals[index][j] for j in range(3))
                if dotprod <= .9: fail(f"marker geometric/NORMAL disagreement {dotprod}")
                min_agree = min(min_agree, dotprod)
            min_winding = min(min_winding, outward)
            for x, y in zip(wtri, (wtri[1], wtri[2], wtri[0])):
                edge = tuple(sorted((x, y))); edges[edge] = edges.get(edge, 0) + 1
    if len(triangles) != MARKER["triangles"]: fail(f"marker triangle count {len(triangles)} != {MARKER['triangles']}")
    if any(count != 2 for count in edges.values()): fail("marker surface is not closed two-manifold")
    counts = {name: len(faces) for name, faces in by_material.items()}
    if counts != MARKER["material_triangle_counts"]: fail(f"marker material partition {counts}")
    lo = [min(p[k] for p in positions) for k in range(3)]; hi = [max(p[k] for p in positions) for k in range(3)]
    if any(abs(lo[k] + 0.09) > 2e-4 or abs(hi[k] - 0.09) > 2e-4 for k in range(3)): fail(f"marker bounds {lo}..{hi}")
    # Every cardinal hemisphere must expose all three materials (exterior visible with culling).
    visibility = {}
    for label, axis, sign in (("+X", 0, 1), ("-X", 0, -1), ("+Y", 1, 1), ("-Y", 1, -1), ("+Z", 2, 1), ("-Z", 2, -1)):
        seen = {name for name, faces in by_material.items() if any(sign * sum(positions[index][axis] for index in tri) > 1e-9 for tri in faces)}
        if seen != set(MARKER["materials"]): fail(f"marker materials not visible from {label}: {seen}")
        visibility[label] = sorted(seen)
    return {"closed_surface": True, "welded_vertices": MARKER["vertices_welded"], "explicit_cornets": len(positions), "triangles": len(triangles), "material_triangle_counts": counts, "explicit_unit_radial_normals": True, "outward_ccw": True, "min_winding_dot_centroid": round(min_winding, 12), "min_geometric_normal_agreement": round(min_agree, 6), "bounds": [lo, hi], "camera_material_visibility": visibility, "sha256": sha(path), "bytes": path.stat().st_size}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--authority-root", required=True); ap.add_argument("--candidate-root", required=True)
    ap.add_argument("--source-commit"); ap.add_argument("--source-tree"); ap.add_argument("--canonical", action="store_true"); a = ap.parse_args()
    authority = Path(a.authority_root).resolve(); candidate = Path(a.candidate_root).resolve()
    raw = candidate / "release/raw" / RELEASE; review = candidate / "review" / RELEASE
    if not raw.is_dir() or not review.is_dir(): fail("release and review trees are required")
    if a.canonical:
        if candidate != authority: fail("canonical validation requires candidate root equal authority root")
    elif raw.resolve().is_relative_to((authority / "release/raw").resolve()): fail("candidate must be isolated")
    inventory = load(raw / "inventory.v1.json"); proof = load(raw / "proof.v1.json")
    files = [path for path in raw.rglob("*") if path.is_file()]
    if len(files) != 17 or inventory.get("release") != RELEASE or inventory.get("expected_asset_count") != 7: fail("exact candidate raw inventory")
    if sha(raw / "inventory.v1.json") != proof.get("inventory_sha256"): fail("proof inventory binding")
    if proof.get("claims", {}).get("changed_identities") != ["athlete-marker/sphere-v1"]: fail("proof marker-only scope")
    if proof["claims"].get("byte_identical_predecessor_roles") != list(UNCHANGED): fail("proof predecessor roles scope")
    if a.source_commit and proof.get("source_authority", {}).get("commit") != a.source_commit: fail("proof source commit")
    if a.source_tree and proof.get("source_authority", {}).get("tree") != a.source_tree: fail("proof source tree")
    # Six unchanged roles byte-identical to immutable 0.0.10 (GLBs and release manifests).
    for role in UNCHANGED:
        variant = ROLES[role]
        for relative in (Path(role) / f"{variant}.glb", Path("manifests") / role / f"{variant}.v1.json"):
            if (raw / relative).read_bytes() != (authority / "release/raw" / PREDECESSOR / relative).read_bytes(): fail(f"unchanged predecessor drift: {relative}")
    marker = validate_marker(raw / "athlete-marker/sphere-v1.glb")
    manifest = load(raw / "manifests/athlete-marker/sphere-v1.v1.json"); source_manifest = load(candidate / "manifests/athlete-marker/sphere-v1.v1.json")
    for document in (manifest, source_manifest):
        if document.get("release") != RELEASE or document.get("identity", {}).get("canonical_name") != "athlete-marker/sphere-v1": fail("marker manifest identity/release")
        if document.get("geometry", {}).get("triangle_count") != MARKER["triangles"]: fail("marker manifest triangle count")
        if document["geometry"].get("triangle_budget") != 1200: fail("marker manifest triangle budget")
        if document.get("materials", {}).get("names") != MARKER["materials"]: fail("marker manifest material names")
        contract = document.get("materials", {}).get("contract", {})
        if contract.get("runtime_tint_material") != "mat/tint_base" or contract.get("structural_materials") != ["mat/white", "mat/charcoal"]: fail("marker manifest structural contract")
        if contract.get("winding") != "outward-ccw" or contract.get("cull") != "back" or contract.get("depth_write") is not True or contract.get("opacity") != 1.0: fail("marker manifest render contract")
        if contract.get("tint_dominant") is not True: fail("marker manifest must record tint dominance")
    if source_manifest.get("files", {}).get("source_sha256") != sha(candidate / "source/athlete-marker/sphere-v1/sphere-v1.blend"): fail("marker source hash")
    if source_manifest["files"].get("release_sha256") != marker["sha256"] or source_manifest["files"].get("release_bytes") != marker["bytes"]: fail("marker release hash")
    # Predecessor marker bytes must still be present and immutable in the authority.
    pred = authority / "release/raw" / PREDECESSOR / "athlete-marker/sphere-v1.glb"
    if not pred.is_file(): fail("missing immutable 0.0.10 predecessor marker")
    if marker["sha256"] == sha(pred): fail("successor marker identical to predecessor (no change)")
    setdoc = load(raw / "sets/default-v1.json")
    if setdoc.get("release") != RELEASE or setdoc.get("roles") != ROLES or (candidate / "sets/default-v1.json").read_bytes() != (raw / "sets/default-v1.json").read_bytes(): fail("candidate set contract")
    pngs = {path.name for path in review.glob("*.png")}; jsons = {path.name for path in review.glob("*.json")}
    if len(pngs) != 83 or jsons != {"hashes.v1.json", "layout.v1.json", "visibility.v1.json", "contrast.v1.json", "wall-grid.v1.json"}: fail("exact review inventory")
    marker_faces = {f"athlete-marker--sphere-v1--{face}-{background}.png" for face in ("plus-x", "minus-x", "plus-y", "minus-y", "plus-z", "minus-z") for background in ("bright", "dark")}
    if not marker_faces <= pngs: fail("marker multi-angle review matrix")
    layout = load(review / "layout.v1.json").get("images", {})
    hashes = load(review / "hashes.v1.json")
    if {entry["path"] for entry in hashes.get("files", [])} != pngs or any(entry["sha256"] != sha(review / entry["path"]) for entry in hashes["files"]): fail("review hash binding")
    contrast = load(review / "contrast.v1.json")
    if contrast.get("geometry", {}).get("material_triangle_counts") != MARKER["material_triangle_counts"]: fail("contrast evidence material counts")
    if contrast.get("geometry", {}).get("tint_dominant") is not True: fail("contrast evidence tint dominance")
    visibility = load(review / "visibility.v1.json")
    if visibility.get("geometry", {}).get(RELEASE, {}).get("triangles") != MARKER["triangles"]: fail("visibility evidence triangle count")
    print(json.dumps({"oracle": "tint-dominant-marker-candidate", "release": RELEASE, "marker": marker, "unchangedRoles": list(UNCHANGED), "reviewPngs": len(pngs), "tintDominant": True, "pass": True}, sort_keys=True))


if __name__ == "__main__": main()
