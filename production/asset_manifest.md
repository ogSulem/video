# Approval workflow and asset manifest

**Project status:** Stage 2 — master exterior generated; awaiting user visual approval.
**Generated reference assets:** One exterior image; not yet approved as canonical.
**Repository:** Workspace checkout `ogSulem/video`, branch `arena/f2208454-video`. The Arena GitHub connector lookup returned `unsupported`; this file and the image are saved in the checkout. Git CLI was used for repository publication where supported.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** documents and workflow approved by user.
2. **Stage 2 — master exterior architecture:** exactly one image generated; awaiting user review/approval before it becomes the locked facility anchor.
3. **Stage 3 — master skier:** generate exactly one image only after Stage 2 is approved; review/approve proposed appearance before use.
4. **Stage 4 — interiors and equipment:** create/review one approved asset at a time, using approved architectural/character references and verifying actual facility equipment/services.
5. **Stage 5 — shot prompts:** write individual prompts based on approved references; obtain approval before generation.
6. **Stage 6 — video:** generate clips in narrative order and review each batch before continuing.
7. **Stage 7 — finishing:** edit, sound, VO, Russian titles, verified brand card, and separately composed vertical cut.

No paid operation without explicit authorization. Do not skip gates or replace approved assets without explicit approval.

## Asset manifest

| Filename / ID | Purpose | Status | Dependencies / notes |
|---|---|---|---|
| `references/architecture/REF-ARC-01-master-exterior.png` | Master exterior architecture reference | Generated — awaiting user visual approval | Original generated PNG; 1376 × 768; 2,688,465 bytes; generated from exact prompt recorded in `prompts/architecture.md`; do not treat as canonical until approved |
| `production/creative_brief.md` | Project goals and guardrails | Stage 1 approved | User brief; claims and brand details still need factual verification |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Stage 1 approved | Refine after approval of visual references |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Stage 1 approved | Brand, URL, medical claims unverified |
| `production/shot_list.md` | 20-shot production plan | Stage 1 approved | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules | Stage 1 approved | Proposed skier not yet approved/generated |
| `prompts/architecture.md` | Stage 2 exterior image brief and generation record | Generated — awaiting user visual approval | Exact generation prompt is preserved; no variants generated |
| `prompts/character.md` | Stage 3 skier design brief | Draft — not submitted to image generation | Hold until Stage 2 is approved |
| `prompts/interiors.md` | Stage 4 reference brief | Draft — not submitted to image generation | Hold until Stages 2–3 and fact checks |

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and any accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

Confirm legal center name and location, facility existence, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, logo and tagline rights, and ownership/operation of `altaysportreab.ru`. Verify all title/VO language with the client and appropriate clinical/legal reviewers. Until then, names, services, equipment, and claims in scripts are placeholders, not facts.
