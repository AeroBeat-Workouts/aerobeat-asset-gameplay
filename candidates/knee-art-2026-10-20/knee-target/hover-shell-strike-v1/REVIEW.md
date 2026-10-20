# Floating knee strike target — provisional, not approved

**Source inspiration:** Derrick's read-only Cookie concept `/home/derrick/Pictures/aerobeat_knee_strike_renders_01.png`, SHA-256 `dc5ba327633c50d28c777e638db4f2d7317a02b34aecb16f5fcb563b3d2a0bba`. We inspected it visually: hovering white rounded upper shell, cyan rim, luminous lime underside pad, and optional ground projection. No concept pixels, person, text, logo, texture or font were copied. The original procedural Blender geometry uses analytic materials only.

This is a **target beat**, not the wearable knee pad. Compared with the earlier `turtle-shell-strap-v1` target's blue vertical shield and dark lower strap, it is a horizontal white dome/cyan lip with a broad yellow-green strike underside and no leg wrap. It is separately addressable, not a replacement in any set or release. The front/approach view is a slightly below-level +Z camera so the lower impact patch remains visible. The underside view faces -Y. Material `mat/cyan_rim` is analytically alpha-blended; mobile depth sorting is untested, and the broad lime/white fields, not transparency, must carry the silhouette.

Images are labeled `front`, `side`, `back`, `underside`, `three-quarter`, `approach-32px`, `approach-64px`. The last two are isolated Blender 640×640 frames with nominal **32/64-pixel widths**, not native PlayCanvas or phone presentation. At 32 pixels the white dome, lime lower patch and a narrow cyan divider are visible; the translucent depth, thin rim edge and any hover projection do not read. At actual **15–21px far size**, no claim of legibility or distinction beside punch/guard is possible yet. We deliberately omitted the optional hover cone/ring because a thin cue would disappear at far size and might confuse the collider location.

Rebuild on Blender 4.0.2 into a **new empty root**:

```bash
blender --background --factory-startup --python tools/generate_hover_strike_candidate.py -- --output-root /tmp/aerobeat-hover-strike-new
python3 tools/validate_hover_strike_candidate.py --candidate-root /tmp/aerobeat-hover-strike-new --smoke
```

The first-generation validator checks exact per-build hashes, GLB structure/material roles, geometry budget and Blender scene/GLB smoke imports. This is a provisional inventory, **not** a strict canonical v1 release manifest or proof of bitwise reproducibility. Earlier art candidate exports showed geometric BIN nondeterminism; final reproducible export remains separately gated (`gmnl.11`). Native renderer review and any target approval (`gmnl.10`) wait until the A2 signed public release preserves renderer provenance. No release, renderer pin, gameplay, UI copy, or human approval is included. Bead `gmnl.13` remains open until native evidence.
