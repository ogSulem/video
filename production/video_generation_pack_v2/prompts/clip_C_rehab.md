# CLIP C — Inside the center: assessment, hard early movement, support, progress

**Target slot in the edit:** 00:24–00:36 (12 s; trim to the best 8–10 s)
**Reference image (room + assessment):** `references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png`
**Reference image (exercise):** `references/scenes/REF-SCENE-06-rehabilitation-exercises.png`
**Reference image (therapist support / seated mobility):** `references/scenes/REF-SCENE-07-recovery-physiotherapy.png`
**Reference image (teamwork):** `references/scenes/REF-SCENE-08-rehabilitation-team.png`
**Reference image (room architecture):** `references/interiors/REF-INT-02-master-rehabilitation-room.png`
**Requested duration:** longest available; 10 s preferred. This clip carries the most beats, so more duration is better here than elsewhere.
**Aspect / rate:** 16:9, 24 fps if selectable.

---

## Positive prompt (paste as one block)

> One single continuous shot, no cuts. Photorealistic cinematic rehabilitation-center footage, 16:9, 24 fps, calm warm-neutral interior light, cool daylight from the panoramic windows balanced with soft warm interior accents, restrained contrast, subtle film grain.
>
> ROOM — preserve the exact room from the reference images: dark timber slat walls, stone, polished concrete floor, big windows with snow and Altai ridgeline outside, an existing treatment plinth, a bench, mats, resistance bands. Do not add machines, monitors, screens, hoists or treadmills. No text, no numbers, no posters, no signage anywhere, no branding on clothing or equipment.
>
> PEOPLE — the same male athlete throughout: same face and light stubble, fitted dark navy technical training top with subtle orange accents, dark charcoal training pants, clean neutral indoor cross-training shoes. The same female rehabilitation specialist throughout: understated sports-clinic clothing, dark athletic trousers, hair tied back, calm and professional. Two people only. No white coats. She supervises and guides verbally, she supports only lightly by the forearm or shoulder when the athlete steadies himself — no manipulation, no forcing a joint, no hands-on treatment of a specific injury.
>
> ACTION, in this order, as one unbroken take:
> 1. (first ~30%) Assessment: he stands on a firm floor in a controlled shallow squat, feet flat, knees tracking over the feet, spine neutral; the specialist observes from the side with a small tablet-free, hands-free attention, one calm cue of the hand. His expression is focused and slightly uncertain.
> 2. (~30–55%) Difficult early movement: he rises, shifts onto the affected leg, wobbles slightly, catches himself with a hand on the plinth and a small exhale. Effort and frustration, no pain grimace, no collapse, no fall indoors.
> 3. (~55–80%) Support and exercise: guided by her calm cue he performs two controlled shallow split-squat repetitions and a slow seated knee extension on the plinth. She stands close, attentive, ready but not touching.
> 4. (final ~20%) Gradual progress and teamwork: he finishes, straightens, breathes out, and gives a small acknowledging nod; she nods back. Both faces readable, quiet respect, understated emotion — work in progress, not triumph.
>
> CAMERA — a single steady medium-wide three-quarter camera at natural standing eye level, a very slow lateral drift and gentle push, continuous through the whole action, framing both people honestly. No cuts, no orbit, no handheld shake, no crash zoom.
>
> PHYSICS — believable human biomechanics: weight through the feet, knees tracking, breathing visible in the shoulders, natural fabric and shoe deformation, anatomically correct hands.

## Negative prompt

> text, letters, numbers, words, subtitles, captions, logo, watermark, UI, monitor, screen, dashboard, medical device, treadmill, hoist, machine, hospital bed, white coat, hospital scrubs, extra people, third person, deformed hands, extra fingers, extra arms, extra legs, fused limbs, duplicated heads, identity change, face morph, different athlete, different specialist, impossible knee bend, hyperextension, pain grimace, scream, collapse, blood, wound, injury close-up, camera cut, second shot, split screen, montage, still image, slideshow, oversaturation, HDR halo, CGI gloss, cartoon

## Notes for the operator

- This is the only clip with several distinct beats. If your generator can hold ~12 s, keep all four; if it caps at 5 s, generate this one **first** at the longest duration and drop beats 1 and 4 rather than compressing everything (a 5-second clip with four beats reads as chaos).
- Prefer `REF-SCENE-05-biomechanics-assessment-v2.png` as the first frame — it has the correct room, the correct specialist and the assessment pose; the prompt evolves from there.
- Keep the room fixed. The most common failure is the model "redesigning" the room between beats; the explicit "do not add machines / do not change the room" line is there to prevent it.
- If the athlete's face drifts, re-run with the identity sentence moved to the very start of the prompt and the room description shortened.
