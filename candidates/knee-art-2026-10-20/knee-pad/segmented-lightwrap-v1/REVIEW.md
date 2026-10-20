# Segmented light-wrap wearable knee pad — unapproved candidate

Derrick clarified that the **wearable equipment** inspiration is the read-only Cookie concept `/home/derrick/Pictures/aerobeat_knee_pad_renders_01.png`, SHA-256 `b3b08b5a29b9061bd3da7ce8a3100d30e13bfe39b3e8e718c26abc7a6c80b911`. It shows a prominent segmented white front, cyan translucent S-curves, circular blue front light, padded gray sleeve and two broad rear straps. The concept is not an exact-pixel or licensed mesh reference. No concept image, text, person, borrowed material or texture is in this candidate.

This **new** procedural Blender4.0.2 model is separate from the simpler blue `dome-strap-v1` candidate and all floating knee strike **targets**. Local +Y is up, front is −Z. The same equipment mesh/GLB is intended to be instanced at both knees. One `mat/glove_match_tint` slot can independently take left/right song glove colors; blue center light and white/gray structure are fixed. The preview uses a white central plate, separated upper/lower/side caps, cyan S-curves and side insets, gray padded side bolsters and two broad rear straps. The empty rear leg tunnel is never filled by a modeled leg in the `.blend` or GLB.

`views/front.png`, `side.png`, `back.png`, `three-quarter.png` inspect the isolated source. `lowered-pair-{a,b}-{front,side,back}.png` and `raised-pair-{a,b}-{front,side,back}.png` are **illustrative** paired poses with review-only neutral cylinders: pair A cyan/magenta; pair B yellow/royal-blue. The cylinders and instance colors are excluded from the editable base scene and GLB. Raised poses are manually angled, not MediaPipe tracking, fitted human limbs, physical ergonomic proof, or native renderer evidence. White segments appear gray in this studio lighting; cyan accent and round light dominate some views. Derrick must decide whether that contrast is acceptable rather than treating source render completion as pad approval.

On Cookie Blender4.0.2, rebuild into a **new empty root** and check imports:

```bash
blender --background --factory-startup --python tools/generate_segmented_knee_pad_candidate.py -- --output-root /tmp/aerobeat-segmented-pad-new
python3 tools/validate_segmented_knee_pad_candidate.py --candidate-root /tmp/aerobeat-segmented-pad-new --smoke
```

The provisional `candidate-manifest.json` binds this build's `.blend`, GLB and 16 labeled PNGs with hashes and measured geometry. It is **not** a canonical release v1 manifest. Existing reproducibility Bead `.11` must pass strict independent exports before any immutable release. Native representative leg poses in PlayCanvas are deferred until after the A signed public source gate so the renderer commit `bdccb55` remains fixed. Pad design decision `.9` remains separately unanswered from target decision `.10`. No product pin, gameplay, release or UI change.
