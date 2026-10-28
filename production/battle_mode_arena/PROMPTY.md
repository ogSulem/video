# Промпты для Arena.ai — копировать целиком

Правила для всех блоков:

- Копируйте **весь** текст блока в единственное поле промпта. Отдельного поля
  «negative prompt» на площадке нет — все запреты уже вписаны в текст.
- Только по-английски и без сокращений: модели читают английский точнее.
- Одна картинка на промпт, один смысловой бит на клип. Не добавляйте свои слова
  «покороче/подешевле/в стиле тикток» — это ломает единство фильма.
- Длительность не указываем: площадка сама даёт 5–8 с.

---

## Слот A1 — Карвинг (день 1, генерация 1)

**Файл:** `REF-SCENE-01-ski-descent.png`
**Место в фильме:** открытие, 00:00–00:07

```text
One continuous cinematic shot, no cuts, 16:9. Photorealistic alpine skiing film, natural overcast winter daylight, cool blue-grey grade, subtle film grain, 35mm lens, shallow depth of field.

Keep the man in the reference image exactly as he is: the same face and light stubble, the same deep navy technical ski jacket with small orange zipper pulls, the same dark charcoal ski pants, matte black helmet with dark reflective goggles worn over the eyes, dark gloves, black ski boots, black skis, dark poles. No logos, no brand marks.

He skis one confident, controlled carved turn at moderate speed on a wide powder slope in the Altai mountains: knees flexed, hips angulated over the outside ski, edges biting the snow, a thin plume of powder lifting from the ski tails, upper body quiet and calm. Snow-dusted conifers and a soft rocky ridgeline blurred in the distance behind him.

Camera: low tracking shot from the downhill front-quarter side, moving with him, a slow subtle push-in. He travels from upper right toward lower left and keeps that direction for the whole shot.

Realistic skiing physics and weight transfer, natural motion blur on the snow only.

No text, no subtitles, no logo, no watermark, no signage, no other people, no extra limbs, no deformed face, no warped or bent skis, no jump, no slow motion, no cartoon or CGI look.
```

**Должно получиться:** он едет, кант режет снег, снег летит с лыж, камера едет рядом.
**Брак:** лыжи гнутся, лицо плывёт, в кадре появляется второй человек, кадр стоит на месте.

---

## Слот D — Возвращение (день 1, генерация 2)

**Файл:** `REF-SCENE-09-return-to-slopes.png`
**Место в фильме:** финал, 01:02–01:12

```text
One continuous cinematic shot, no cuts, 16:9. Photorealistic alpine skiing film, natural winter daylight with soft high overcast and one lifted break of brighter light on the ridge, cool snow shadows, deep alpine blue and white palette, subtle film grain, 35mm lens.

Keep the man in the reference image exactly as he is: the same face, the same deep navy technical ski jacket with small orange zipper pulls, dark charcoal ski pants, matte black helmet with dark reflective goggles worn over the eyes, black gloves, black ski boots, the same skis and poles. No logos, no brand marks.

He enters frame already moving and links two clean carved turns at moderate speed: knees flexed, hips angulated over the outside ski, edges engaging, a sculpted plume of powder thrown from the ski tails, shoulders facing down the fall line, hands forward, poles carried with intent. The slope opens out beneath him and the Altai ridgeline fills the background.

Camera: wide-to-medium tracking shot from the downhill front-quarter side, smooth parallel motion with a gentle push. He travels from upper right toward lower left. At the very end the camera tilts slowly up and away from him toward the bright empty sky and the ridge line, ending on sky.

Confident, skilled, believable skiing, not a stunt, not a race, no jump, no airborne skis, no extreme edge angle.

No text, no subtitles, no logo, no watermark, no signage, no other people, no extra limbs, no deformed face, no warped or bent skis, no crash, no fall, no cartoon or CGI look.
```

**Должно получиться:** два резаных поворота и уход камеры в небо в конце.
**Брак:** падение, прыжок, зеркальное направление (едет слева-сверху вправо-вниз), текст.

---

## Слот A2 — Падение (день 2, генерация 1)

**Файл:** `REF-SCENE-01-ski-descent.png`
**Место в фильме:** 00:07–00:12 (сразу после карвинга)

```text
One continuous cinematic shot, no cuts, 16:9. Photorealistic alpine skiing film, natural overcast winter daylight, cool blue-grey grade, subtle film grain, 35mm lens.

Keep the man in the reference image exactly as he is: the same face and light stubble, the same deep navy technical ski jacket with small orange zipper pulls, dark charcoal ski pants, matte black helmet with dark reflective goggles, dark gloves, black boots, black skis, dark poles. No logos, no brand marks.

He is skiing a controlled carve at moderate speed. Without any cut, the downhill ski loses grip in the soft snow: his knee on that side collapses inward, his hips drop back over the tails, his shoulders rotate uphill, his arms open outward for balance. The skis swing flat and skid sideways across the fall line, throwing a low wide fan of powder. He topples backward and lands on his side in the deep soft snow, slides a short way and comes to rest, snow dust settling and drifting down-slope around him.

Slow, low-energy fall into deep powder, real falling weight, no acrobatics, no spin, no flight. He is clearly unhurt and nothing is graphic: helmet intact, calm face, no blood, no wound, no torn clothing. Skis stay attached or release naturally and never bend or warp.

Camera: low front-quarter tracking shot, drifting slightly closer as he goes down, then holding still while the snow settles.

No text, no subtitles, no logo, no watermark, no signage, no other people, no extra limbs, no deformed face, no graphic injury, no blood, no cartoon or CGI look.
```

**Должно получиться:** кант срывается → заваливается назад → мягко садится/ложится в снег, снежная пыль оседает.
**Брак:** кровь, «страшная» травма, кульбит, лыжи-пропеллер, кадр разваливается на два.

---

## Слот C — Восстановление (день 2, генерация 2)

**Файл:** `REF-SCENE-06-rehabilitation-exercises.png`
**Место в фильме:** 00:24–00:34

```text
One continuous cinematic shot, no cuts, 16:9. Photorealistic interior film, calm warm-neutral light, soft daylight from a window balanced with gentle interior warmth, restrained depth of field, subtle film grain, 35mm lens.

Keep the room and both people in the reference image exactly as they are: the same rehabilitation room, the same fitted dark navy training top with small orange accents and dark charcoal training pants on the man, the same female specialist in understated sports-clinic clothing, her identity and her calm observing manner. Do not add equipment, do not rearrange the furniture, do not change the room. No text or numbers on the walls.

He performs one controlled shallow bodyweight squat: both feet flat and stable, knees tracking naturally over the feet, spine neutral, controlled breathing, then a slow rise to standing. The specialist stands beside him, does not touch him, gives one small calm cue with her hand, and he answers with a short nod. Quiet focus and honest effort, no pain shown, no grimace, no theatrical emotion.

Camera: stable medium-wide three-quarter view, a very slow lateral reframe, unhurried and honest.

Realistic human biomechanics, anatomically correct hands and feet, natural fabric movement.

No text, no subtitles, no logo, no watermark, no signage, no medical device, no monitor, no hospital bed, no white coat, no other people, no extra limbs, no extra fingers, no deformed face, no impossible knee angle, no cartoon or CGI look.
```

**Должно получиться:** одно спокойное приседание и кивок, специалистка рядом.
**Брак:** придуманные приборы, белый халат, третий человек, вывернутые колени, текст на стене.

---

## Слот B — Приезд (день 3, генерация 1)

**Файл:** `REF-SCENE-03-center-exterior-reveal.png`
**Место в фильме:** 00:19–00:24

```text
One continuous cinematic shot, no cuts, 16:9. Photorealistic architectural film, natural winter daylight, cool exterior tones with warm interior glow through the glazing, refined contrast, subtle film grain, 35mm lens.

Keep the building in the reference image exactly as it is: the natural stone base, the dark vertical timber slats, the charcoal steel, the same glazing rhythm, roofline, entrance and railings. Do not redesign the architecture, do not move the entrance, do not add signage or any lettering.

A man in a deep navy technical ski jacket with small orange details and dark charcoal ski pants walks calmly toward the entrance, a matte black helmet under his arm and dark goggles in his hand, unhurt and steady, a little tired. Snow on the ground, soft snow falling in the air, mountains beyond the roofline. No other people.

Camera: wide grounded establishing move at standing eye level, slowly pushing toward the entrance and settling as he reaches the door.

Believable human walking gait, anatomically correct hands and face, warm human tone without staged stock-photo emotion.

No text, no subtitles, no logo, no watermark, no signage, no lettering, no ambulance, no medical equipment, no deformed hands, no distorted architecture, no other people, no cartoon or CGI look.
```

**Должно получиться:** камера медленно едет к входу, человек идёт к двери.
**Брак:** дом перерисован, появилась вывеска/логотип, кривые руки, толпа.

---

## Слот E — Снег и небо, «воздух» (день 3, генерация 2)

**Файл:** любой одобренный горный кадр (`REF-SCENE-09` подходит)
**Место в фильме:** переходы и дыхание между смысловыми кусками

```text
One continuous cinematic shot, no cuts, 16:9. Photorealistic alpine landscape film, soft high overcast winter light, deep alpine blue and white palette, subtle film grain, 35mm lens, shallow depth of field.

A snowy mountain ridge in the Altai mountains: wind lifts fine powder off the crest and it streams across the frame as a slow bright veil, snow-dusted conifers stand below the ridge line, distant peaks are soft in the haze.

Camera: a very slow upward tilt and gentle drift toward the bright empty sky, the ridge line sliding down out of frame, finally only sky. Smooth, stabilized, meditative.

Natural snow behaviour with real mass and gravity, sunlight diffused by thin cloud.

No text, no subtitles, no logo, no watermark, no signage, no people, no animals, no aircraft, no lens flare spam, no time-lapse flicker, no cartoon or CGI look.
```

**Должно получиться:** снег сдувает с гребня, камера уходит в небо. Чистая красота, без людей.
**Брак:** мерцание как в таймлапсе, «пластиковый» снег, текст.

---

## Если поле промпта не принимает такой объём

Скажите мне — сокращу до 500–600 символов, сохранив: кто он, что делает,
какой свет и оптика, и запрет на текст/логотипы. Смысл не потеряется.
