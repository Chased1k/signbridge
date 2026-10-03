# Sprint 6 batch render test

Run date: 2026-10-02  
Configuration: Cycles CPU, 32 samples, 640×360, 30 fps  
Base-scene loads: 1

| Sign | Frames | Import | Transfer | Render | Render/frame | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hello | 67 | 2.033s | 2.818s | 192.280s | 2.870s | 197.172s |
| Biological Mother | 108 | 1.587s | 3.502s | 303.749s | 2.812s | 308.867s |
| Please | 62 | 1.318s | 2.030s | 176.431s | 2.846s | 179.811s |

Total wall time was **686.311 seconds** for 237 output frames. Import and transfer accounted for only 13.288 seconds across all three signs; rendering dominates.

Outputs:

- `output/batch_test/hello.mp4` — H.264, 640×360, 30 fps, 67 frames, 2.233s
- `output/batch_test/biological_mother.mp4` — H.264, 640×360, 30 fps, 108 frames, 3.600s
- `output/batch_test/please.mp4` — H.264, 640×360, 30 fps, 62 frames, 2.067s
- `output/batch_test/batch-results.json` — raw timing data

The test confirms that Galtis can be loaded once and reused while source FBX armatures are imported, transferred, removed, and replaced sequentially.
