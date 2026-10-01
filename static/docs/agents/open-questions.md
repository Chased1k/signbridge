# Open Questions — SignBridge

| ID | Question | Priority | Status |
|---|---|---|---|
| Q1 | Character sheet: ComfyUI-generated, stock photo, or user upload? | High | Open — Kellen to decide |
| Q2 | GPU strategy: pre-compute all poses (lookup table) vs on-demand? | High | Resolved — D5: pre-compute |
| Q3 | Deployment target: Docker on Watchtower or separate VPS? | Medium | Open — depends on processing load |
| Q4 | Long video handling: stitch at pose level or after Dreamactor output? | Medium | Open — test with 30 sec first |
| Q5 | Should we fork GenASL or extract just the data prep scripts? | Low | Lean toward extracting scripts — less AWS baggage |