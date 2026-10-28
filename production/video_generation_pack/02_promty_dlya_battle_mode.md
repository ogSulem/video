# Промпты: 4 клипа для battle mode

Каждый блок — самодостаточный. Копируйте целиком. Если сервис принимает картинку —
приложите указанный файл из папки `references/`. Если принимает только текст —
используйте вариант «text-only», он уже содержит описание героя.

**Формат для всех:** 16:9, 24 fps (или «cinematic»), длительность 8–10 с,
один непрерывный кадр, без склеек, без текста.

---

## CLIP A — Карвинг и падение (00:00–00:12)

**Приложить:** `references/CLIP-A_def_P87-ski-descent.png`
**Альтернатива, если нужен более крупный план:** `references/CLIP-A_alt_carve-close.png`
**Длительность:** 10 с

**Prompt (EN, с референсом):**

> One single continuous cinematic shot, 10 seconds, 16:9, photorealistic, shot on 35mm with a long lens, natural overcast alpine daylight, cool blue-grey grade, subtle film grain.
> Preserve the person in the reference image exactly: the same man's face and light stubble, the same deep navy technical ski jacket with restrained orange zipper pulls, the same dark charcoal ski pants, matte black helmet, dark reflective goggles, dark gloves, black ski boots, black skis and dark poles. Do not change his face, his clothing, the colour grade or the lens.
> Camera: low front-quarter tracking camera on the downhill side of the action, moving with him, a slow modest push-in, the framing tightening slightly as the shot develops. Keep the same downhill direction and the same side of the action axis the whole time: he travels from upper right toward lower left. Snowy Altai slope, snow-dusted conifers and distant rocky ridges softly out of focus behind him.
> Action, in one unbroken take. First seconds: he holds a controlled carved turn at moderate speed, knees flexed, hips angulated over the outside ski, edges biting, a thin plume of powder off the uphill ski. Then, without any cut, the downhill ski loses grip in the soft snow: his knee on that side collapses inward, the hips drop back and the shoulders rotate uphill as he fights for balance, both arms opening outward, poles lifting off the snow. His weight goes behind his heels and the skis swing flat and sideways across the fall line, throwing a wide fan of powder. He topples backward and lands on his side in the deep soft powder with a soft snow burst, sliding a short way, and comes to rest, still, dust hanging in the air. He is clearly unhurt: helmet intact, calm face, the whole fall is slow and low-energy. Both skis stay attached or release naturally; skis never bend or warp.
> Realistic skiing physics throughout, believable weight transfer, natural motion blur on the powder only. No cuts, no camera cut, no second shot, no text, no logos, no signage, no watermark, no extra limbs, no duplicated body, no face change, no clothing change, no graphic injury, no blood, no medical scene.

**Дополнение text-only** (если картинку приложить нельзя): добавьте к промпту
> The man is about 32 years old, lean and athletic, short light-brown hair visible under a matte black helmet, dark mirrored goggles resting on the helmet above his eyes, light stubble, no scars. Practical alpine kit, no brand marks.

**Negative prompt:** `text, words, subtitles, logo, watermark, signature, blood, wound, injury close-up, deformed face, extra head, extra arms, extra legs, fused skis, bent skis, warped poles, cartoon, CGI gloss, oversaturated, HDR halo, slow-motion gore, jump cut, multiple shots, split screen`

---

## CLIP B — Приезд и встреча (00:17–00:24)

**Приложить:** `references/CLIP-B_def_exterior.png`
**Альтернатива, если нужен интерьер:** `references/CLIP-B_alt_reception.png`
**Длительность:** 8 с

**Prompt (EN, с референсом):**

> One single continuous cinematic shot, 8 seconds, 16:9, photorealistic, natural winter daylight with a cool exterior and warm interior glow, refined contrast, subtle film grain.
> Preserve the building in the reference image exactly: natural stone base, dark vertical timber slats, charcoal steel, the glazing rhythm, roofline, entrance and railings. Do not redesign the architecture, do not move the entrance, do not add signage or any lettering.
> Camera: wide, grounded establishing move, slowly pushing toward the entrance at standing eye level, then settling as the door opens. One unbroken take, no cut.
> Action: the same male skier, about 32, lean athletic build, short light-brown hair, light stubble, deep navy technical ski jacket with restrained orange details, dark charcoal ski pants, matte black helmet under his arm and dark goggles in his hand, no skis, walks calmly toward the entrance, a little tired but steady and unhurt. A single friendly team member in understated non-branded sports-clinic clothing — no white coat, no medical uniform — appears at the doorway and greets him with a quiet, respectful nod, natural eye contact, no handshake performance, no exaggerated smile. Snow on the ground, soft falling snow in the air, mountains beyond.
> Believable human motion, natural walking gait, anatomically correct hands and faces, warm human tone without staged stock-photo emotion. No cuts, no text, no logos, no signage, no watermark, no medical equipment, no hospital, no ambulance, no extra people, no diagnosis, no distress.

**Negative prompt:** `text, signage, lettering, logo, watermark, white coat, hospital bed, ambulance, blood, crutches, bandage, extra people, deformed hands, distorted architecture, changing building design, CGI gloss, oversaturation, multiple shots, split screen`

---

## CLIP C — Восстановление под наблюдением (00:28–00:36)

**Приложить:** `references/CLIP-C_def_exercise.png`
**Альтернатива:** `references/CLIP-C_alt_physio.png`
**Длительность:** 8 с

**Prompt (EN, с референсом):**

> One single continuous cinematic shot, 8 seconds, 16:9, photorealistic, calm warm-neutral interior light, cool daylight from a window balanced with soft interior warmth, restrained depth of field, subtle film grain.
> Preserve the room and the two people from the reference image exactly: the same rehabilitation room, the same fitted dark navy technical training top with subtle orange accents, dark charcoal training pants, neutral indoor cross-training shoes, the same female specialist in understated sports-clinic clothing, her identity, her calm observing manner. Do not add equipment, do not rearrange furniture, do not change the room, do not add any text or numbers on walls.
> Camera: stable medium-wide three-quarter view, a very slow lateral reframe, the framing staying honest and unhurried. One unbroken take, no cut.
> Action: a controlled, shallow bodyweight squat — both feet flat and stable, knees tracking naturally over the feet, spine neutral, breathing visible, then a slow rise to standing. The specialist observes from beside him without touching, gives one small calm cue with her hand, and he answers with a short nod. Quiet focus and effort, no pain displayed, no strain grimace, no theatrical emotion — this is work, not suffering. The skier's face stays clearly recognisable.
> Realistic human biomechanics, natural fabric movement, anatomically correct hands and feet, small believable camera breathing. No cuts, no text, no logos, no watermark, no medical device, no monitor, no invented equipment, no diagnosis, no extra people, no injury close-up.

**Negative prompt:** `text, numbers, monitor UI, screen, logo, watermark, extra people, deformed hands, extra fingers, extra limbs, distorted posture, impossible knee angle, pain grimace, blood, medical device, hoist, treadmill not in reference, CGI gloss, multiple shots`

---

## CLIP D — Возвращение на склон (01:02–01:12)

**Приложить:** `references/CLIP-D_def_return.png`
**Длительность:** 10 с

**Prompt (EN, с референсом):**

> One single continuous cinematic shot, 10 seconds, 16:9, photorealistic, natural late-afternoon alpine light, cool snow shadows, deep alpine blue and white palette, subtle film grain.
> Preserve the person in the reference image exactly: the same face, the same deep navy ski jacket with restrained orange accents, dark charcoal pants, matte black helmet, dark reflective goggles now worn over the eyes, dark gloves, black boots, the same skis and poles. Do not change his face, kit or equipment, do not add logos.
> Camera: wide tracking shot from the downhill front-quarter side, moving with him along the same action axis as the opening shot — he travels from upper right toward lower left — then, at the end, the camera tilts slowly up and away from him toward the bright sky and the empty ridge line, ending on sky. One unbroken take, no cut.
> Action: he enters frame and links two confident, controlled carved turns at moderate speed, weight balanced, skis edged and in contact with the snow, a restrained plume of powder following the edges. Confident and calm, not a stunt, not superhuman, no jump, no airborne skis. As the camera rises past him, the slope and the Altai ridgeline fill the frame and the image opens into bright overcast sky.
> Realistic skiing physics, natural snow spray, believable body mechanics. No cuts, no text, no logos, no watermark, no signage, no guaranteed-triumph gesture, no extra limbs, no warped skis, no face change, no graphic injury.

**Negative prompt:** `text, logo, watermark, signage, jump, airborne skis, bent skis, warped poles, deformed face, extra limbs, impossible lean, cartoon, oversaturation, HDR halo, multiple shots, split screen, lens flare spam`

---

## Служебная склейка (добавлять в конец любого промпта при необходимости)

> Continuity: the same man in all shots, the same navy jacket with orange details, the same charcoal pants, the same matte black helmet and dark goggles, the same skis and poles, the same winter overcast sky and the same Altai geography. No brand names, no readable text anywhere in frame. This is a premium outdoor-sports commercial, photoreal, restrained, no spectacle beyond what is described.
