# CLIP A — Loss of control, fall, slide, and lying afraid

**Target slot in the edit:** 00:00–00:11 (11 s)
**Reference image (primary):** `references/scenes/REF-SCENE-01-ski-descent.png`
**Reference image (secondary, identity):** `references/characters/REF-CHAR-01-master-skier.png`
**Reference image (end state, optional last frame):** `references/scenes/REF-SCENE-02-injury-aftermath-v2.png`
**Requested duration:** longest available that keeps motion coherent; ask for 10 s minimum, 12 s if the model allows.
**Aspect / rate:** 16:9, 24 fps if selectable.

---

## Positive prompt (paste as one block)

> One single continuous shot, no cuts, no camera jump, no time jump. Photorealistic cinematic alpine footage, 16:9, 24 fps, natural overcast winter daylight, cool blue-grey grade with a restrained palette of snow white, deep navy and charcoal, subtle organic film grain.
>
> SUBJECT — preserve the man in the reference images exactly: the same face and light stubble, deep navy technical ski jacket with restrained orange zipper pulls, dark charcoal ski pants, matte black helmet with dark reflective goggles, dark gloves, black ski boots, black skis, dark ski poles. Same age impression, same build, same kit throughout. No logo, no brand mark, no badge, no scar.
>
> PLACE — an authentic Altai ski slope in winter: soft ungroomed powder over a firm base, snow-dusted conifers at the edges, distant rocky ridgeline slightly out of focus, flat overcast sky. Camera is on the downhill front-quarter side of the skier, on the same side of the action axis for the entire shot; he travels from upper right toward lower left of frame.
>
> ACTION, in this order, as one unbroken take:
> 1. (first ~25%) He is competently skiing a controlled carved turn at moderate speed — knees flexed, hips angulated over the outside ski, edges biting, a thin plume of powder lifting off the uphill ski, upper body calm and confident.
> 2. (~25–45%) Without any cut, the downhill ski loses grip in the soft snow. His knee on that side collapses inward, the hips drop back over the tails, shoulders rotate uphill; his arms open outward for balance and the pole tips lift off the snow. His expression changes from concentration to alarm.
> 3. (~45–65%) The skis swing flat and skid sideways across the fall line, throwing a wide low fan of powder. His weight goes behind his heels and he topples backward, landing on his side and back in the deep soft snow with a soft burst of powder. Realistic falling weight, no acrobatics, no spin, no flight.
> 4. (~65–85%) He slides a short distance and comes to rest. Snow dust settles around him, fine crystals hanging in the air and drifting down-slope. One ski stays attached, the other lies flat nearby; one pole near his hand, one behind him.
> 5. (final ~15%) He lies still in the snow, propped slightly on one elbow, and looks up the slope with genuine fear and disbelief — wide eyes, quick shallow breathing, mouth slightly open. Frightened, vulnerable, but conscious and not gory: no blood, no visible wound, no deformity, no bone, no torn clothing.
>
> CAMERA — one continuous camera: low, front-quarter, tracking with modest speed, drifting slightly closer as the fall happens, settling and holding on the frightened face at the end. Smooth, stabilized motion, no whip pan, no crash zoom, no handheld shaking.
>
> PHYSICS — believable skiing mechanics: edges, weight transfer, drag of skis on soft snow, powder behaving like real powder with mass and gravity. Garments and helmet straps move naturally.
>
> No text, no subtitles, no captions, no logos, no signage, no watermark, no UI, no end card, no lower third.

## Negative prompt

> text, letters, words, subtitles, captions, logo, watermark, UI, end card, graphic injury, blood, wound, exposed bone, bruising close-up, medical gore, pain scream, deformed face, face morph, identity change, different person, extra head, extra arms, extra hands, extra fingers, extra legs, duplicated body, floating limbs, fused skis, bent skis, warped poles, melted poles, skis through body, walking after fall, standing up, unrealistic ragdoll, weightless jump, camera cut, second shot, split screen, montage, still image, frozen frame, slideshow, zoom artifacts, oversaturation, HDR halo, CGI gloss, cartoon, anime, 3D render look

## Notes for the operator

- If the model accepts a **first frame**, use `REF-SCENE-01-ski-descent.png` (pre-fall carve, correct axis).
- If it accepts **first + last frame**, use `REF-SCENE-02-injury-aftermath-v2.png` as the last frame — but note that keyframe shows him *seated upright*, while this prompt ends with him *lying down*. Only pair them if you accept a small pose change at the end; otherwise first-frame only.
- If the fall reads as a stunt, re-run with the words "slow, low-energy fall into deep powder, no acrobatics" emphasised and keep the same seed if seeds are available.
- The frightened face must stay recognisable: if the generator tends to hide the face, add "face clearly visible, snow only lightly on the jacket".
