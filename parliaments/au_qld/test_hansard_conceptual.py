import os
import unittest

from parliaments.au_qld.hansard import Hansard


class HansardConceptualTestCase(unittest.TestCase):
    hansard: Hansard = None
    this_file_dir: str = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.hansard = Hansard()
        cls.this_file_dir = os.path.dirname(__file__)

    def test_fails_when_file_does_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            self.hansard.run(os.path.join(self.this_file_dir, 'does_not_exist.txt'))

    def test_passes_when_file_does_exist(self):
        self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))

    def test_has_expected_documents(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        self.assertSetEqual(
            {'au-qld-example-document-1'},
            {i for i in result['documents'].keys()}
        )

    def test_has_expected_document_issn(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        self.assertEqual(
            '1322-0330',
            result['documents']['au-qld-example-document-1'].international_standard_serial_number
        )

    def test_has_expected_document_session(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        self.assertEqual(
            'First Session Of The Fifty-Sixth Parliament',
            result['documents']['au-qld-example-document-1'].session)

    def test_has_expected_page_headers(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        self.assertSetEqual(
            {'au-qld-example-page-2-header', 'au-qld-example-page-3-header',
             'au-qld-example-page-5-header', 'au-qld-example-page-6-header'},
            {i for i in result['headers'].keys()}
        )


if __name__ == '__main__':
    unittest.main()
