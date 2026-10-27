# Approval workflow and asset manifest

**Project status:** Stage 4 planning — REF-ARC-01 and REF-CHAR-01 approved; REF-INT-01 exact prompt prepared and awaiting approval. No interior image has been generated.
**Repository:** Workspace checkout `ogSulem/video`, branch `arena/f2208454-video`. Arena's GitHub connector lookup returned `unsupported`; repository work has been performed via the configured Git CLI.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** approved.
2. **Stage 2 — master exterior architecture:** REF-ARC-01 generated once and approved; locked canonical facility exterior.
3. **Stage 3 — master skier:** REF-CHAR-01 generated once and approved; locked canonical skier identity and wardrobe.
4. **Stage 4 — interiors and equipment:** next is REF-INT-01, reception/main public interior. Exact prompt is prepared in `prompts/interiors.md`; awaiting user approval before generating exactly one image. Other interiors/equipment remain on hold.
5. **Stage 5 — shot prompts:** write individual prompts using approved references; obtain approval before generation.
6. **Stage 6 — video:** generate clips in narrative order and review each batch before continuing.
7. **Stage 7 — finishing:** edit, sound, VO, Russian titles, verified brand card, and separately composed vertical cut.

No paid operation without explicit authorization. Do not skip gates or replace approved assets without explicit approval.

## Asset manifest

| Filename / ID | Purpose | Status | Dependencies / notes |
|---|---|---|---|
| `references/architecture/REF-ARC-01-master-exterior.png` | Master exterior architecture reference | Approved — canonical | Original generated PNG; 1376 × 768; 2,688,465 bytes; preserve unchanged; exact prompt in `prompts/architecture.md` |
| `references/characters/REF-CHAR-01-master-skier.png` | Master skier identity and wardrobe reference | Approved — canonical | Original generated PNG; 1376 × 768; 2,180,293 bytes; preserve unchanged; exact prompt and continuity details in `prompts/character.md` |
| `references/interiors/REF-INT-01-master-reception.png` | Master reception/main public interior | Not generated — prompt awaiting approval | Proposed prompt in `prompts/interiors.md`; intended to use REF-ARC-01 as image reference; generate only after explicit approval |
| `production/creative_brief.md` | Project goals and guardrails | Stage 1 approved | Brand details and factual claims still need verification |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Approved baseline | Continue to refine against approved references |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Stage 1 approved | Brand, URL, medical claims unverified |
| `production/shot_list.md` | 20-shot production plan | Stage 1 approved | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules | Updated — approved references locked | REF-ARC-01 and REF-CHAR-01 unchanged; REF-INT-01 still proposed |
| `prompts/architecture.md` | Stage 2 exterior image brief and generation record | Approved reference | Original reference preserved; no variants generated |
| `prompts/character.md` | Stage 3 skier brief and generation record | Approved reference | Original reference preserved; no variants generated |
| `prompts/interiors.md` | Stage 4 interior prompt and equipment guardrails | Prompt awaiting approval | Exact REF-INT-01 prompt included; no image generated |

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

Confirm legal center name and location, facility existence, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, logo and tagline rights, and ownership/operation of `altaysportreab.ru`. Verify all title/VO language with the client and appropriate clinical/legal reviewers. Until then, names, services, equipment, and claims in scripts are placeholders, not facts.
