# SignBridge — Tech Debt & Future Work

## Tech Debt

### TD-001: 31 missing ASLLVD videos (LOW)
- 2,569/2,746 glosses extracted (93.6%). 31 source videos corrupted/missing.
- Fix: Re-download from BU, or use synonym glosses for coverage gaps.
- Impact: Minimal — missing signs are rare words.

### TD-002: MediaPipe vs RTMPose (MEDIUM)
- MediaPipe (75 keypoints) used instead of RTMPose (133).
- Faster on CPU but may miss fine hand shapes.
- Compare quality after POC. RTMPose needs GPU (Vast.ai RTX 4090 ~$0.12/hr).

### TD-003: DO GPU whitelisting (LOW)
- DigitalOcean GPU droplets blocked via API across all regions.
- Fix: Open support ticket, or use Vast.ai for GPU processing.

### TD-004: Deictic signs are placeholder color videos (LOW)
- 20 pronoun/common words (YOU, HE, SHE, WE, MY, etc.) generated as solid-color videos.
- ASLLVD doesn't include these because they're pointing gestures (deictic/indexical), not lexical signs.
- Need proper pose extraction from recorded sample videos or hand-drawn keypoints.
- Functional for POC pipeline flow — demonstrates the full pipeline works.

### TD-005: LLM rephrasing quality (MEDIUM)
- Gemma4:cloud rephrases English → ASL grammar. ~76% direct hit rate.
- Sometimes creates compounds like "TELL-YOU" that don't exist in the database.
- Fix: Better prompt engineering, or fine-tune a small model on ASL gloss pairs.

## Future Work

### FW-001: Fingerspelling video generation
- Currently skipped in POC. Need letter-by-letter pose videos or animated hand shapes.
- Could use MediaPipe hand keypoints to generate manual alphabet poses.

### FW-002: Real-time translation stream
- Current: batch processing (audio file → video file).
- Future: WebSocket stream for live translation.

### FW-003: Multi-signer support
- Currently uses first available signer per gloss.
- Future: User selects signer, or system picks consistent signer per video.

### FW-004: ASL grammar improvements
- Current: LLM rephrases, then deterministic word matching.
- Future: Fine-tuned model on ASL gloss pairs, handles classifiers, spatial references, non-manual markers.

### FW-005: Mobile app / browser extension
- Record audio → upload → get ASL video.
- Chrome extension: translate YouTube/broadcast content in real-time.

### FW-006: Database & pipeline scale-up
- If POC succeeds: RTMPose on dedicated GPU, vector search for semantic gloss matching, caching layer, queue system.
- Productize as SaaS for content creators, educators, accessibility teams.

### FW-007: Competitive product analysis
- SignAll, Signly, Avatarslike are the closest competitors.
- Most are avatar-based (not photorealistic video).
- Our angle: photorealistic signer video via fal.ai polish + open-source pose data.