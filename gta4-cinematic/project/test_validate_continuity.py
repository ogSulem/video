"""Regression tests for the video/audio continuity audit, without rendering."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

import validate_continuity as audit


class ContinuityTests(unittest.TestCase):
    FPS = 24
    FRAMES = 120
    SR = 16000
    OFFSET = 1.34
    VIDEO = Path('finished.mp4')
    MUSIC = Path('music.m4a')

    def setUp(self):
        rng = np.random.default_rng(45)
        self.source = rng.normal(0, .1, (int((self.OFFSET+6)*self.SR), 2))
        first = round(self.OFFSET*self.SR)
        self.output = self.source[first:first+5*self.SR].copy() * (10 ** (-5/20))
        self.lines = [f'n: {n} pts: {n*512} pts_time:{n/self.FPS:.6f} checksum:{n:08X}'
                      for n in range(self.FRAMES)]

    def scan(self):
        result = SimpleNamespace(stderr=('\n'.join(self.lines)).encode(), stdout=b'')
        def stereo(_ff, path, _seconds, _sr):
            return self.source if path == self.MUSIC else self.output
        with patch.object(audit, '_run', return_value=result), \
                patch.object(audit, '_stereo', side_effect=stereo), redirect_stdout(StringIO()):
            audit.verify_continuity(self.VIDEO, self.MUSIC, 'ffmpeg', self.FPS,
                                    self.FRAMES, self.OFFSET)

    def test_valid_stream(self):
        self.scan()

    def test_missing_frame_is_rejected(self):
        self.lines.pop(10)
        with self.assertRaisesRegex(ValueError, 'expected 120'):
            self.scan()

    def test_wrong_timestamp_is_rejected(self):
        self.lines[20] = self.lines[20].replace('pts_time:0.833333', 'pts_time:0.930000')
        with self.assertRaisesRegex(ValueError, 'frame timestamp'):
            self.scan()

    def test_repeated_picture_is_rejected(self):
        self.lines[20] = self.lines[20].replace('checksum:00000014', 'checksum:00000013')
        with self.assertRaisesRegex(ValueError, 'repeated frames'):
            self.scan()

    def test_black_gap_is_rejected(self):
        self.lines.append('black_start:2 black_end:2.4 black_duration:0.4')
        with self.assertRaisesRegex(ValueError, 'black interval'):
            self.scan()

    def test_silenced_channel_is_rejected(self):
        self.output[self.SR:2*self.SR, 1] = 0
        with self.assertRaisesRegex(ValueError, 'Audio mismatch.*channel 1'):
            self.scan()


if __name__ == '__main__':
    unittest.main()
