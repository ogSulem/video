"""The approved Spartak montage order should not be silently rearranged."""
import unittest
from unittest.mock import patch

import render_intro


class SceneOrderTests(unittest.TestCase):
    def test_current_sequence_passes(self):
        render_intro.validate()

    def _assert_swap_rejected(self, a, b):
        scenes = list(render_intro.SCENES)
        self.assertEqual(scenes[a].frames, scenes[b].frames)
        scenes[a], scenes[b] = scenes[b], scenes[a]
        with patch.object(render_intro, 'SCENES', scenes):
            with self.assertRaisesRegex(ValueError, 'approved order'):
                render_intro.validate()

    def test_new_photos_cannot_be_swapped(self):
        self._assert_swap_rejected(1, 2)

    def test_existing_photos_cannot_be_swapped(self):
        self._assert_swap_rejected(5, 6)


if __name__ == '__main__':
    unittest.main()
