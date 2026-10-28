# Approval workflow and asset manifest

**Project status (2026-10-28):** REF-ARC-01, REF-CHAR-01, REF-INT-01, REF-INT-02, REF-SCENE-01 through REF-SCENE-10, and the full Russian VO script/audio remain APPROVED — LOCKED. Scene 10 is a backup card background; its motif is decorative, not an official logo. Preserve all approved sources unchanged. V1 remains preserved as the baseline at `video/final/altai_rehabilitation_commercial_v1.mp4`. The test-first six-second motion test is category C (programmatic movement over a still). A technically decoded 77-second v2 review render now exists at `video/final/altai_rehabilitation_commercial_v2.mp4`; it uses approved stills and VO plus three new provisional AI-generated **still** inserts, with only programmatic 2D motion—not genuine image-to-video or articulated skier motion. The three inserts are not approval-locked and await owner review. See `video/tests/MOTION_TEST_REPORT.md` and `video/tests/V2_QC_REPORT.md`.
**v3 (2026-10-28):** `video/final/altai_rehabilitation_v3.mp4` is a new review
master, 78.8 s, 1920 × 1080, 24 fps, −16 LUFS. It is the first cut that uses the
three generated clips (`scene a1/a2/d.mp4`) as motion picture: they are re-timed
with per-frame optical flow and supply 32.5 s (41 %) of the film. The remaining
picture is 40.3 s of approved stills staged as depth-layered living stills
(clearly stills, not footage) and a 7.6 s typeset brand card. The locked VO file
is byte-identical; a codec-click repair and a broadcast voice curve are applied
to an in-memory placement copy only and are switchable off. Nothing approved was
modified or regenerated. v3 remains a review master pending the Stage 7 gates.

**Repository:** Workspace checkout `ogSulem/video`, branch `arena/9927bff3-video`.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** approved.
2. **Stage 2 — master exterior architecture:** REF-ARC-01 generated once and approved; locked canonical facility exterior.
3. **Stage 3 — master skier:** REF-CHAR-01 generated once and approved; locked canonical skier identity and wardrobe.
4. **Stage 4 — interiors and equipment:** REF-INT-01 reception and REF-INT-02 rehabilitation room approved and locked. Specialized equipment remains unverified.
5. **Stage 5 — scene continuity stills:** REF-SCENE-02 v2, REF-SCENE-01 pre-fall descent, REF-SCENE-03 center exterior reveal, REF-SCENE-04 reception welcome, REF-SCENE-05 v2 biomechanics assessment, REF-SCENE-06 rehabilitation exercises, REF-SCENE-07 recovery physiotherapy, REF-SCENE-08 rehabilitation team, REF-SCENE-09 return to slopes, and REF-SCENE-10 final brand-card backup are APPROVED — LOCKED; REF-SCENE-02 v1 remains archived and unapproved, and REF-SCENE-05 v1 is archived as an unapproved alternative.
6. **Stage 6 — video:** the six-second capability test was rendered and inspected first, then classified category C (camera/snow motion over a locked still; no subject articulation). V1 remains preserved. The v2 director's rework was rendered and fully decoded on 2026-10-28 at `video/final/altai_rehabilitation_commercial_v2.mp4` (77.00 s, 1920 × 1080, 24 fps, H.264/AAC). It uses unchanged approved stills/VO, an original synthetic bed, three provisional AI-generated still inserts, and programmatic 2D camera/compositing motion—not video-generated footage. Technical QC is recorded in `video/tests/V2_QC_REPORT.md`; v2 and its new inserts await owner and applicable release review.
7. **Stage 7 — finishing/release:** owner review of the three provisional stills, factual/clinical/legal/brand/rights review, client/platform loudness approval, any licensed or recorded audio replacement, and a separate vertical re-edit remain future work if requested.

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
| `references/scenes/REF-SCENE-09-return-to-slopes.png` | Canonical return-to-sport carve | APPROVED — LOCKED | PNG; 1376 × 768; 2,739,826 bytes; SHA-256 `5eec2e8d9dc4730241c10500e2541b97da51475827d714b1c5f5e9ccb7626897`; REF-CHAR-01 identity/wardrobe and REF-SCENE-01 action/slope continuity; preserve image unchanged |
| `references/scenes/REF-SCENE-10-final-brand-card.png` | Approved backup end-card background with reserved text zones | APPROVED — LOCKED (owner approval, 2026-10-28) | PNG; 1376 × 768; 1,364,967 bytes; SHA-256 `5c173731529dd1899046b842997d798865a2059062f0a6cec99696a9afdc7486`; preserve unchanged; no AI-rendered text; exact name/tagline/website copy is owner-approved for production; motif is decorative, not an official logo |
| `audio/voiceover/voiceover_ru_safe_excerpt_v1.mp3` | Short Russian synthetic VO technical test | GENERATED — TEST; retained | MP3; 99,910 bytes; SHA-256 `7990ad0e097ff3671e30c7faece8a0c5e95a2c5ba33934f374af34eb7912e0c8`; selected voice `voice-00`; contains draft line 1 and the return-question fragment only; excludes unverified injury diagnosis; not a complete final VO |
| `audio/voiceover/voiceover_ru_full_v1.mp3` | Continuous synthetic Russian reading of approved full VO script | APPROVED — LOCKED (owner approval, 2026-10-28) | MP3; 561,546 bytes; 70.16 seconds from Xing frame count; SHA-256 `7d5368d3075ba16c30e9f6bf717d477c1ff2c6eb51bf59dba2a86b6d199376f1`; voice `voice-00`; matching script at `editing/voiceover_final_ru.md`; preserve unchanged |
| `video/final/altai_rehabilitation_commercial_v1.mp4` | 16:9 commercial v1, preserved baseline | Rendered — technical QC passed; awaiting owner/release review | MP4; 31,217,020 bytes; 77.00 s; 1920 × 1080 progressive at 24 fps; H.264 High Profile / AAC-LC stereo 48 kHz; SHA-256 `c41468ce4342c8349f2d3936f2b5a935242695d8b58afbcb8071404bb852acd2`; preserved unchanged; all apparent motion is 2D animation over stills |
| `video/final/altai_rehabilitation_commercial_v2.mp4` | 16:9 director's-cut v2 review master | Rendered — full decode/QC passed; awaiting owner/release review | MP4; 45,420,896 bytes; 77.00 s / 1,848 frames; 1920 × 1080 progressive at 24 fps; H.264 High/yuv420p, Rec.709 / AAC-LC stereo 48 kHz; SHA-256 `86fdee75baf13a2183d219e34f65b9bd8ffe9c916a11722808ae0d3a79390410`; unchanged approved stills/VO plus three provisional still inserts; no generated moving footage |
| `video/tests/skier_motion_test_v1.mp4` | Test-first 6-second motion capability render | Rendered and inspected — category C | MP4; 2,397,447 bytes; 6.00 s / 144 frames; 1920 × 1080 / 24 fps; H.264 High/yuv420p / AAC stereo; SHA-256 `972cf6ecb94bf898f46c608a99bb1c02db427d0eb9de92f38bf8056f1cb4e167`; camera push/snow over unchanged skier still, no body articulation |
| `video/assets/skier_loss_of_control_keyframe_v1.png` | Pre-impact loss-of-control visual keyframe for v2 | GENERATED — provisional editorial insert; not approval-locked | PNG; 1376 × 768; SHA-256 `869924435d75bc045be03a1a57060aa744b3a81e8b532be4dd08d0c54cc11918`; still only, distinct from later seated aftermath; owner review required |
| `video/assets/assisted_arrival_keyframe_v1.png` | Supported exterior arrival keyframe for v2 | GENERATED — provisional editorial insert; not approval-locked | PNG; 1376 × 768; SHA-256 `d491fc559021a6bd55e88f494a0443b0e1e35b2a78477df1661f42dc6d147895`; still only; depicts companion supporting skier at entrance; no specific service/procedure implied |
| `video/assets/endcard_altai_landscape_v1.png` | Wide Altai mountain/sky end-card background for v2 | GENERATED — provisional editorial insert; not approval-locked | PNG; 1376 × 768; SHA-256 `2beca354122fe5ffac84b43c1ddd27e06be63db3fa37a172fc8b28d060061e5c`; no lettering/logo; only a still plate with a simulated digital reframe |
| `video/render_altai_commercial.py` | Reproducible director's-cut v2 assembly and original synthetic score/ambience generator | Created; inputs SHA-pinned | Uses FFmpeg 7.0.2 via `imageio-ffmpeg`, Pillow, and NumPy; defaults to `video/final/altai_rehabilitation_commercial_v2.mp4`; exact rerun instructions in `video/README.md` |
| `video/render_altai_commercial_v1.py` | Preserved v1 assembly renderer | Archived for reproducibility | Keeps the previous v1 render workflow separate from the new v2 default; no approved sources changed |
| `video/render_skier_motion_test.py` | Reproducible six-second category-C capability-test renderer | Created; locked skier-source hash checked | Uses a fixed REF-CHAR-01 hash; output stays separate from the commercial |
| `video/tests/MOTION_TEST_REPORT.md` | Test-first capability classification/provenance | Completed | Records category C, source/output hashes, unavailable I2V capability, and unknown prior green-field/cloud provenance |
| `video/tests/V2_QC_REPORT.md` | V2 technical, visual, audio, and motion-provenance QC report | Completed — technical QC passed; release review pending | Records output hash/metadata, unchanged VO, measured loudness, limitations, and owner-review gate |
| `video/README.md` | Renderer setup, outputs, motion provenance, and review notes | Updated — v2 | Includes v1 preservation and v2/test reproduction steps |
| `prompts/scene_prompts.md` | Scene 1, Scene 2, Scene 4, and Scene 5 prompt/generation records | Updated — Scene 5 v2 approved and locked | Exact still prompts/output metadata recorded; no reference-image-to-video clip; v2 still inserts are separately provisional |
| `production/creative_brief.md` | Project goals and guardrails | Stage 1 approved | Owner-approved name, tagline, and URL are production copy; factual medical/service claims still need review |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Approved baseline | Maintain reference continuity |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Stage 1 timing proposal | Owner-approved final brand copy; factual VO claims still require review |
| `production/shot_list.md` | 20-shot production plan | Stage 1 approved | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules and v2 provisional inserts | Updated — approved references remain locked; three new inserts marked provisional | Scene 10 background remains unchanged; its motif is decorative only; v2 motion is still-based |
| `editing/video_assembly_plan.md` | 77-second v2 director's timeline, test-first capability audit, render record, and QC/release gates | Updated — v2 rendered and technically verified | Approved sources/VO remain locked; three AI-generated still inserts are provisional; genuine moving footage and any licensed/recorded final mix remain absent |
| `editing/voiceover_final_ru.md` | Final Russian narration and scene cues | APPROVED — LOCKED (owner approval, 2026-10-28) | Approximately 65–77 seconds; non-guaranteed, no diagnosis or unverified treatment/equipment claims; exact approved end-card copy included as on-screen text only; preserve unchanged |
| `prompts/interiors.md` | Interior prompts and generation records | REF-INT-01 and REF-INT-02 approved | Approved reference images preserved; equipment availability remains unverified |
| `scene a1.mp4`, `scene a2.mp4`, `scene d.mp4` | Generated motion footage: carve, fall/aftermath, return | GENERATED — reviewed, hash-pinned for v3; not owner-approved | 8.0 s / 8.0 s / 10.1 s, 24 fps, 1280 × 704 / 1284 × 716 / 1344 × 768; upscaled to 1080p in v3; known AI artefacts in skis, gloves and snow |
| `video/final/altai_rehabilitation_v3.mp4` (+ `.json`) | v3 review master and its manifest | QC REVIEW — awaiting owner approval | 78.8 s; 41 % generated motion, 51 % staged stills, 8 % typeset card; −16 LUFS / −1.5 dBTP; see `video/tests/V3_QC_REPORT.md` |
| `video/render_film_v3.py`, `video/filmkit/*` | Reproducible v3 renderer (optical-flow retiming, living stills, grade, score, mix) | In production — deterministic, offline | Hash-pins every source in `filmkit/sources.py`; refuses to render if a pin drifts |
| `video/tools/qc_v3.py` | Delivery QC: decode, loudness, duplicate-frame census, contact sheet | In production | Reads the delivery only; writes `video/tests/V3_QC_REPORT.md` |

## Equipment verification status

The project documents do not confirm the center's actual equipment inventory or service availability. Specifically unconfirmed: cryotherapy/cold therapy; anti-gravity treadmill; therapy pool/aquatic rehabilitation; stabilometric platform; SkyTech or any other named ski simulator; biomechanical treadmills/sensors; and any other specialized diagnostic or exercise device. Do not depict or claim these until the facility confirms them and supplies references where needed. Generic furnishings in REF-INT-02 are illustrative, not verified inventory.

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

The owner-approved name, tagline, and `altaysportreab.ru` are approved production copy. Before public release, verify facility facts, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, and any rights for a separately supplied official logo. Review VO language with the appropriate clinical/legal reviewers. Services, equipment, and medical/performance claims remain unverified until substantiated.
