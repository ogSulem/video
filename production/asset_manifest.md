# Approval workflow and asset manifest

**Project status:** REF-ARC-01, REF-CHAR-01, and REF-INT-01 are approved and locked. REF-INT-02 was generated once and is awaiting user approval.
**Repository:** Workspace checkout `ogSulem/video`, branch `arena/f2208454-video`. Repository updates are tracked via the configured Git CLI.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** approved.
2. **Stage 2 — master exterior architecture:** REF-ARC-01 generated once and approved; locked canonical facility exterior.
3. **Stage 3 — master skier:** REF-CHAR-01 generated once and approved; locked canonical skier identity and wardrobe.
4. **Stage 4 — interiors and equipment:** REF-INT-01 revised reception generated, approved, and locked. REF-INT-02 rehabilitation/exercise room generated exactly once and awaiting user visual approval. No further interior/equipment asset until approval.
5. **Stage 5 — shot prompts:** write individual prompts using approved references; obtain approval before generation.
6. **Stage 6 — video:** generate clips in narrative order and review each batch before continuing.
7. **Stage 7 — finishing:** edit, sound, VO, Russian titles, verified brand card, and separately composed vertical cut.

No paid operation without explicit authorization. Do not skip gates or replace approved assets without explicit approval.

## Asset manifest

| Filename / ID | Purpose | Status | Dependencies / notes |
|---|---|---|---|
| `references/architecture/REF-ARC-01-master-exterior.png` | Master exterior architecture reference | Approved — canonical | Original PNG; 1376 × 768; 2,688,465 bytes; preserve unchanged |
| `references/characters/REF-CHAR-01-master-skier.png` | Master skier identity and wardrobe reference | Approved — canonical | Original PNG; 1376 × 768; 2,180,293 bytes; preserve unchanged |
| `references/interiors/REF-INT-01-master-reception.png` | Revised master reception reference | APPROVED — LOCKED, canonical | PNG; 1376 × 768; 2,772,482 bytes; exact prompt in `prompts/interiors.md`; preserve unchanged |
| `references/interiors/REF-INT-01-master-reception-v1-original.png` | Initial reception draft | Archived — unapproved, not canonical | PNG; 1376 × 768; 2,673,858 bytes; preserved byte-identically; SHA-256 `3d9cb7781d1c5efd20b8a7be9901a9717645150d5d9131c248fdc4279881353b` |
| `references/interiors/REF-INT-02-master-rehabilitation-room.png` | Master rehabilitation/exercise room | GENERATED — AWAITING APPROVAL | PNG; 1376 × 768; 2,690,673 bytes; generated once using REF-ARC-01 primary and REF-INT-01 secondary image references; exact prompt in `prompts/interiors.md` |
| `production/creative_brief.md` | Project goals and guardrails | Stage 1 approved | Brand details and factual claims still need verification |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Approved baseline | Refine consistently with approved references |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Stage 1 approved | Brand, URL, medical claims unverified |
| `production/shot_list.md` | 20-shot production plan | Stage 1 approved | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules | Updated — REF-INT-02 awaiting approval | REF-ARC-01, REF-CHAR-01, REF-INT-01 locked; REF-INT-02 is not locked |
| `prompts/architecture.md` | Stage 2 exterior image brief and generation record | Approved reference | Original reference preserved |
| `prompts/character.md` | Stage 3 skier brief and generation record | Approved reference | Original reference preserved |
| `prompts/interiors.md` | REF-INT-01 record and REF-INT-02 prompt/generation record | REF-INT-01 approved; REF-INT-02 awaiting approval | Exact generation prompt and image metadata recorded |

## Equipment verification status

The current project documents do not confirm the center's actual equipment inventory or service availability. Specifically unconfirmed: cryotherapy/cold therapy; anti-gravity treadmill; therapy pool/aquatic rehabilitation; stabilometric platform; SkyTech or any other named ski simulator; biomechanical treadmills/sensors; and any other specialized diagnostic or exercise device. The generated REF-INT-02 uses only generic, unbranded furnishings as illustrative design elements, not a verified inventory or a claim about available services. Confirm actual equipment with the facility before depicting it in later assets.

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

Confirm legal center name and location, facility existence, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, logo and tagline rights, and ownership/operation of `altaysportreab.ru`. Verify all title/VO language with the client and appropriate clinical/legal reviewers. Until then, names, services, equipment, and claims in scripts are placeholders, not facts.
