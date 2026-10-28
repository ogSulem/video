# Sound design — director's cut v2

**Status (2026-10-28):** The v2 render uses an original deterministic synthetic score/ambience bed and designed procedural effects. No third-party music, recorded location sound/SFX, or external audio service was used. The approved Russian VO source remains unchanged.

## Musical arc and effects

- **Opening / descent (00:00–00:08):** restrained warm harmonic pad beneath shaped alpine-air texture; very soft synthetic ski-edge/snow noise supports the approved still's action. No claim of recorded slope sound.
- **Loss of control / impact (~00:07–00:08.7):** one muted low thump and brief broadband snow-brush accent at approximately 00:08.18; the sound is designed to support the off-screen/whiteout impact beat, not a recorded collision or injury.
- **Quiet aftermath (00:08.5–00:14):** music and wind duck sharply. The score/FX bed alone over 8–12 seconds measured −38.8 dB mean / −21.8 dB max. The approved VO continues unchanged over this near-silent bed; two very faint synthetic breath-like effects are not recorded breathing.
- **Arrival / assessment / recovery (00:14–01:03):** gradual warm harmonic lift and a soft pulse that enters during rehabilitation. Interior scenes receive music only; no invented dialogue, footsteps, clinical beeps, scanner/simulator noise, or treatment sounds.
- **Return / end card (01:03–01:17):** broader synthetic alpine-air texture accompanies the approved return still and mountain end-card still; the music resolves without suggesting a guaranteed outcome. The VO ends before the card's final hold.

## Mix notes and measurement

- Score, wind texture, ski-edge noise, impact, and breath-like effects are synthesized reproducibly by `video/render_altai_commercial.py`; the generated bed is not third-party music or recorded sound.
- The approved VO file `audio/voiceover/voiceover_ru_full_v1.mp3` is hash-pinned and used unchanged. The bed is ducked beneath narration and near-silent after the fall.
- Decoded v2 measurements (FFmpeg): approximately **−15.8 LUFS integrated**, **3.9 LU LRA**, and **−0.9 dBFS true peak**; `volumedetect` mean **−18.5 dB**, max sample **−0.9 dB**. These are descriptive, not a claim of compliance with an unspecified platform/client loudness target.
- A client-approved licensed or recorded score/SFX replacement, subjective listening approval, and final platform-specific loudness/true-peak settings remain optional finishing/release decisions. No external service is connected or implied.
