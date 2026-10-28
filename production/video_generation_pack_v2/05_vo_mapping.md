# Mapping: four clips → approved Russian voice-over → the 77-second edit

Voice-over: `audio/voiceover/voiceover_ru_full_v1.mp3` — **approved, locked, 70.16 s**.
It is never re-rendered, re-timed or re-worded. The picture is cut to it.

Edit baseline: `video/final/altai_rehabilitation_commercial_v2.mp4` — 77.00 s, 1920×1080, 24 fps.
The four clips replace four windows of that picture; every other beat stays on the
approved stills.

---

## Timeline

| Time | Approved VO (verbatim, per `editing/voiceover_final_ru.md`) | Picture | Source |
|---|---|---|---|
| 00:00–00:11 | «В горах всё решает мгновение. Скорость, поворот, снег — и привычный ритм обрывается.» | Controlled carve → edge lets go → fall → slides → lies frightened | **Clip A** (00:00, 11 s) |
| 00:11–00:19 | «После падения — тишина и вопрос: смогу ли я вернуться?» | Two rescuers arrive, assess, stabilise, move him on a sled | **Clip B** (11.0, 8 s) |
| 00:19–00:24 | «Ответ начинается не с громких обещаний.» | Center exterior, then reception welcome | `REF-SCENE-03`, `REF-SCENE-04` (stills) |
| 00:24–00:36 | «Сначала — разговор, внимание к движению, возможность спросить.» | Assessment → difficult first movement → supported exercise → teamwork | **Clip C** (24.0, 10 s of a 12 s clip) |
| 00:36–00:47 | «Без спешки и сравнения с чужим маршрутом.» | Seated mobility, specialist guidance | `REF-SCENE-07`, `REF-SCENE-06` |
| 00:47–00:55 | «Восстановление — не соревнование. Терпение, внимание к себе, поддержка рядом.» | Progress-check reprise, one-to-one support | `REF-SCENE-05 v2`, `REF-SCENE-08` |
| 00:55–01:02 | «Иногда шаг вперёд, иногда пауза, чтобы прислушаться к ощущениям.» | Calm repeats, warmer grade | `REF-SCENE-06`, `REF-SCENE-07` |
| 01:02–01:12 | «У каждого свой маршрут. … пусть это будет твой выбор — в своём темпе…» | Return to the slope, two clean carved turns, opens out | **Clip D** (62.0, 10 s) |
| 01:12–01:17 | *(no VO — narration ends at 01:10.16)* | Ridge to sky, then the typeset end card | `REF-SCENE-09` tail + `REF-SCENE-10` |

Live motion: **A 11 s + B 8 s + C 10 s + D 10 s = 39 s of 77 s**, i.e. half the film is
genuinely moving footage, the other half approved stills with eased reframes.

## Narration cues that must land on picture

| Cue | Word | Should land on |
|---|---|---|
| the fall | «обрывается» (~00:07–00:09) | the moment the edge lets go / the topple |
| the question | «смогу ли я вернуться?» (~00:10–00:12) | his frightened face in the snow (end of Clip A) or the rescuers reaching him |
| first "answer" | «Ответ начинается…» (~00:12–00:14) | rescuers' hands, i.e. early Clip B |
| the work | «возможность спросить» (~00:20–00:24) | end of Clip B / interior |
| effort | «Восстановление — не соревнование» (~00:24–00:27) | the hard first movement in Clip C |
| the return | «У каждого свой маршрут» (~00:42–00:44 after its paragraph start) | leave room: the return itself is Clip D at 01:02 |

Because Clip B introduces a rescue beat that the current v2 edit does not contain,
two things change editorially and need **owner sign-off before the final cut**:

1. the 00:08.5–00:14 aftermath hold and the 00:14–00:17 exterior push are compressed
   into 00:19–00:24 (the exterior gets ~4 s instead of 3 s, the aftermath still becomes
   a ~1 s flash or is dropped);
2. the provisional `assisted_arrival_keyframe_v1.png` insert is no longer needed —
   Clip B supersedes it.

The VO itself needs no change: the rescue sits exactly over «После падения — тишина и
вопрос», which is where a rescue belongs narratively.

## Where each clip is allowed to be shorter

| Clip | If it comes back at 5 s | If it comes back at 8 s |
|---|---|---|
| A | keep carve + fall + topple; drop the slide, freeze on the frightened face as a still from `REF-SCENE-02 v2` | keep everything except the longest part of the slide |
| B | keep arrival + assessment + blanket; end on the two rescuers kneeling | keep the sled loading, trim the down-slope move |
| C | keep **only** the difficult first movement + support (beats 2–3) | keep assessment + movement + support, drop the nod |
| D | keep one complete carved turn | keep both turns, shorten the exit |

## Audio handling

The approved mix is copied, never re-encoded: picture is re-encoded, audio is
`-c:a copy`. Result keeps AAC-LC 48 kHz stereo at the original 192 kbps. Clip soundtracks,
if any, are discarded.

## What is deliberately *not* in the edit

- No generated text, subtitles, logos, lower thirds or end cards.
- No ambulance, hospital, helicopter or clinical procedure.
- No diagnosis, no named injury, no timeline, no guaranteed return.
- No medical equipment beyond what the approved interiors already show.
- The final card stays typeset in post with the exact approved copy.
