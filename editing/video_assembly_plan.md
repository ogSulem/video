# Video assembly plan — RETURN TO THE SLOPE, director's cut v2

**Status (2026-10-28):** The approximately 77-second v2 is rendered and technically verified at `video/final/altai_rehabilitation_commercial_v2.mp4`. It is a new review export; the v1 baseline remains unchanged at `video/final/altai_rehabilitation_commercial_v1.mp4`. Approved source stills and approved Russian VO remain hash-identical. The v2 adds three new AI-generated **still images** as provisional editorial inserts; these are not yet owner-approved.

**Important motion classification:** The test-first render is category C (programmatic 2D motion over a still). The v2 also uses only still-image camera crops, compositing, overlays, and cross-dissolves. There is no genuine image-to-video, moving AI footage, live-action clip, or articulated skier motion. Do not describe its stills as video footage.

**Target / actual:** 77.00 seconds, 1920 × 1080, progressive 16:9, 24 fps.

## 1. Test-first capability audit and constraints

- Before beginning the commercial rework, the six-second capability test `video/tests/skier_motion_test_v1.mp4` was rendered, decoded, and inspected at multiple points. It shows a slow digital camera push and procedural drifting snow on the locked `REF-CHAR-01` still; the skier's body does not move. Its category-C classification and checksum are recorded in `video/tests/MOTION_TEST_REPORT.md`.
- The current session tools exposed still-image generation, but no image-to-video/video-generation workflow. The local environment audit found no GPU/model runtime and did not establish an external video API/service. The available repeatable rendering route is pinned PyPI-based FFmpeg/Pillow/NumPy.
- The earlier described green-field/cloud method has no accessible asset, script, prompt, or workflow in this repository/session. Its provenance remains unknown; no technique is inferred or claimed.
- V2 therefore uses restrained still animation and adds new still keyframes only where they clarify the narrative. It does not pretend to solve the lack of true subject movement.
- No official logo/emblem file or brand-font package was found. The decorative mark in approved Scene 10 is not an official logo; v2 does not use it as one. The exact approved name, tagline, and URL are typeset in post.

## 2. Picture plan — exact v2 timeline

All times are seconds from program start. All move descriptions refer to digital reframing or compositing of a still, not a physical camera move. Smooth eased camera paths, brief motivated dissolves, and a consistent action axis replace abrupt/random jumps.

| # | Time / duration | Source and beat | Director's treatment | Sound / narration |
|---:|---|---|---|---|
| 01 | 00:00–00:04 / 4.0s | Approved Scene 1, `REF-SCENE-01-ski-descent.png` | Establish the slope and skier with a restrained opening fade and slow wide push. The fall's movement axis is set here. | Soft synthetic alpine air; approved VO begins unchanged. |
| 02 | 00:04–00:07 / 3.0s | Same Scene 1 still | Continuous move into a closer tracking crop; the end framing of shot 1 is the start framing here. Procedural snow/ski texture stays restrained. | A little more synthetic edge/snow texture; VO remains front. |
| 03 | 00:07–00:08.5 / 1.5s | Provisional `skier_loss_of_control_keyframe_v1.png` | Short snow-motivated dissolve into a visibly off-balance, pre-impact keyframe. Small roll/push and a brief procedural powder burst lead toward white. This still is not the impact and contains no articulated fall. | Designed low snow/thump accent near 00:08.18; music and wind drop rapidly. |
| 04 | 00:08.5–00:09.1 / 0.6s | Approved Scene 2 aftermath, `REF-SCENE-02-injury-aftermath-v2.png` | Snow-white transition resolves into the seated aftermath. This separate image is not misrepresented as the fall. | Near-silent bed begins; VO continues as approved. |
| 05 | 00:09.1–00:14 / 4.9s | Same approved Scene 2 aftermath still | Slow close push; sparse snow and a faint breath-like visual cue hold the quiet, disoriented aftermath. No diagnosis or visible injury is added. | Score/FX bed remains near silence; a very soft synthetic breath-like texture only. |
| 06 | 00:14–00:17 / 3.0s | Approved Scene 3 exterior, `REF-SCENE-03-center-exterior-reveal.png` | Short dissolve from cold slope to the established center exterior; slow push toward entrance, no geometry warp. | Warm harmonic bed starts returning; VO continues. |
| 07 | 00:17–00:21 / 4.0s | Provisional `assisted_arrival_keyframe_v1.png` | Supported arrival at the exterior entrance: companion has an arm around the skier; slow forward reframe. It is an arrival still, not moving footage or proof of a particular service. | Gentle exterior air; no invented siren, clinical, or device sound. |
| 08 | 00:21–00:24 / 3.0s | Approved Scene 4, `REF-SCENE-04-reception-welcome.png` | Warm match dissolve into reception; restrained push and clear eyelines. | Synthetic score warms; approved VO unchanged. |
| 09 | 00:24–00:28 / 4.0s | Approved Scene 5 v2, `REF-SCENE-05-biomechanics-assessment-v2.png` | Calm medium-wide assessment hold, then gentle push. Show only the depicted supervised movement; no diagnostic overlays/equipment added. | Music only under VO; no invented clinic beeps. |
| 10 | 00:28–00:32 / 4.0s | Approved Scene 7, `REF-SCENE-07-recovery-physiotherapy.png` | First measured seated mobility beat; stable crop and patient/specialist relationship remain understandable. | Soft synthetic room tone; no clinical procedure claim. |
| 11 | 00:32–00:36 / 4.0s | Approved Scene 6, `REF-SCENE-06-rehabilitation-exercises.png` | Show the depicted controlled split squat; warm, slow lateral reframe. | Sparse pulse begins to enter. |
| 12 | 00:36–00:39 / 3.0s | Same Scene 6 still | Continuous closer reframe toward effort and stance; no body/limb warping or invented action. | Pulse remains gentle. |
| 13 | 00:39–00:43 / 4.0s | Approved Scene 7 still | Return to guided knee mobility as a calmer counterpoint; short motivated dissolve from the effort detail. | Music opens slightly; VO continues. |
| 14 | 00:43–00:46 / 3.0s | Same Scene 7 still | Closer crop toward the specialist's attentive guidance, preserving the skier's position and eyeline. | No added treatment/device sound. |
| 15 | 00:46–00:51 / 5.0s | Approved Scene 8, `REF-SCENE-08-rehabilitation-team.png` | Establish the one-to-one team/support relationship in a stable medium-wide view. | The warm harmonic bed grows subtly. |
| 16 | 00:51–00:55 / 4.0s | Same Scene 8 still | Continuous close reframe; hold the conversation and teamwork without inventing dialogue. | Music continues beneath approved VO. |
| 17 | 00:55–00:59 / 4.0s | Approved Scene 5 v2 still | A calm progress-check reprise; new crop and warmer grade distinguish it from the first assessment beat. No outcome claim. | Soft pulse grows. |
| 18 | 00:59–01:03 / 4.0s | Approved Scene 6 still | Confident, still-controlled exercise reprise; the story advances through framing/color, not fabricated body motion. | Score begins its return lift. |
| 19 | 01:03–01:08 / 5.0s | Approved Scene 9, `REF-SCENE-09-return-to-slopes.png` | Hero return carve; slow push follows the established direction and action axis. Snow overlay is light and purposeful. | Alpine air and snow-edge texture return; score lifts without a triumphal guarantee. |
| 20 | 01:08–01:11 / 3.0s | Same approved Scene 9 still | Continue the crop upward toward sky/mountain. This is a simulated digital reframe, not a true camera tilt or second clip. | Music resolves; full approved VO ends at about 01:10.16. |
| 21 | 01:11–01:17 / 6.0s | Provisional `endcard_altai_landscape_v1.png` | Dissolve into the wide generated Altai landscape still, then continue a gentle upward digital reframe. Reveal exact rendered typography in sequence without boxes or an invented mark; hold the complete URL through the end. | VO-free end card; synthetic score resolves and fades. |

**Total: 77.00 seconds.** V2 contains 21 editorial beats. Repeated recovery stills are deliberate crops/reprises from the approved scene set; they do not become moving footage through the edit.

## 3. Motion, transitions, and image treatment

- The fall sequence distinguishes three beats: (1) the skier visibly loses balance in the new still, (2) a brief designed snow impact/whiteout, and (3) the separate approved seated aftermath. The render never calls the aftermath image a fall clip.
- The supported-arrival still follows the exterior establishing view and precedes the reception scene. No ambulance, clinical procedure, diagnosis, treatment, or unverified service is implied.
- Snow and breath cues are restrained generated compositing effects. They are not recorded weather/breath and do not imply injury severity.
- Camera movement is eased digital crop/scale/position; shots 1–2, 4–5, 11–12, 13–14, 15–16, 19–20 use continuous endpoints where they share a source. Dissolves are used only for location or atmosphere changes.
- All approved reference PNGs remain unchanged. New AI-generated stills are hash-pinned for reproducibility but remain provisional and owner-review candidates; a generated still is not approved merely because it is in the cut.
- No motion vectors, interpolated anatomy, face morphing, fake camera footage, fabricated logo, or external-service claim is used.

## 4. Locked copy and VO

The approved, unchanged narration is `editing/voiceover_final_ru.md` and `audio/voiceover/voiceover_ru_full_v1.mp3` (70.16 seconds; source SHA-256 `7d5368d3075ba16c30e9f6bf717d477c1ff2c6eb51bf59dba2a86b6d199376f1`). It is mixed from the opening; the picture timeline does not alter its wording or source file. The VO ends before the six-second end card.

Typeset the owner-approved copy exactly, in post-production:

**РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ**

**Твой сезон продолжается.**

**altaysportreab.ru**

The end-card serif/sans type is rendered at high resolution and downsampled for clean edges. No logo or emblem is added. The motif in approved Scene 10 remains decorative only and is not presented as an official logo.

## 5. Sound design and measured levels

- V2 uses a deterministic original synthetic pad/pulse, shaped alpine-air texture, restrained ski-edge noise, one muted designed snow impact around 00:08.18, and two faint breath-like synthetic effects in the aftermath. No licensed/recorded score, recorded location sound, conversation, device beep, medical procedure sound, or external audio service was used.
- The score/FX bed alone over 8–12 seconds measured −38.8 dB mean / −21.8 dB max; the approved VO continues unchanged over this near-silent bed.
- The rendered program measured about −15.8 LUFS integrated, LRA 3.9 LU, and −0.9 dBFS true peak (FFmpeg `ebur128`); decoded mean level was −18.5 dB. The AAC audio stream decodes to about 77.013 seconds including standard codec frame padding; the edited program duration is 77.00 seconds. These are descriptive measurements; client/platform delivery loudness requirements were not supplied. Final subjective mix/loudness approval remains open.
- The timeline and source are the reproducible mix; re-render with `video/render_altai_commercial.py` after any authorized change. Never alter the locked VO without approval.

## 6. Export and reproducibility

- Renderer: `video/render_altai_commercial.py`; previous v1 renderer is preserved as `video/render_altai_commercial_v1.py`. Pinned dependencies are in `video/requirements.txt`; setup and commands are in `video/README.md`.
- FFmpeg 7.0.2 from the `imageio-ffmpeg` PyPI wheel with `libx264`; Pillow 13.0.0; NumPy 2.4.6.
- V2 delivery: 1920 × 1080 progressive, 24 fps, Rec.709, MP4 / H.264 High / yuv420p + AAC-LC stereo 48 kHz / 192 kb/s.
- Existing outputs are not overwritten unless `--force` is explicit. Input hashes are checked before and after render; v1 is never the v2 output target.
- Reproduce after installing the pinned requirements:

```bash
.venv/bin/python video/render_altai_commercial.py --verify-only
.venv/bin/python video/render_altai_commercial.py
```

## 7. QC / render record — 2026-10-28

- **V2:** `video/final/altai_rehabilitation_commercial_v2.mp4`; 45,420,896 bytes; SHA-256 `86fdee75baf13a2183d219e34f65b9bd8ffe9c916a11722808ae0d3a79390410`; 77.00 s / 1,848 frames.
- **V1 baseline:** `video/final/altai_rehabilitation_commercial_v1.mp4`; unchanged; SHA-256 `c41468ce4342c8349f2d3936f2b5a935242695d8b58afbcb8071404bb852acd2`.
- **Full decode:** FFmpeg decoded the complete v2 with no errors. Probe confirms 1920 × 1080, 24 fps, 77.00 s, H.264 High/yuv420p, Rec.709, AAC-LC stereo 48 kHz.
- **Visual sampling:** checked opening and action, the loss-of-control/whiteout/aftermath distinction, exterior and supported arrival, reception, exercises/teamwork, return, sky reframe, and end-card timing. Exact copy is present and legible at the final hold. No new official logo or source-image edits.
- **Source integrity:** all 13 inputs were hash-verified before/after render; the locked VO SHA is unchanged. V1 remains separate.
- **QC report:** `video/tests/V2_QC_REPORT.md`; motion test report: `video/tests/MOTION_TEST_REPORT.md`.
- **Release gate:** technically verified does not mean owner-approved or medically/legal/brand cleared. Review the three new still inserts, confirm factual/rights requirements and platform loudness, then approve separately before public use.
