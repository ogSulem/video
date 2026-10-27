# Approval workflow and asset manifest

**Project status:** Stage 1 — documents prepared; awaiting user approval.  
**Generated reference assets:** None.  
**GitHub integration status:** Arena's GitHub connector lookup returned `unsupported` in this conversation. The workspace checkout is `ogSulem/video` (remote `origin: https://github.com/ogSulem/video.git`) on `arena/f2208454-video`; files can be written locally, but no GitHub connector operations or remote publication have been performed.

## Sequential approval gates

1. **Stage 1 — setup and creative direction:** these documents and workflow. Await approval before proceeding.
2. **Stage 2 — master exterior architecture:** generate exactly one image; review and approve before it becomes the locked facility anchor.
3. **Stage 3 — master skier:** generate exactly one image only after Stage 2 is approved; review/approve proposed appearance before use.
4. **Stage 4 — interiors and equipment:** create/review one approved asset at a time, using approved architectural/character references and verifying actual facility equipment/services.
5. **Stage 5 — shot prompts:** write individual prompts based on approved references; obtain approval before generation.
6. **Stage 6 — video:** generate clips in narrative order and review each batch before continuing.
7. **Stage 7 — finishing:** edit, sound, VO, Russian titles, verified brand card, and separately composed vertical cut.

No paid operation without explicit authorization. Do not skip gates or replace approved assets without explicit approval.

## Asset manifest

| Filename / ID | Purpose | Status | Dependencies / notes |
|---|---|---|---|
| `production/creative_brief.md` | Project goals and guardrails | Draft — Stage 1 review | User brief; not an approved final creative |
| `production/visual_style_guide.md` | Shared look, light, camera, credibility rules | Draft — Stage 1 review | To be refined against approved references |
| `production/master_script.md` | 10-beat timing, Russian titles and VO | Draft — Stage 1 review | Brand, URL, medical claims unverified |
| `production/shot_list.md` | 20-shot production plan | Draft — Stage 1 review | Service/equipment shots are conditional |
| `production/continuity_guide.md` | Character, facility, action-axis rules | Draft — Stage 1 review | Proposed skier not yet approved/generated |
| `prompts/architecture.md` | Stage 2 exterior image brief | Draft — not submitted to image generation | Generate one image only after Stage 1 approval |
| `prompts/character.md` | Stage 3 skier design brief | Draft — not submitted to image generation | Hold until Stage 2 approval |
| `prompts/interiors.md` | Stage 4 reference brief | Draft — not submitted to image generation | Hold until Stages 2–3 and fact checks |

## Status vocabulary

`Draft` → `Awaiting approval` → `Approved` → `In production` → `QC review` → `Final`. Record the date/decision and any accepted changes when approval occurs. A generated file is not an approved asset merely because it exists.

## Factual verification before public release

Confirm legal center name and location, facility existence, actual available procedures/devices, staff roles/credentials, safety protocols, substantiation of medical/performance claims, logo and tagline rights, and ownership/operation of `altaysportreab.ru`. Verify all title/VO language with the client and appropriate clinical/legal reviewers. Until then, names, services, equipment, and claims in scripts are placeholders, not facts.
