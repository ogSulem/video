# Approval workflow and asset manifest

**Project status:** REF-ARC-01, REF-CHAR-01, REF-INT-01, REF-INT-02, REF-SCENE-02 v2, REF-SCENE-01, REF-SCENE-03 center exterior reveal, REF-SCENE-04 reception welcome, REF-SCENE-05 v2 biomechanics assessment, REF-SCENE-06 rehabilitation exercises, REF-SCENE-07 recovery physiotherapy, and REF-SCENE-08 rehabilitation team are approved and locked. REF-SCENE-09 return to slopes is generated and awaiting user visual approval. REF-SCENE-05 v1 is archived as an unapproved alternative. Preserve all approved references unchanged. No video has been generated.
**Repository:** Workspace checkout `ogSulem/video`, branch `arena/f2208454-video`.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** approved.
2. **Stage 2 — master exterior architecture:** REF-ARC-01 generated once and approved; locked canonical facility exterior.
3. **Stage 3 — master skier:** REF-CHAR-01 generated once and approved; locked canonical skier identity and wardrobe.
4. **Stage 4 — interiors and equipment:** REF-INT-01 reception and REF-INT-02 rehabilitation room approved and locked. Specialized equipment remains unverified.
5. **Stage 5 — scene continuity stills:** REF-SCENE-02 v2, REF-SCENE-01 pre-fall descent, REF-SCENE-03 center exterior reveal, REF-SCENE-04 reception welcome, REF-SCENE-05 v2 biomechanics assessment, REF-SCENE-06 rehabilitation exercises, REF-SCENE-07 recovery physiotherapy, and REF-SCENE-08 rehabilitation team are approved and locked; REF-SCENE-02 v1 remains archived and unapproved, and REF-SCENE-05 v1 is archived as an unapproved alternative. REF-SCENE-09 return to slopes is generated and awaiting approval.
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
| `references/scenes/REF-SCENE-01-ski-descent.png` | Canonical pre-fall descent continuity still | APPROVED — LOCKED | PNG; 1376 × 768; 2,247,593 bytes; REF-CHAR-01 primary and REF-SCENE-02 v2 secondary references; preserve unchanged; exact prompt and hash in `prompts/scene_prompts.md` |
| `references/scenes/REF-SCENE-03-center-exterior-reveal.png` | Canonical center exterior reveal still | APPROVED — LOCKED | PNG; 1376 × 768; 2,630,607 bytes; SHA-256 `3cff05af0b82055281a203e5187ac4a0266cd4f53d6b05440de280dc74543ac0`; REF-ARC-01 sole architectural reference; preserve image unchanged |
| `references/scenes/REF-SCENE-04-reception-welcome.png` | Canonical skier reception welcome still | APPROVED — LOCKED | PNG; 1376 × 768; 2,773,335 bytes; SHA-256 `dcc6b97af2e1452d9a09a6bf5397ab1b8282a56c08aac864cecf9db7a6f00320`; REF-INT-01 and REF-CHAR-01 references; preserve image unchanged |
| `references/scenes/REF-SCENE-05-biomechanics-assessment.png` | First functional movement assessment candidate (v1) | ARCHIVED — UNAPPROVED ALTERNATIVE | PNG; 1376 × 768; 2,660,634 bytes; SHA-256 `56cccf4c639787858c0b8dea3b0be8e57491df78895ac1d48626c468bdc38ecf`; preserve unchanged; not canonical |
| `references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png` | Canonical indoor biomechanics assessment still | APPROVED — LOCKED | PNG; 1376 × 768; 2,727,414 bytes; SHA-256 `0a6d303ee25232ba9d82474e120001cbcf0c2813debdaf9ea44d3031f4722acb`; REF-SCENE-05 v1 composition reference, REF-CHAR-01 identity reference; preserve image unchanged |
| `references/scenes/REF-SCENE-06-rehabilitation-exercises.png` | Canonical supervised split-squat rehabilitation still | APPROVED — LOCKED | PNG; 1376 × 768; 2,737,178 bytes; SHA-256 `d163d7baab6f34d2cc5720e3b68782adb7389b22a83af793c54fa442395ad9de`; preserve image unchanged |
| `references/scenes/REF-SCENE-07-recovery-physiotherapy.png` | Canonical supervised knee-mobility still | APPROVED — LOCKED | PNG; 1376 × 768; 2,700,046 bytes; SHA-256 `a3899eb7d0c1a5470c7fa90dc31e3760e3dd9dfc56e0ac519855911d542618e1`; preserve image unchanged |
| `references/scenes/REF-SCENE-08-rehabilitation-team.png` | Canonical supportive athlete-specialist conversation | APPROVED — LOCKED | PNG; 1376 × 768; 2,691,273 bytes; SHA-256 `581c44ba71f91d3de5a0f3447246e3d406afa7427b99e60d95db6a5ba15ef749`; preserve image unchanged |
| `references/scenes/REF-SCENE-09-return-to-slopes.png` | Skier’s controlled return-to-sport carve | GENERATED — AWAITING APPROVAL | PNG; 1376 × 768; 2,739,826 bytes; SHA-256 `5eec2e8d9dc4730241c10500e2541b97da51475827d714b1c5f5e9ccb7626897`; REF-CHAR-01 identity/wardrobe and REF-SCENE-01 action/slope continuity; generated once; preserve all approved refs; do not lock until approved |
| `prompts/scene_prompts.md` | Scene 1, Scene 2, Scene 4, and Scene 5 prompt/generation records | Updated — Scene 5 v2 approved and locked | Exact prompt and output metadata recorded; no video generated |
| `production/creative_brief.md` | Project goals and guardrails | Stage 1 approved | Brand details and factual claims still need verification |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Approved baseline | Maintain reference continuity |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Stage 1 approved | Brand, URL, medical claims unverified |
| `production/shot_list.md` | 20-shot production plan | Stage 1 approved | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules | Updated — twelve references locked; REF-SCENE-09 awaiting approval | Scene 9 returns to the approved skier and opening descent continuity |
| `prompts/interiors.md` | Interior prompts and generation records | REF-INT-01 and REF-INT-02 approved | Approved reference images preserved; equipment availability remains unverified |

## Equipment verification status

The project documents do not confirm the center's actual equipment inventory or service availability. Specifically unconfirmed: cryotherapy/cold therapy; anti-gravity treadmill; therapy pool/aquatic rehabilitation; stabilometric platform; SkyTech or any other named ski simulator; biomechanical treadmills/sensors; and any other specialized diagnostic or exercise device. Do not depict or claim these until the facility confirms them and supplies references where needed. Generic furnishings in REF-INT-02 are illustrative, not verified inventory.

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

Confirm legal center name and location, facility existence, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, logo and tagline rights, and ownership/operation of `altaysportreab.ru`. Verify all title/VO language with the client and appropriate clinical/legal reviewers. Until then, names, services, equipment, and claims in scripts are placeholders, not facts.
