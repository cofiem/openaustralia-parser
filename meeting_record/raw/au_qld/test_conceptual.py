import os
import unittest
from datetime import datetime
from pathlib import Path

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
        self.assertEqual('1322-0330', result.identifier)

    def test_has_expected_document_session(self):
        result = self.process.extract(self.example_data)
        self.assertEqual('First Session Of The Fifty-Sixth Parliament', result.session)

    def test_has_expected_document_date(self):
        result = self.process.extract(self.example_data)
        self.assertEqual(datetime(2020, 2, 6), result.session_date)

    def test_has_expected_page_headers(self):
        result = self.process.extract(self.example_data)
        self.assertSetEqual(
            {'au-qld-example-page-2-header', 'au-qld-example-page-3-header',
             'au-qld-example-page-5-header', 'au-qld-example-page-6-header'},
            {i.header for i in result.sections}
        )
