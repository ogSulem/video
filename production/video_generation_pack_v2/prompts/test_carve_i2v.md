# Test prompt — single short image-to-video clip (carve in motion)

**Purpose:** Stage 3 quality gate. One short clip, animated from an approved still, to
prove the hosted model can produce genuine photoreal motion of our skier before
spending anything on the four full clips.
**Reference image:** `references/scenes/REF-SCENE-01-ski-descent.png`
**Requested:** shortest documented duration (see the workflow input; default 4 s,
832×480 as documented). Do not stretch a short clip to fill a window.

---

## Positive prompt

> Photoreal cinematic alpine footage, 16:9, natural overcast winter daylight, cool
> blue-grey grade, snow white / deep navy / charcoal palette, subtle organic film grain.
> Animate the skier from the reference image as a real moving shot: he is skiing a
> controlled carved turn at moderate speed, knees flexed, hips angulated over the
> outside ski, edges biting the soft snow, a thin plume of powder lifting off the uphill
> ski and drifting behind him. His upper body stays quiet and balanced, hands forward,
> poles carried naturally, head up looking down the fall line. The camera is on the
> downhill front-quarter side and tracks him smoothly with a gentle push; the slope and
> snow-dusted conifers slide past with believable parallax and the distant Altai ridge
> stays softly out of focus.
> Preserve exactly: the same face and light stubble, the same deep navy technical ski
> jacket with restrained orange zipper pulls, dark charcoal ski pants, matte black
> helmet, dark reflective goggles over the eyes, dark gloves, black ski boots, black
> skis, dark poles. Same age, same build, same kit. Do not change his identity.
> Believable skiing physics: weight through the outside ski, snow compressing under the
> edge, powder with mass, garment and helmet strap movement in the wind, natural motion
> blur on the snow only.
> No text, no subtitles, no logos, no signage, no watermark, no UI.

## Negative prompt

> text, letters, words, subtitles, captions, logo, watermark, UI, deformed face, face
> morph, identity change, different person, extra head, extra arms, extra hands, extra
> fingers, extra legs, duplicated body, merged limbs, floating limbs, warped skis, bent
> skis, fused skis, melted poles, skis through body, impossible lean, weightless
> floating, camera cut, second shot, split screen, montage, still image, frozen frame,
> slideshow, oversaturation, HDR halo, CGI gloss, cartoon, anime, 3D render look

## What to judge before approving the remaining clips

1. **Real motion** — is the body articulating through the turn, or is the frame just
   being pushed/scaled? (If it looks like a slow zoom on a photo, reject.)
2. **Identity** — same face, same jacket, same helmet; no drift.
3. **Anatomy** — no extra or merged limbs, hands stay hands, knees bend plausibly.
4. **Skis and poles** — straight, rigid, attached, no warping.
5. **Snow physics** — powder has mass and trails behind the edge; no floating dots.
6. **Camera** — smooth track, no snap zoom, no roll, horizon stable.
7. **Text** — nothing written appears anywhere in frame.

Approve only if 1–7 all pass. One rejected clip is cheaper than four.
