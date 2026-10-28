# Reference-image guide — which approved image goes with which prompt

All paths are relative to the repository root. Every file listed here is an
**approved, locked** project reference and must be uploaded as-is — never
cropped, regraded, resized by hand, or re-exported.

To stage copies for upload without touching the originals (names become
`clipA__…`, `clipB__…` etc.), run:

```bash
.venv/bin/python video/tools/stage_clip_references.py
```

That tool verifies each source hash against the values recorded in the project
documents and fails loudly if anything drifted.

---

## Clip A — fall

| Role | File | Why this one |
|---|---|---|
| Primary (first frame) | `references/scenes/REF-SCENE-01-ski-descent.png` | The pre-fall carve on the correct action axis, same terrain and light |
| Identity | `references/characters/REF-CHAR-01-master-skier.png` | Canonical face, hair, stubble, navy jacket with orange pulls, helmet, goggles-up |
| Optional last frame | `references/scenes/REF-SCENE-02-injury-aftermath-v2.png` | Approved aftermath in the same snow and light (seated, not lying — see the prompt note) |

## Clip B — rescue

| Role | File | Why this one |
|---|---|---|
| Primary (scene, snow, light) | `references/scenes/REF-SCENE-02-injury-aftermath-v2.png` | The only approved image of him down in the snow: posture, snow state, light |
| Identity | `references/characters/REF-CHAR-01-master-skier.png` | Face and kit, so the patient is recognisably the same man |
| Terrain continuity | `references/scenes/REF-SCENE-01-ski-descent.png` | Slope, conifers and ridge so the rescue happens on the same mountain |

**No approved reference exists for the rescuers.** They are new content: mountain
ski-patrol in dark red/navy technical shells, helmets, gloves. Upload no image of
hospital staff or vehicles — the approved set contains none, and inventing one
would contradict the center's visual identity.

## Clip C — rehabilitation

| Role | File | Why this one |
|---|---|---|
| Primary (first frame) | `references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png` | Correct room, correct specialist, correct assessment pose, indoor training clothing |
| Exercise | `references/scenes/REF-SCENE-06-rehabilitation-exercises.png` | The approved controlled squat / split-squat beat |
| Support, seated mobility | `references/scenes/REF-SCENE-07-recovery-physiotherapy.png` | Plinth, gentle seated mobility, specialist supervising without touching |
| Teamwork | `references/scenes/REF-SCENE-08-rehabilitation-team.png` | The one-to-one supportive conversation, same two people |
| Room architecture (if the model needs a clean plate) | `references/interiors/REF-INT-02-master-rehabilitation-room.png` | Locks the room so it cannot be redesigned |

Use all five only if the generator accepts multiple references. If it accepts one:
`REF-SCENE-05-biomechanics-assessment-v2.png`. If two: add
`REF-SCENE-07-recovery-physiotherapy.png`.

## Clip D — return

| Role | File | Why this one |
|---|---|---|
| Primary | `references/scenes/REF-SCENE-09-return-to-slopes.png` | The approved return carve: same skier, same kit, goggles over the eyes |
| Identity | `references/characters/REF-CHAR-01-master-skier.png` | Canonical face and wardrobe |
| Action axis / terrain | `references/scenes/REF-SCENE-01-ski-descent.png` | Guarantees the return echoes the opening direction and camera side |

## Do **not** upload as generation references

| File | Reason |
|---|---|
| `references/scenes/REF-SCENE-10-final-brand-card.png` | Reserved background for the typeset end card; contains reserved text bands and must never be regenerated |
| `references/scenes/REF-SCENE-03-center-exterior-reveal.png` | Only needed if a shot is added outside these four clips |
| `references/scenes/REF-SCENE-04-reception-welcome.png` | Same — the reception beat is not one of the four clips |
| `video/assets/*.png` | Provisional, not approval-locked; not part of the approved continuity set |
| `references/scenes/REF-SCENE-02-injury-aftermath.png`, `REF-SCENE-05-biomechanics-assessment.png` | Archived v1 drafts, explicitly unapproved |

## Identity anchor

`references/characters/REF-CHAR-01-master-skier.png` is the single source of truth
for the face. Upload it with **every** clip, including C, even though the clothing
differs indoors: it is the only approved close view of his face with the goggles up.
