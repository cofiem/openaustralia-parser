import os
import unittest

from parliaments.au_qld.hansard import Hansard
from parliaments.content.persistence import Line, Page


class HansardPersistenceTestCase(unittest.TestCase):
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

    def test_has_expected_pages(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        self.assertSetEqual(
            {f'au-qld-example-page-{i + 1}' for i in range(6)},
            {i for i in result['pages'].keys()}
        )

    def test_has_expected_lines(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        self.assertSetEqual(
            {f'au-qld-example-line-{i + 1}' for i in range(310)},
            {i for i in result['lines'].keys()}
        )

    def test_has_expected_files(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        self.assertSetEqual(
            {'au-qld-example'},
            {i for i in result['files'].keys()}
        )

    def test_empty_page(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        page_number = 4
        pdf_page_number = None
        expected = Page(
            page_id=f'au-qld-example-page-{page_number}', overall_page_number=page_number,
            pdf_page_number=pdf_page_number, file_id=list(result['files'].values())[0].file_id
        )
        self.assertEqual(expected, result['pages'][f'au-qld-example-page-{page_number}'])

    def test_sample_line_first_matches(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        expected = Line(
            line_id='au-qld-example-line-1', page_id='au-qld-example-page-1',
            raw_text="                                  ISSN 1322-0330\n",
            overall_line_number=1, page_line_number=1,
        )
        self.assertEqual(expected, result['lines']['au-qld-example-line-1'])

    def test_sample_line_last_matches(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))
        line_number = len(result['lines'])
        page_number = len(result['pages'])
        page_line_number = len(result['pages'][f'au-qld-example-page-{page_number}'].line_ids)
        expected = Line(
            line_id=f'au-qld-example-line-{line_number}', page_id=f'au-qld-example-page-{page_number}',
            raw_text="Simpson, Sorensen, Stevens, Stewart, Trad, Watts, Weir, Whiting, Wilson\n",
            overall_line_number=line_number, page_line_number=page_line_number,
        )
        self.assertEqual(expected, result['lines'][f"au-qld-example-line-{line_number}"])

    def test_sample_line_matches(self):
        result = self.hansard.run(os.path.join(self.this_file_dir, 'example.txt'))

        expected_items = [{
            'line_text': "MINISTERIAL STATEMENTS ............................................................................................................................................... 206\n",
            'line_number': 27, 'page_number': 1, 'page_line_number': 27,
        }, {
            'line_text': "                Minister for Health and Minister for Ambulance Services............................................................................... 214\n",
            'line_number': 54, 'page_number': 2, 'page_line_number': 7,
        }, {
            'line_text': "                Bonney Electorate, Schools ............................................................................................................................. 290\n",
            'line_number': 186, 'page_number': 3, 'page_line_number': 63,
        }, {
            'line_text': "\n",
            'line_number': 269, 'page_number': 5, 'page_line_number': 70,
        }, {
            'line_text': "          for the Department of Natural Resources, Mines and Energy, December 2019\n",
            'line_number': 270, 'page_number': 5, 'page_line_number': 71,
        }, {
            'line_text': "\f296  Attendance  6 Feb 2020\n",
            'line_number': 271, 'page_number': 6, 'page_line_number': 1,
        }, {
            'line_text': "\n",
            'line_number': 272, 'page_number': 6, 'page_line_number': 2,
        }, {
            'line_text': "deliver the refurbishment of three learning spaces in block E, including new floor coverings, new joinery,\n",
            'line_number': 273, 'page_number': 6, 'page_line_number': 3,
        }]

        for expected_index, expected_item in enumerate(expected_items):
            line_number = expected_item['line_number']
            page_number = expected_item['page_number']
            page_line_number = expected_item['page_line_number']
            line_text = expected_item['line_text']
            with self.subTest(i=expected_index, **expected_item):
                expected = Line(
                    line_id=f'au-qld-example-line-{line_number}', page_id=f'au-qld-example-page-{page_number}',
                    raw_text=line_text,
                    overall_line_number=line_number, page_line_number=page_line_number,
                )
                self.assertEqual(expected, result['lines'][f'au-qld-example-line-{line_number}'])


if __name__ == '__main__':
    unittest.main()
