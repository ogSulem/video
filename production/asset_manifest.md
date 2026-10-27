# Approval workflow and asset manifest

**Project status:** REF-ARC-01, REF-CHAR-01, REF-INT-01, REF-INT-02, and REF-SCENE-02 v2 are approved and locked. A prompt for `REF-SCENE-01-ski-descent` is prepared and awaiting approval; no descent image or video has been generated.
**Repository:** Workspace checkout `ogSulem/video`, branch `arena/f2208454-video`.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** approved.
2. **Stage 2 — master exterior architecture:** REF-ARC-01 generated once and approved; locked canonical facility exterior.
3. **Stage 3 — master skier:** REF-CHAR-01 generated once and approved; locked canonical skier identity and wardrobe.
4. **Stage 4 — interiors and equipment:** REF-INT-01 reception and REF-INT-02 rehabilitation room approved and locked. Specialized equipment remains unverified.
5. **Stage 5 — skier continuity stills:** REF-SCENE-02 v2 is approved and locked; v1 is archived and unapproved. The REF-SCENE-01 pre-fall descent prompt is prepared; awaiting user approval before generating exactly one still.
6. **Stage 6 — video:** generate clips in narrative order and review each batch before continuing.
7. **Stage 7 — finishing:** edit, sound, VO, Russian titles, verified brand card, and separately composed vertical cut.

No paid operation without explicit authorization. Do not skip gates or replace approved assets without explicit approval.

## Asset manifest

| Filename / ID | Purpose | Status | Dependencies / notes |
|---|---|---|---|
| `references/architecture/REF-ARC-01-master-exterior.png` | Master exterior architecture reference | APPROVED — LOCKED | PNG; 1376 × 768; 2,688,465 bytes; preserve unchanged |
| `references/characters/REF-CHAR-01-master-skier.png` | Master skier identity and wardrobe reference | APPROVED — LOCKED | PNG; 1376 × 768; 2,180,293 bytes; preserve unchanged |
| `references/interiors/REF-INT-01-master-reception.png` | Revised master reception reference | APPROVED — LOCKED | PNG; 1376 × 768; 2,772,482 bytes; preserve unchanged |
| `references/interiors/REF-INT-01-master-reception-v1-original.png` | Initial reception draft | Archived — unapproved, not canonical | PNG; 1376 × 768; 2,673,858 bytes; preserved byte-identically |
| `references/interiors/REF-INT-02-master-rehabilitation-room.png` | Master rehabilitation/exercise room | APPROVED — LOCKED | PNG; 1376 × 768; 2,690,673 bytes; preserve unchanged; generic furnishings are illustrative, not verified inventory |
| `references/scenes/REF-SCENE-02-injury-aftermath.png` | First post-fall still candidate (v1) | Archived — unapproved alternative | PNG; 1376 × 768; 2,274,093 bytes; retain unchanged for comparison |
| `references/scenes/REF-SCENE-02-injury-aftermath-v2.png` | Canonical non-graphic post-fall still | APPROVED — LOCKED | PNG; 1376 × 768; 2,045,368 bytes; preserve unchanged; face visible with goggles raised |
| `references/scenes/REF-SCENE-01-ski-descent.png` | Proposed pre-fall descent continuity still | Not generated — prompt awaiting approval | Use REF-CHAR-01 as primary identity reference; use REF-SCENE-02 v2 only as secondary slope/axis continuity reference; exact prompt in `prompts/scene_prompts.md` |
| `prompts/scene_prompts.md` | Scene 2 continuity and Scene 1 descent prompt | Updated — v2 approved; Scene 1 prompt awaiting approval | Preserve v1/v2 prompt and status history; no video generated |
| `production/creative_brief.md` | Project goals and guardrails | Stage 1 approved | Brand details and factual claims still need verification |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Approved baseline | Maintain reference continuity |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Stage 1 approved | Brand, URL, medical claims unverified |
| `production/shot_list.md` | 20-shot production plan | Stage 1 approved | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules | Updated — five references locked | Scene 1 descent still is planned, not generated |
| `prompts/interiors.md` | Interior prompts and generation records | REF-INT-01 and REF-INT-02 approved | Approved reference images preserved; equipment availability remains unverified |

## Equipment verification status

The project documents do not confirm the center's actual equipment inventory or service availability. Specifically unconfirmed: cryotherapy/cold therapy; anti-gravity treadmill; therapy pool/aquatic rehabilitation; stabilometric platform; SkyTech or any other named ski simulator; biomechanical treadmills/sensors; and any other specialized diagnostic or exercise device. Do not depict or claim these until the facility confirms them and supplies references where needed. Generic furnishings in REF-INT-02 are illustrative, not verified inventory.

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

Confirm legal center name and location, facility existence, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, logo and tagline rights, and ownership/operation of `altaysportreab.ru`. Verify all title/VO language with the client and appropriate clinical/legal reviewers. Until then, names, services, equipment, and claims in scripts are placeholders, not facts.
