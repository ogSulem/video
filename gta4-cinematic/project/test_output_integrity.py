"""Ensure the QC reports identify the exact MP4s in the repository."""
from hashlib import file_digest
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = (
    (ROOT / 'project' / 'QC_REPORT.md', ROOT / 'output' / 'spartak_intro.mp4'),
    (ROOT / 'dubravnaya' / 'project' / 'QC_REPORT.md',
     ROOT / 'dubravnaya' / 'output' / 'dubravnaya_intro.mp4'),
)


class ExportIntegrityTests(unittest.TestCase):
    def test_reported_sha256_matches_each_export(self):
        for report, video in EXPORTS:
            with self.subTest(video=video.name):
                matches = re.findall(r'^SHA-256:\s*`([a-f0-9]{64})`\s*$',
                                     report.read_text(encoding='utf-8'), re.MULTILINE)
                self.assertEqual(len(matches), 1, f'Expected one SHA-256 in {report}')
                with video.open('rb') as stream:
                    actual = file_digest(stream, 'sha256').hexdigest()
                self.assertEqual(matches[0], actual,
                                 f'{report} does not describe the current {video.name}')


if __name__ == '__main__':
    unittest.main()
