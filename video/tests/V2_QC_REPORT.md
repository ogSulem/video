# Director's cut v2 — render and QC record

**Status:** Technically rendered and decode-verified; awaiting owner review and any applicable clinical, legal, brand, and release approval. This is a still-based director's rework, not generated moving footage.

## Deliverable

- **File:** `video/final/altai_rehabilitation_commercial_v2.mp4`
- **Runtime / frames:** 77.00 seconds / 1,848 frames
- **Picture:** 1920 × 1080, 16:9, progressive, 24 fps, Rec.709, H.264 High Profile / yuv420p
- **Audio:** AAC-LC, stereo, 48 kHz, 192 kb/s
- **File size:** 45,420,896 bytes
- **SHA-256:** `86fdee75baf13a2183d219e34f65b9bd8ffe9c916a11722808ae0d3a79390410`
- **Baseline preserved:** v1 remains at `video/final/altai_rehabilitation_commercial_v1.mp4`; its recorded hash remains `c41468ce4342c8349f2d3936f2b5a935242695d8b58afbcb8071404bb852acd2`.

## Technical checks

- The v2 renderer verified SHA-256 for all 13 pinned inputs before and after render: nine approved scene stills, the unchanged approved Russian voice-over, and three separately pinned provisional AI-generated stills.
- The approved VO file remains byte-identical: `audio/voiceover/voiceover_ru_full_v1.mp3`, SHA-256 `7d5368d3075ba16c30e9f6bf717d477c1ff2c6eb51bf59dba2a86b6d199376f1`.
- FFmpeg decoded the entire 77-second MP4 with no error. Stream metadata confirms 1,920 × 1,080, 24 fps, H.264 High/yuv420p, AAC-LC stereo 48 kHz, and 77.00 seconds.
- Visual frames were inspected at representative opening/action, loss-of-control, impact/aftermath, exterior/arrival, reception, rehabilitation/teamwork, return, and end-card timecodes. The loss-of-control keyframe is distinct from the later seated aftermath image; the impact is bridged with a short snow-white transition, not falsely represented by the aftermath still.
- The v2 end card is a new provisional generated landscape **still** with supersampled rendered type. Exact copy is present: `РЕАБИЛИТАЦИОННЫЙ ЦЕНТР АЛТАЙ`, `Твой сезон продолжается.`, `altaysportreab.ru`. No official logo/emblem was found or fabricated; the decorative motif in locked Scene 10 is not used as a logo.
- No approved still or VO source was edited or overwritten.

## Motion provenance and limitations

- The skiing, fall transition, snow, camera drift, interior exercise beats, return, and mountain-to-sky ending use keyframed 2D camera crops, short cross-dissolves, and procedural snow/breath/impact layers over still images.
- The new fall, supported-arrival, and mountain end-card plates were generated as still images, not video. The skier's body does not articulate in the fall or skiing scenes; there is no genuine image-to-video, live-action, or generated subject motion in v2.
- The earlier six-second capability test is category C; see `video/tests/MOTION_TEST_REPORT.md`.

## Audio measurements

- The approved 70.16-second Russian VO remains unchanged and is mixed over an original deterministic synthetic score/ambience bed. Synthetic wind/ski texture and a restrained designed impact are not recorded location sound or clinical procedure sounds.
- On the delivered MP4, FFmpeg `ebur128` measured approximately **−15.8 LUFS integrated**, **3.9 LU LRA**, and **−0.9 dBFS true peak**. `volumedetect` reported **−18.5 dB mean** and **−0.9 dB max sample**. The AAC audio stream decodes to about 77.013 seconds including standard codec frame padding; the edited program duration is 77.00 seconds.
- The score/FX bed alone over 8–12 seconds, around the fall and aftermath, measured **−38.8 dB mean** / **−21.8 dB max**; the VO continues by design and was not muted or altered. The bed ducks to near-silence under the aftermath narration.
- Platform/client loudness targets and final subjective mix approval remain outstanding; these measurements are descriptive, not a claim of delivery-spec compliance.

## Review gate

The export is a technically verified review master, not automatically cleared for public advertising. Review the three new provisional stills for character/continuity, confirm brand/domain and all factual claims, and set any client/platform loudness or rights requirements before release. If true moving AI/video footage is a must-have, the single next dependency is an available, approved image-to-video service or supplied/licensed motion clips; this workspace has neither.
