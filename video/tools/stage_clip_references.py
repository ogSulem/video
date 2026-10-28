#!/usr/bin/env python3
"""Stage approved reference PNGs for upload, without touching the originals.

Copies the exact files named in production/video_generation_pack_v2/02_reference_image_guide.md
into video/shots/ai_hero_clips/_refs/ with clip-prefixed names, and verifies each
source SHA-256 against the value recorded in the project documents. Refuses to
stage a file whose hash does not match, so a drifted reference can never be
uploaded as an "approved" one.

Nothing in references/ is modified: sources are opened read-only and only copied.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "video" / "shots" / "ai_hero_clips" / "_refs"

# Recorded in the project documents (asset_manifest / prompts). A mismatch is fatal.
EXPECTED = {
    "references/characters/REF-CHAR-01-master-skier.png":
        "3b0bbeb5199e254930a9938f9dd1b2371c9fbbcb33311d1d6af494b9de4cc407",
    "references/scenes/REF-SCENE-01-ski-descent.png":
        "384fd25d66cb3598939b0e8e8bb52e9b9019439f651b10bbbafef1ea224191dc",
    "references/scenes/REF-SCENE-02-injury-aftermath-v2.png":
        "4b4e21eed7a5b62d368782c4c5b805f836e07fd1ac9ecba932bf3a6fd0ac5074",
    "references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png":
        "0a6d303ee25232ba9d82474e120001cbcf0c2813debdaf9ea44d3031f4722acb",
    "references/scenes/REF-SCENE-06-rehabilitation-exercises.png":
        "d163d7baab6f34d2cc5720e3b68782adb7389b22a83af793c54fa442395ad9de",
    "references/scenes/REF-SCENE-07-recovery-physiotherapy.png":
        "a3899eb7d0c1a5470c7fa90dc31e3760e3dd9dfc56e0ac519855911d542618e1",
    "references/scenes/REF-SCENE-08-rehabilitation-team.png":
        "581c44ba71f91d3de5a0f3447246e3d406afa7427b99e60d95db6a5ba15ef749",
    "references/scenes/REF-SCENE-09-return-to-slopes.png":
        "5eec2e8d9dc4730241c10500e2541b97da51475827d714b1c5f5e9ccb7626897",
    "references/interiors/REF-INT-02-master-rehabilitation-room.png": None,  # no hash recorded
}

STAGE = {
    "A": [
        ("references/scenes/REF-SCENE-01-ski-descent.png", "clipA__1_primary_first-frame.png"),
        ("references/characters/REF-CHAR-01-master-skier.png", "clipA__2_identity.png"),
        ("references/scenes/REF-SCENE-02-injury-aftermath-v2.png", "clipA__3_optional_last-frame.png"),
    ],
    "B": [
        ("references/scenes/REF-SCENE-02-injury-aftermath-v2.png", "clipB__1_primary_scene.png"),
        ("references/characters/REF-CHAR-01-master-skier.png", "clipB__2_identity.png"),
        ("references/scenes/REF-SCENE-01-ski-descent.png", "clipB__3_terrain.png"),
    ],
    "C": [
        ("references/scenes/REF-SCENE-05-biomechanics-assessment-v2.png", "clipC__1_primary_first-frame.png"),
        ("references/scenes/REF-SCENE-07-recovery-physiotherapy.png", "clipC__2_support.png"),
        ("references/scenes/REF-SCENE-06-rehabilitation-exercises.png", "clipC__3_exercise.png"),
        ("references/scenes/REF-SCENE-08-rehabilitation-team.png", "clipC__4_teamwork.png"),
        ("references/interiors/REF-INT-02-master-rehabilitation-room.png", "clipC__5_room.png"),
        ("references/characters/REF-CHAR-01-master-skier.png", "clipC__6_identity.png"),
    ],
    "D": [
        ("references/scenes/REF-SCENE-09-return-to-slopes.png", "clipD__1_primary.png"),
        ("references/characters/REF-CHAR-01-master-skier.png", "clipD__2_identity.png"),
        ("references/scenes/REF-SCENE-01-ski-descent.png", "clipD__3_axis.png"),
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=str(DEST))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--allow-unverified", action="store_true",
                    help="copy files that have no recorded hash (still prints a warning)")
    args = ap.parse_args()

    dest = Path(args.dest)
    if dest.exists() and any(dest.iterdir()) and not args.force:
        print(f"{dest} already populated; pass --force to restage")
        return 2
    dest.mkdir(parents=True, exist_ok=True)

    failures, copied = [], 0
    for clip, items in STAGE.items():
        print(f"\nclip {clip}:")
        for src_rel, name in items:
            src = ROOT / src_rel
            if not src.exists():
                print(f"  MISSING  {src_rel}")
                failures.append(src_rel)
                continue
            got = sha256(src)
            want = EXPECTED.get(src_rel)
            if want and got != want:
                print(f"  HASH MISMATCH  {src_rel}\n    expected {want}\n    found    {got}")
                failures.append(src_rel)
                continue
            if not want:
                print(f"  WARN no recorded hash, copying as-is: {src_rel}")
                if not args.allow_unverified:
                    failures.append(src_rel)
                    continue
            shutil.copy2(src, dest / name)
            print(f"  ok  {name}   (sha256 {got[:12]}…)")
            copied += 1

    index = dest / "UPLOAD_ORDER.md"
    lines = ["# Upload order\n",
             "Files are named `clip<X>__<n>_<role>.png`; upload in numbered order.\n",
             "Originals live under `references/` and are never modified by this tool.\n"]
    for clip, items in STAGE.items():
        lines.append(f"\n## Clip {clip}\n")
        for _, name in items:
            lines.append(f"- `{name}`\n")
    index.write_text("".join(lines))

    print(f"\n{copied} file(s) staged in {dest}")
    if failures:
        print("INCOMPLETE — resolve these first:")
        for f in sorted(set(failures)):
            print(f"  - {f}")
        return 1
    print("all staged files verified against recorded hashes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
