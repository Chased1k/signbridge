# Sprint 6 render benchmarks

Run date: 2026-10-02  
Host: Watchtower, macOS 14.8.5, Intel i9-9980HK, Blender 4.5.14 LTS  
Test frame: Hello source frame 67  
Engine/device: Cycles CPU with denoising

| Configuration | Resolution | Samples | Still-frame time |
| --- | ---: | ---: | ---: |
| Fast development | 640×360 (50%) | 32 | 1.884s |
| Standard | 1280×720 (100%) | 64 | 5.322s |
| Quality | 1280×720 (100%) | 128 | 9.261s |

Raw measurements are in `output/benchmarks/sprint6-benchmarks.json`; the corresponding PNGs are in `output/benchmarks/`.

## Recommendation

Use 32 samples at 50% resolution for development and batch validation. It is 2.8× faster than the standard still and 4.9× faster than the quality still. Use 64 samples at 720p for normal deliverables. The 128-sample setting costs 1.7× the standard setting on this frame and should be reserved for final quality checks.

A deformed animation frame costs more than a warmed single-frame benchmark because Cycles rebuilds animated geometry and its BVH. The full 720p/64-sample Hello render averaged 9.983 seconds per frame (668.860 seconds for 67 frames).
