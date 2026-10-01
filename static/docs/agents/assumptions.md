# Assumptions — SignBridge

| ID | Assumption | Risk | Mitigation |
|---|---|---|---|
| A1 | ASLLVD dataset is still available at BU URLs | Low | Download immediately during S1. Mirror to local storage. |
| A2 | 3,300 ASLLVD signs cover most common English words | Medium | Fingerspelling fallback for missing vocabulary. Track coverage stats. |
| A3 | Dreamactor v2 can transfer signing motion (not just talking head) | Medium | Test early with a 5-sec clip. If poor, try Seedance 2.0 as fallback. |
| A4 | fal.ai key has sufficient credits/quota | Low | Monitor usage. Key found in hermes/.env. |
| A5 | Whisper.cpp on Watchtower can transcribe in reasonable time | Low | Already using whisper-local skill successfully. |
| A6 | Pose video chunks <30 sec for Dreamactor | Low | Most voice notes are short. Chunk longer inputs at sentence boundaries. |