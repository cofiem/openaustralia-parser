import json
import os
import unittest
from datetime import datetime
from pathlib import Path
from typing import List, Any, Generator

from meeting_record.model import Section
from meeting_record.raw.au_qld.process import Process


class HansardConceptualTestCase(unittest.TestCase):
    process: Process = None
    this_file_dir: str = None
    example_path: Path = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.process = Process()
        cls.this_file_dir = os.path.dirname(__file__)
        cls.example_path = Path(os.path.join(cls.this_file_dir, 'example.txt'))
        cls.example_data = cls.process.read(cls.example_path)

    def test_has_expected_document_identifier(self):
        result = self.process.extract(self.example_data)
        self.assertEqual('1322-0330', result.preface.identifier)

    def test_has_expected_document_session(self):
        result = self.process.extract(self.example_data)
        self.assertEqual('First Session Of The Fifty-Sixth Parliament', result.preface.session)

    def test_has_expected_document_date(self):
        result = self.process.extract(self.example_data)
        self.assertEqual(datetime(2020, 2, 6), result.preface.session_date)

    def test_has_expected_structure(self):
        result = self.process.extract(self.example_data)
        expected = [
            {
                'header': [202],
                'paragraphs': [206, 207, 208, 209, 210, 211, 212],
            },
            {
                'header': [214],
                'sections': [{
                    'header': [216],
                    'paragraphs': [218, 219, 220, 222, 223]
                }]
            },
            {
                'header': [225],
                'sections': [{
                    'header': [227],
                    'paragraphs': [229, 230, 231, 232, 233, 234,
                                   236, 237, 238, 239, 240,
                                   242, 243, 244, 245, 246],
                }]
            },
            {
                'header': [248],
                'paragraphs': [250],
                'sections': [{
                    'header': [252],
                    'paragraphs': [254, 255, 257],
                }]
            },
            {
                'header': [259],
            },
            {
                'header': [261],
            },
            {
                'header': [263],
                'paragraphs': [265, 267, 268, 270,
                               274, 275, 276,
                               278, 279, 280, 281, 282, 283, 284,
                               285, 286, 287, 288, 289, 290],
                'votes': [{
                    'question': [291],
                    'yes': [293, 295, 297, 298, 299, 301, 302],
                    'no': [304, 306, 308, 309, 311, 312, 313],
                    'pair': [315],
                    'resolution': [317],
                    'outcome': [318]
                }]
            },
            {
                'header': [230],
                'paragraphs': [322, 324, 326, 327],
            },
            {
                'header': [329, 330],
                'paragraphs': [332],
                'sections': [{
                    'header': [334],
                    'paragraphs': [336, 337,
                                   339,
                                   341, 342, 343,
                                   346, 347, 348,
                                   350, 351, 352, 353, 354, 355, 356, 357, 358, 359,
                                   361, 362, 363, 364, 365, 366, 367, 368, 369, 370,
                                   372],
                }]
            },
            {
                'header': [329, 330],
                'paragraphs': [332],
                'sections': [{
                    'header': [334],
                    'paragraphs': [336, 339, 341, 346, 350, 361, 372],
                }]
            },
            {
                'header': [374],
                'attendance': [376, 377, 378, 379, 380, 381, 382, 383]
            },
        ]
        # test = str(result)
        self.assertEqual(
            json.dumps(expected, sort_keys=True, indent=1),
            json.dumps(result.structure(), sort_keys=True, indent=1))
        # self.assertEqual(DeepDiff(expected, result.structure()), {})

    def _get_sections(self, sections: List[Section]) -> Generator[int, Any, None]:
        for section in sections:
            if section.header and section.header.lines:
                for line in section.header.lines:
                    yield line.overall_line_number
                self._get_sections(section.sections)
