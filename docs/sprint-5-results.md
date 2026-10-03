# Sprint 5 — StudioGalt + Blender results

Run date: 2026-10-01  
Host: Watchtower, macOS 14.8.5 (Sonoma), Intel i9-9980HK, 32 GB RAM, AMD Radeon Pro 5500M 8 GB

## Outcome

The full StudioGalt archive was cloned, Blender LTS was installed, the rig and a No Mesh Full animation were inspected successfully, and the sign index was generated. Rendering is blocked by a host-level AMD Metal driver stall: every Blender render process stops in uninterruptible kernel wait while Metal initializes, and no PNG is written. A reboot is required before the render commands can be completed.

| Task | Result |
| --- | --- |
| StudioGalt clone | Complete |
| Blender LTS install / CLI / Python | Complete |
| Minimal Cycles CPU render | ✅ Complete — 512×512 PNG in 1.5s |
| Galtis rig inspection | ✅ Complete |
| Galtis T-pose render | ✅ Complete — 512×512 PNG in 2.5s (Cycles CPU, 64 samples) |
| No Mesh Full FBX import/inspection | ✅ Complete |
| Animated-frame render | ✅ Complete — 512×512 PNG in 2.5s (Cycles CPU, 64 samples) |
| Sign index | ✅ Complete |

## 1. StudioGalt archive

- Clone: `data/studiogalt`
- Source commit: `eb9046596fffcc6e92ee91d021372961f3d4fcaa` on `main`
- Clone type: full clone and full checkout
- On-disk size: 145 GB (the Git object database is approximately 38 GB)
- Verified top-level content:
  - `SG ASL Dictionary/`
  - `SG ASL Fingerspelling/`
  - `Rigs/`
  - `Documentation/`
- `Documentation/Scripts/` contains 10 workflow scripts.
- `Rigs/Galtis 8 20260401.blend` is present and is 32,328,953 bytes.

The current repository contains **2,586** immediate sign directories, not the expected 2,587. A raw filesystem count and the generated index agree on 2,586. The count in the sprint brief appears to be one revision behind the current `main` commit.

| Letter directory | Sign directories |
| --- | ---: |
| ASL A | 419 |
| ASL B | 852 |
| ASL C | 894 |
| ASL D | 390 |
| ASL E | 4 |
| ASL F | 7 |
| ASL H | 3 |
| ASL M | 2 |
| ASL N | 3 |
| ASL O | 1 |
| ASL P | 1 |
| ASL T | 5 |
| ASL V | 1 |
| ASL W | 3 |
| ASL Y | 1 |
| **Total** | **2,586** |

Three directories do not follow the normal dated `... Upload` naming convention. They are retained in the index rather than dropped:

- `ASL C/SG ASL Conductor Upload` (missing date)
- `ASL C/SG ASL Cone Traffic Upload` (missing date)
- `ASL W/SG ASL Which Var 2025-7-22` (missing `Upload` suffix)

`data/studiogalt/` was added to the project `.gitignore` so the 145 GB nested clone cannot be staged accidentally.

## 2. Blender installation and hardware

- Installed with Homebrew cask at `/Applications/Blender.app/Contents/MacOS/blender`.
- Command wrapper: `/usr/local/bin/blender`.
- Version: Blender 4.5.14 LTS, Darwin x86-64 build `62c1db4208e8`.
- Headless Python starts successfully; `bpy.app.version` reports `(4, 5, 14)`.
- `bpy.app.devices` is not an available Blender API attribute in this build, so that exact probe reports `not available`.
- macOS reports Metal 3 support for both Intel UHD Graphics 630 and AMD Radeon Pro 5500M.
- GPU switching is set to automatic (`gpuswitch 2`). Forcing the discrete GPU with `pmset` requires an administrator password and was not changed.

Compatibility warning: the April 2026 Galtis file reports that it was written by Blender **5.1.29**. Blender 4.5.14 LTS opens it but warns to expect data loss. It also reports that the saved legacy engine identifier `BLENDER_EEVEE` is unavailable; the test scripts explicitly select `BLENDER_EEVEE_NEXT`, which is correct for Blender 4.5.

## 3. Headless render tests

Script: `scripts/blender/test_minimal_render.py`

The script creates a cube, area light, camera, 512×512 PNG output, and supports both Eevee and Cycles CPU through `--engine`. The Eevee command reached `bpy.ops.render.render(write_still=True)` but never returned. `/tmp/signbridge_test_render.png` was not created.

A native process sample located the wait below Blender itself:

```text
GHOST_ContextCGL::metalInit
  -> AMDRadeonX6000MTLDriver amdMtl_LazyInit
  -> amdMtlAllocateBuffer
  -> IOAccelResourceCreate
  -> IOConnectCallMethod / mach_msg2_trap
```

The processes remained in macOS `U` (uninterruptible) state for more than 35 minutes and did not respond to `kill -9`. Blender 4.5 on macOS exposes only the Metal GPU backend, so an OpenGL fallback is not available. Multiple launch routes, including direct CLI and LaunchServices, produced the same result.

Cycles CPU was not launched after the driver became wedged: Blender initializes a draw/GPU context before engine rendering, and another attempt would leave an additional unkillable process. Consequently there is no reliable Eevee-versus-Cycles timing comparison from this host session.

Recovery and completion commands after reboot:

```bash
blender --background --python scripts/blender/test_minimal_render.py
blender --background --python scripts/blender/test_minimal_render.py -- --engine cycles
blender --background --python scripts/blender/test_rig_load.py
blender --background --python scripts/blender/test_fbx_import.py
```

For best rig compatibility, repeat the rig tests with Blender 5.1.x (the version family that wrote the `.blend`) after confirming the AMD Metal driver is healthy.

## 4. Galtis rig inspection

Script: `scripts/blender/test_rig_load.py`

The non-render inspection completed in **0.806 seconds**:

- 38 scene objects
- 1 armature: `root`
- 405 armature bones
- 20 mesh objects
- Avatar meshes: `GaltisBody` and `GaltisHead`
- `GaltisHead`: 71 shape keys total (Basis plus 70 FACS/expression targets)
- `GaltisBody`: no shape keys

The shape-key set covers AU1 through AU64-style facial controls plus mouth-slide controls. The bone list confirms the documented FK/IK → intermediate → deform flow, including FK/IK controls, `*inte*` intermediate bones, and lowercase deform bones.

Inspection command used while rendering was unavailable:

```bash
blender --background --python scripts/blender/test_rig_load.py -- --skip-render
```

The default command still sets rest pose, creates a dedicated camera and two area lights, and targets `output/galtis_tpose_test.png`; that file is absent because of the Metal blocker.

## 5. FBX import and bone mapping

Script: `scripts/blender/test_fbx_import.py`

Sample tested:

```text
SG ASL Dictionary/ASL A/SG ASL Anymore 1 2023-7-16 Upload/
  SG ASL Anymore 1 2023-7-16 No Mesh Full.fbx
```

Results:

- FBX importer result: `FINISHED`
- Observed import time: 0.921–1.202 seconds (1.191 seconds on the final mapping run)
- Imported armature: `Galtis_Rig`, 116 bones
- Base armature: `root`, 405 bones
- Exact case-sensitive bone-name matches: only 6
  - `EyeController`
  - `EyeController_L`
  - `EyeController_R`
  - `FKIK Switch`
  - `HeadTarget`
  - `Locator_Root`
- Imported action: `Galtis_Rig|SG ASL Anymore 1 2023-7-16 Animation`
- F-curves: 1,169
- Frame range: 1–192

The No Mesh Full skeleton does **not** directly match the 405-bone Galtis base rig. Most differences are deliberate export names and capitalization, such as `BicepFK_L` versus `bicepfk_L` and `Bicep_L` versus `upperarminte_L`.

The test script now reverses the official mapping found in `Documentation/Scripts/6) Triple 6 New`, then applies normalized matching for FK/IK controls. It maps **114 of 116** imported bones onto the Galtis rig; only `KneePin_L` and `KneePin_R` have no base-rig target. This mapped action is what the default render path assigns to Galtis before selecting the middle frame. The inspection-only run completed in **1.938 seconds**.

The target `output/fbx_import_test.png` is absent because rendering reaches the same Metal driver stall.

## 6. Sign index

Script: `scripts/build_sign_index.py`  
Output: `data/sign_index.json` (approximately 2.4 MB)

Index statistics:

- 2,586 sign entries
- 2,325 normalized sign names
- 257 names with multiple variants/alts
- Date range: 2023-05-12 through 2026-09-02
- 0 skipped directories
- 3 retained naming anomalies (listed above)

FBX coverage:

| Variant | Entries with a file |
| --- | ---: |
| Mesh | 2,574 |
| No Mesh Full | 2,200 |
| No Mesh Mini | 2,192 |
| No Mesh Mixamo | 2,192 |

Each sign is grouped by normalized sign name and contains its variant label, alt number, normalized ISO date (or `null` when absent), letter directory, source directory, and project-relative paths for all four FBX variants. Nested `FBX Files/` directories are handled recursively.

## Render results (Cycles CPU — no reboot needed)

The Eevee/Metal GPU path hangs in an uninterruptible AMD driver wait. Switching all scripts to **Cycles CPU** bypasses the GPU entirely and renders successfully:

| Test | Resolution | Samples | Time | Output |
| --- | ---: | ---: | ---: | --- |
| Minimal cube | 512×512 | 32 | 1.5s | `/tmp/signbridge_test_render_cycles.png` |
| Galtis T-pose | 512×512 | 64 | 2.5s | `output/galtis_tpose_test.png` |
| FBX import (Anymore, frame 124) | 512×512 | 64 | 2.5s | `output/fbx_import_test.png` |

Cycles CPU is sufficient for headless pipeline rendering. Eevee would be faster but requires the AMD Metal driver to recover (likely needs macOS reboot or GPU reset). The Galtis .blend was saved by Blender 5.1.29 — opens in 4.5.14 with a compatibility warning but functions correctly.

## Remaining notes

The 4 zombie Blender processes from the original Eevee attempts (PIDs 70118, 70536, 71755, 72982) are in `?E` (exiting) state and harmless. One process (75947) remained in `U` state but does not interfere with new Cycles CPU renders.
