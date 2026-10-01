# Decision Log — SignBridge

| ID | Date | Decision | Rationale | Alternatives Considered |
|---|---|---|---|---|
| D1 | 2026-09-30 | Use GenASL (AWS) as base, strip AWS dependencies | MIT-0 license, proven pipeline, already has RTMPose + ASLLVD integration | Build from scratch (more work, no advantage) |
| D2 | 2026-09-30 | Two-phase: open-source skeleton + fal.ai polish | Best of both worlds — accurate signing + photorealistic output | Pure avatar (looks fake) or pure AI gen (inaccurate signing) |
| D3 | 2026-09-30 | Dreamactor v2 for motion transfer | Purpose-built for image+driving video → output. Exactly our use case. | Seedance 2.0 (more expensive, less direct), Omnihuman (no body motion) |
| D4 | 2026-09-30 | On-demand processing, not batch | Each audio file processed individually. Simpler, no queue complexity | Batch (over-engineered for POC) |
| D5 | 2026-09-30 | Pre-compute ASLLVD pose videos as lookup table | One-time GPU cost (~$2-4), then on-demand is just file lookup + concat | On-demand pose inference (needs GPU always available) |