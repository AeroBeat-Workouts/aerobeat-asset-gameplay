# New shell-and-strap knee target (unapproved)

Additive option after the first two target silhouettes read as bunny ears or a location pin. This uses one broad domed turtle-shell shield facing incoming notes (local −Z), a continuous thin white rim, and a dark horizontal strap visibly crossing the lower shell, returning along both sides and across the back of an invisible leg. The main shell `mat/target_tint` is runtime-tintable; trim and strap are structural. Geometry and materials are original procedural Blender 4.0.2 work, inspired by Derrick's concept 03, not a copy. No leg, concept image, texture or external dependency is bundled. The same target could be tinted per left/right beat instance; neither lane convention nor game integration is approved.

`views/front.png`, `side.png`, `back.png`, and `three-quarter.png` show geometry and wrap. `approach-32px.png` and `approach-64px.png` are **isolated 640×640 Blender frames** with nominal projected widths, not native track-size proof. At 32 px the strap/rim may collapse, so human target approval still requires actual far/near/hit states at phone size alongside glove and guard. The rear of the dome is visible through the open leg space; this is a visual cue model, not physical safety equipment.

Rebuild in a **new empty root** on Cookie or another Blender 4.0.2 host:

```bash
blender --background --factory-startup --python tools/generate_knee_shell_strap_candidate.py -- --output-root /tmp/aerobeat-knee-shell-preview-new
```

The generator refuses populated roots and writes only `knee-target/turtle-shell-strap-v1` under its requested root. This folder's `candidate-manifest.json` binds source, GLB, and six PNG hashes for this provisional build. Full immutable-release reproducibility remains unsatisfied; see `../../export-diagnosis.md`. Preserve the earlier target candidates for comparison. No approval, gameplay, or release is implied.
