# Sprint 6 — Galtis scene, animation transfer, and rendering results

Run date: 2026-10-02  
Host: Watchtower, macOS 14.8.5, Intel i9-9980HK, Blender 4.5.14 LTS

## Outcome

Sprint 6 is complete. SignBridge now has a reusable headless Galtis scene, reusable StudioGalt FBX import/retarget/transfer code, a single-sign MP4 orchestrator, measured Cycles CPU configurations, and a load-once three-sign batch renderer.

## Deliverables

| Deliverable | Result |
| --- | --- |
| `scripts/blender/setup_scene.py` | 50 mm front-facing medium camera, three area lights, dark-gray world, green-screen option, 720p/30 fps, Cycles CPU/64 samples |
| `scripts/blender/sign_importer.py` | No Mesh Full FBX import, mesh removal, reusable bone remap, Blender action-slot binding, constraint release, transfer, and 60→30 fps retiming |
| `scripts/blender/render_sign.py` | Galtis load → scene setup → FBX import → transfer → exact PNG range → H.264 MP4 |
| `scripts/blender/benchmark_render.py` | Reproducible three-configuration still benchmark |
| `scripts/blender/batch_render.py` | One Galtis load with three sequential sign renders |
| First animated render | `output/first_sign_render.mp4` |
| Batch outputs | `output/batch_test/` |
| Reusable scene | `output/galtis_signbridge_scene.blend` |

## Import and transfer validation

Five different `no_mesh_full` FBXs imported and transferred successfully:

| Sign | Mapped/action-driven bones | Import + transfer test |
| --- | ---: | ---: |
| Hello | 331 | 1.181s |
| Biological Mother | 331 | 1.014s |
| Please | 331 | 0.844s |
| Anymore (older export) | 94 mapped / 96 driven | 0.302s |
| Born Again | 331 | 0.985s |

The recent exports contain a larger rig subset than the older Anymore export, but both layouts work through the explicit export-name map plus normalized-name fallback.

Two Blender-specific transfer issues were fixed:

1. Intermediate Galtis bones are constrained to FK/IK controls, so constraints on action-driven bones must be muted for baked FBX transforms to take effect.
2. Blender 4.4+ copied actions retain a source action slot; the target armature must explicitly select that slot or the action remains visually static.

The first, midpoint, and last Hello frames show T-pose/entry, the raised-hand Hello motion, and a neutral exit respectively. The Galtis mesh is the only rendered character; imported meshes are removed and imported armatures are hidden and then deleted.

## First animated sign

Source: `Hello`, latest indexed No Mesh Full variant dated 2024-06-09.

| Metric | Result |
| --- | ---: |
| Output | `output/first_sign_render.mp4` |
| Codec | H.264 |
| Resolution | 1280×720 |
| Frame rate | 30 fps |
| Output frames | 67 |
| Duration | 2.233s |
| Samples | 64 |
| Import | approximately 2s |
| Transfer/retime | approximately 3s |
| Render + encode | 668.860s |
| Render per frame | 9.983s |
| Total pipeline | 672.999s |

StudioGalt actions are authored at 60 fps. The copied action is retimed to 30 fps before transfer, preserving motion duration. Rendering uses an exact temporary PNG sequence followed by ffmpeg H.264 encoding; this avoids saved Blender preview ranges and makes the frame count deterministic.

## Benchmarks

| Configuration | Resolution | Samples | Time/frame |
| --- | ---: | ---: | ---: |
| Development | 640×360 | 32 | 1.884s |
| Standard | 1280×720 | 64 | 5.322s |
| Quality | 1280×720 | 128 | 9.261s |

These are warmed single-still measurements. See `docs/sprint6-render-benchmarks.md` for interpretation.

## Batch result

Hello, Biological Mother, and Please rendered sequentially with one base-scene load at 640×360/32 samples. The batch produced 237 frames in 686.311 seconds and averaged 2.81–2.87 seconds per rendered frame. All three MP4s passed ffprobe validation. See `docs/sprint6-batch-test.md`.

## Known constraints

- Eevee remains unusable on this host because the AMD Metal path stalls; every Sprint 6 render uses Cycles CPU.
- The Galtis source file was written by Blender 5.1.29 and opens in 4.5.14 with a compatibility warning.
- Rendering dominates wall time. Imports and transfers are small compared with animated Cycles geometry updates.
- The first Hello frame is the source clip's T-pose/entry frame. Sprint 8 composition should trim clip handles and blend neutral transitions.
