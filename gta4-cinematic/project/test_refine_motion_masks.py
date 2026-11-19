"""Reproducibility and boundary checks for both intros' reviewed mattes."""
from pathlib import Path
import unittest

from PIL import Image

from refine_motion_masks import SELECTED, VERSIONS, correct


class ReviewedMaskTests(unittest.TestCase):
    def test_all_masks_rebuild_from_the_saved_sources(self):
        counts = {'spartak': 20, 'dubravnaya': 17}
        for root in VERSIONS:
            version = 'dubravnaya' if root.name == 'dubravnaya' else 'spartak'
            photos = sorted((root/'originals').glob('*.jpeg'))
            masks = sorted((root/'assets'/'motion_masks').glob('*.png'))
            self.assertEqual(len(photos), counts[version])
            self.assertEqual({p.stem for p in photos}, {p.stem for p in masks})
            for photo in photos:
                with self.subTest(version=version, name=photo.stem):
                    folder = 'motion_masks_source' if photo.stem in SELECTED[version] else 'intro_masks'
                    with Image.open(root/'assets'/folder/f'{photo.stem}.png') as source:
                        rebuilt = correct(version, photo.stem, source.convert('L'))
                    with Image.open(root/'assets'/'motion_masks'/f'{photo.stem}.png') as saved:
                        self.assertEqual(rebuilt.size, saved.size)
                        self.assertEqual(rebuilt.tobytes(), saved.convert('L').tobytes())
                        self.assertIsNotNone(saved.getbbox())

    def test_manually_checked_background_and_subject_pixels(self):
        # Background voids should be transparent, and adjacent subject pixels
        # (including the recovered cap brim and shoe) remain opaque.
        cases = {
            ('spartak', 'IMG_20210101_003521_Original'): [((320,240), 0), ((310,270), 255)],
            ('dubravnaya', 'IMG_6751'): [((190,1015), 0), ((225,810), 0), ((190,970), 255)],
            ('dubravnaya', 'IMG_6645'): [((660,455), 0), ((470,552), 255), ((660,480), 255)],
            ('dubravnaya', '3a003eeb6f62ae091f04215208f19bec'): [((310,650), 0), ((300,600), 255)],
        }
        for (version, name), points in cases.items():
            root = VERSIONS[1] if version == 'dubravnaya' else VERSIONS[0]
            with Image.open(root/'assets'/'motion_masks'/f'{name}.png') as im:
                for point, expected in points:
                    with self.subTest(version=version, name=name, point=point):
                        self.assertEqual(im.getpixel(point), expected)


if __name__ == '__main__':
    unittest.main()
