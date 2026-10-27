# Approval workflow and asset manifest

**Project status:** REF-ARC-01 and REF-CHAR-01 approved. Revised REF-INT-01 reception candidate generated and awaiting user visual review; no interior is locked yet.
**Repository:** Workspace checkout `ogSulem/video`, branch `arena/f2208454-video`. Arena's GitHub connector lookup returned `unsupported`; repository work is tracked via the configured Git CLI.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** approved.
2. **Stage 2 — master exterior architecture:** REF-ARC-01 generated once and approved; locked canonical facility exterior.
3. **Stage 3 — master skier:** REF-CHAR-01 generated once and approved; locked canonical skier identity and wardrobe.
4. **Stage 4 — interiors and equipment:** revised REF-INT-01 generated once and awaiting user visual review. Original reception draft is preserved separately. Do not prepare/generate REF-INT-02 or any other interior/equipment asset until the revised reception candidate is approved.
5. **Stage 5 — shot prompts:** write individual prompts using approved references; obtain approval before generation.
6. **Stage 6 — video:** generate clips in narrative order and review each batch before continuing.
7. **Stage 7 — finishing:** edit, sound, VO, Russian titles, verified brand card, and separately composed vertical cut.

No paid operation without explicit authorization. Do not skip gates or replace approved assets without explicit approval.

## Asset manifest

| Filename / ID | Purpose | Status | Dependencies / notes |
|---|---|---|---|
| `references/architecture/REF-ARC-01-master-exterior.png` | Master exterior architecture reference | Approved — canonical | Original PNG; 1376 × 768; 2,688,465 bytes; preserve unchanged |
| `references/characters/REF-CHAR-01-master-skier.png` | Master skier identity and wardrobe reference | Approved — canonical | Original PNG; 1376 × 768; 2,180,293 bytes; preserve unchanged |
| `references/interiors/REF-INT-01-master-reception.png` | Revised master reception candidate | Generated — awaiting user visual review; not locked | PNG; 1376 × 768; 2,772,482 bytes; one revised image; REF-ARC-01 was the sole image reference; exact prompt in `prompts/interiors.md` |
| `references/interiors/REF-INT-01-master-reception-v1-original.png` | Preserved copy of initial reception draft | Archived — unapproved, not canonical | PNG; 1376 × 768; 2,673,858 bytes; SHA-256 `3d9cb7781d1c5efd20b8a7be9901a9717645150d5d9131c248fdc4279881353b`; byte-identical to the earlier unapproved image |
| `production/creative_brief.md` | Project goals and guardrails | Stage 1 approved | Brand details and factual claims still need verification |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Approved baseline | Refine consistently with approved references |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Stage 1 approved | Brand, URL, medical claims unverified |
| `production/shot_list.md` | 20-shot production plan | Stage 1 approved | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules | Updated — REF-INT-01 awaiting review | REF-ARC-01 and REF-CHAR-01 remain locked; neither reception image is canonical yet |
| `prompts/architecture.md` | Stage 2 exterior image brief and generation record | Approved reference | Original reference preserved |
| `prompts/character.md` | Stage 3 skier brief and generation record | Approved reference | Original reference preserved |
| `prompts/interiors.md` | Revised Stage 4 reception prompt and generation record | Candidate awaiting approval | Exact revised prompt and both reception-file records are included |

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

Confirm legal center name and location, facility existence, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, logo and tagline rights, and ownership/operation of `altaysportreab.ru`. Verify all title/VO language with the client and appropriate clinical/legal reviewers. Until then, names, services, equipment, and claims in scripts are placeholders, not facts.
