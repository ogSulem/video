# CLIP B — Mountain rescue: approach, assessment, stabilisation, stretcher transport

**Target slot in the edit:** 00:11–00:19 (8 s)
**Reference image (primary, scene/pose/light):** `references/scenes/REF-SCENE-02-injury-aftermath-v2.png`
**Reference image (identity):** `references/characters/REF-CHAR-01-master-skier.png`
**Reference image (terrain / light continuity):** `references/scenes/REF-SCENE-01-ski-descent.png`
**Requested duration:** longest available; 10 s preferred, 12 s if supported.
**Aspect / rate:** 16:9, 24 fps if selectable.

> **Scope note:** no approved reference exists of rescue personnel — this is genuinely new content, and the two rescuers below are the only figures to be invented. They must read as **mountain ski-patrol / rescue**, not as the rehabilitation center's staff, and must not carry any branding. Any implied diagnosis, treatment or timeline is out of scope and must not appear.

---

## Positive prompt (paste as one block)

> One single continuous shot, no cuts, no camera jump. Photorealistic cinematic alpine rescue footage, 16:9, 24 fps, flat overcast winter daylight, cool blue-grey grade, snow white / deep navy / charcoal palette, subtle film grain.
>
> PATIENT — preserve exactly the man in the reference images: same face, light stubble, deep navy technical ski jacket with restrained orange zipper pulls, dark charcoal ski pants, matte black helmet with dark reflective goggles pushed up, black gloves, black ski boots. He is lying on his side/back in disturbed deep snow beside his skis, frightened, breathing fast, conscious, alert. He does not stand, does not walk, does not try to get up at any point. No blood, no visible wound, no deformity, no bone, no dramatised agony.
>
> RESCUERS — two adult mountain ski-patrol rescuers in realistic technical winter mountain rescue clothing: dark red or navy shell jackets with reflective strips, dark trousers, helmets, gloves, small backpacks. Calm, trained, economical movements, no running, no panic. No white medical coats, no hospital uniforms, no branding on their clothing or equipment, no readable text on anything.
>
> PLACE — the same Altai slope as the reference: deep soft powder, disturbed snow where he slid, snow-dusted conifers, distant ridge out of focus, flat overcast light. Consistent with the fall: same terrain, same light, same downhill direction.
>
> ACTION, in this order, as one unbroken take:
> 1. (first ~25%) The two rescuers reach him from uphill, skis off, moving carefully in the deep snow. The first one kneels beside his head and speaks to him calmly; the patient's eyes move to the rescuer.
> 2. (~25–50%) Careful assessment in the snow: the rescuer steadies his helmet with both hands, checks his responsiveness and breathing, and keeps him still with a light hand on the shoulder. The second rescuer kneels at his legs and gently straightens the attached ski, then unfastens the boot. Hands and bodies stay anatomically correct; nothing is forced, nothing is twisted.
> 3. (~50–70%) Stabilisation: they wrap him in a folded thermal blanket, keep him flat and aligned, and slide a compact rescue sled / vacuum mattress under him with coordinated, practiced effort — a slow controlled log-roll onto the sled, one rescuer supporting the head and shoulders throughout. He stays conscious and frightened but cooperative.
> 4. (~70–100%) They lift and secure him on the sled, strap him in gently, and begin to move him down-slope at walking pace, one rescuer at the head and one at the foot. Camera lets them move slightly away from frame, snow spraying lightly off their boots, powder drifting. No ambulance, no vehicle, no clinic, no stretcher-carried running, no helicopter.
>
> CAMERA — one continuous camera on the downhill side of the action: medium-wide, steady, slowly pushing in as they work, then easing back and drifting with them as the sled starts to move. No cuts, no snap zooms, no orbit, no crossing to the other side of the action axis.
>
> PHYSICS — real weight in soft snow, real fabric, real cold breath, believable coordinated lifting by two trained people. Nothing floats, nothing intersects.

## Negative prompt

> text, letters, words, subtitles, captions, logo, watermark, UI, end card, branding, white medical coat, hospital uniform, ambulance, helicopter, hospital interior, blood, wound, exposed bone, graphic injury, leg bent impossibly, unnatural neck bend, patient walking, patient standing, patient running, rescuer running, extra rescuer, extra person, extra arms, extra hands, extra fingers, extra legs, duplicated body, merged bodies, floating limbs, deformed faces, identity change, different patient, warped skis, bent poles, camera cut, second shot, split screen, montage, still image, slideshow, oversaturation, HDR halo, CGI gloss, cartoon

## Notes for the operator

- **First frame:** if the model accepts one, `REF-SCENE-02-injury-aftermath-v2.png` gives the right snow, light and aftermath pose. Note it shows him *seated*; the prompt moves him to lying — choose first-frame only if that trade is acceptable, otherwise use it as a style/terrain reference only.
- If the generator cannot handle two rescuers plus a patient, split the beat: keep one rescuer and the sled, and drop the second rescuer rather than letting the model produce duplicated limbs.
- "Stabilize him" is deliberately written as *keep still, wrap, support, move* — avoid any instruction that implies diagnosis, splinting a specific injury, or treatment claims.
- If a stretcher/sled reads unrealistically, re-run with "compact rescue sled, low to the snow, one rescuer at the head, one at the foot, slow walking pace".
