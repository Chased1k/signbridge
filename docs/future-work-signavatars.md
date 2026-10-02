# SignAvatars — Future Work Reference

> **Status:** NOT PURSUING NOW — saved for future evaluation
> Created: 2026-10-01
> Purpose: Reference document for potential future integration

---

## Why This Is Future Work

Two blockers prevent us from using SignAvatars as our primary dataset:

1. **License: Non-commercial only.** SignAvatars is released under a non-commercial license. StudioGalt is CC0 (public domain). For a commercial product, CC0 is the safe choice.

2. **Access gate: Google Form required.** SignAvatars requires filling out a Google Form and waiting for email approval. StudioGalt is available immediately via `git clone`. No waiting, no gatekeeping.

**Decision:** Start with StudioGalt (CC0, available now). Evaluate SignAvatars later if we need broader vocabulary or different motion data.

---

## SignAvatars Overview

**Source:** SignAvatars (ECCV 2024) — Zhengdi Yu et al., Imperial College London / Tencent AI Lab
**GitHub:** https://github.com/ZhengdiYu/SignAvatars
**Paper:** https://arxiv.org/abs/2310.20436

### What It Is
- First large-scale 3D sign language motion dataset with mesh annotations
- 8.34M precise 3D whole-body SMPL-X annotations
- 70K motion sequences across multiple subsets
- SMPL-X + MANO hand annotations (detailed 3D hand poses)

### Key Specs
- **Format:** .pkl files containing SMPL-X parameters (182-dim per frame)
- **Parameter breakdown:** root_pose, body_pose (21 joints × 3), hand_poses (MANO, 15 joints × 3 per hand), jaw_pose, betas (body shape), expression (facial), cam_trans
- **Frame rate:** 24fps (vs StudioGalt's 60fps posted / 240fps recorded)
- **Rig:** SMPL-X (standardized parametric body model, not a custom rig)
- **Quality:** Estimated/annotated from video (not direct mocap like StudioGalt)

---

## Dataset Subsets (3)

### 1. Word Subset (WLASL) — Most Relevant
- Individual ASL signs, each ~57 frames at 24fps (~2.4 sec avg)
- Signers standing, performing a single sign
- Annotated with word-level English glosses
- ~2,000 unique words from WLASL dataset
- This is the subset most comparable to StudioGalt's dictionary

### 2. Continuous Subset
- Continuous sign language sentences
- Multiple signs per sequence
- Longer animations (varies)
- Useful for: studying transitions between signs, co-articulation

### 3. ABC-59 Subset
- 59-sign alphabet/numbers subset
- Fingerspelling content
- Comparable to StudioGalt's `SG ASL Fingerspelling/`

---

## Gloss Overlap Analysis

- **WLASL vocabulary:** ~2,000 unique words
- **ASLLVD glosses (our POC set):** 2,589 glosses
- **Overlap with ASLLVD:** 1,139 of 2,589 glosses overlap (~44%)
- This means: ~1,139 of our POC glosses would be found in SignAvatars Word subset
- StudioGalt has 2,587 signs — potentially much higher overlap with our gloss list

**Note:** The 44% overlap was a concern. StudioGalt's 2,587 signs likely cover more of our vocabulary since both are comprehensive ASL dictionaries.

---

## SMPL-X Technical Details

### Parameter Space (182-dim per frame)
- `root_pose`: 3-dim (global root rotation)
- `body_pose`: 63-dim (21 joints × 3 axis-angle)
- `left_hand_pose`: 45-dim (15 MANO joints × 3)
- `right_hand_pose`: 45-dim (15 MANO joints × 3)
- `jaw_pose`: 3-dim
- `leye_pose`: 3-dim (left eye)
- `reye_pose`: 3-dim (right eye)
- `betas`: 10-dim (body shape parameters)
- `expression`: 10-dim (facial expression)
- `cam_trans`: 3-dim (camera translation)

### Data Keys (per .pkl)
- `smplx`: smoothed SMPL-X parameters
- `unsmooth_smplx`: raw (unsmoothed) parameters
- `trans`: translation data
- Additional metadata

### Model Files Required
- SMPL-X neutral model (`SMPLX_NEUTRAL.npz` or `.pth`)
- MANO hand models (`MANO_LEFT.pkl`, `MANO_RIGHT.pkl`)
- These are separate downloads (human_model_files)
- License: SMPL-X model files have their own license (non-commercial research)

---

## License Details

- **Dataset:** Non-commercial research license
- **SMPL-X model files:** Non-commercial research (Meshcapade / Max Planck Institute)
- **MANO model files:** Non-commercial research (MPI)
- **All components are non-commercial** — cannot be used in a commercial product without separate licensing

**This is the primary blocker.** Even if we got access, we couldn't use it commercially.

---

## How It Would Integrate (If We Switch Later)

### Option A: SMPL-X → Blender Pipeline
1. Install SMPL-X Blender add-on (zjucxh/smplx_blender_addon or Meshcapade version)
2. Load SMPL-X model in Blender headless
3. Apply .pkl parameters per frame to SMPL-X rig
4. Render using same camera/lighting setup as StudioGalt pipeline
5. NLA composition would work the same way

### Option B: SMPL-X → FBX Export → StudioGalt Rig
1. Load SMPL-X parameters in Python (outside Blender)
2. Convert SMPL-X joint rotations to StudioGalt armature bone rotations
3. Export as FBX
4. Import into Galtis rig (same as StudioGalt FBX pipeline)
5. This would unify both datasets under one rendering pipeline

### Option C: Dual Pipeline
1. Keep StudioGalt pipeline for CC0-safe signs
2. Add separate SignAvatars pipeline for non-commercial use cases
3. Route based on license requirements
4. More complex but preserves commercial safety

### Recommended: Option B
Converting SMPL-X → FBX → Galtis rig would let us use one rendering pipeline for both datasets. The conversion math is straightforward (both use joint rotations in axis-angle or quaternion). The challenge is bone mapping between SMPL-X skeleton and Galtis armature.

---

## What SignAvatars Offers That StudioGalt Doesn't

1. **Continuous sentences** — StudioGalt has individual signs only. SignAvatars Continuous subset has full sentences with natural co-articulation between signs.
2. **Larger vocabulary potential** — 70K sequences total across subsets, vs StudioGalt's 2,587 signs.
3. **Standardized format** — SMPL-X is a widely-supported parametric model. Many tools and add-ons exist. StudioGalt uses custom FBX armature.
4. **Academic backing** — ECCV 2024 paper, ongoing research. Citations and improvements likely.

## What StudioGalt Offers That SignAvatars Doesn't

1. **CC0 license** — commercially safe, no restrictions
2. **Real motion capture** — Xsens Link + StretchSense (direct measurement), vs SignAvatars' estimated/annotated data
3. **Higher frame rate** — 240fps recorded, 60fps posted (vs 24fps)
4. **Blender-native** — .blend rig files, Blender Python scripts, Blender workflow documentation
5. **FBX format** — universal 3D format, works in Blender, Unity, Unreal, etc.
6. **Facial shapekeys** — FACS expressions included on Galtis rig
7. **Available now** — no Google Form, no waiting

---

## Decision Log

- **2026-10-01:** Kellen decided to start with StudioGalt as primary dataset. CC0 license + immediate availability + real mocap + Blender-native = clear winner for commercial product.
- SignAvatars research preserved in this document for future reference.
- If StudioGalt vocabulary proves insufficient (>15% missing signs), revisit SignAvatars as a supplement.
- If we need continuous sentence data (not just individual signs), SignAvatars Continuous subset is the only option.
- Re-evaluate if SignAvatars releases under more permissive license.

---

## Quick Reference

| Attribute | StudioGalt | SignAvatars |
|-----------|-----------|-------------|
| License | CC0 ✅ | Non-commercial ⚠️ |
| Access | Immediate (git clone) | Google Form + wait |
| Signs | 2,587 | ~2,000 (Word) / 70K (all) |
| Format | FBX | .pkl (SMPL-X) |
| Quality | Real mocap | Estimated/annotated |
| Frame rate | 240fps rec / 60fps posted | 24fps |
| Hands | StretchSense gloves | MANO estimation |
| Face | FACS shapekeys | Expression params |
| Blender | Native (.blend rig, scripts) | Add-on required |
| Continuous | No (individual signs) | Yes (Continuous subset) |
| Commercial | Yes ✅ | No ❌ |