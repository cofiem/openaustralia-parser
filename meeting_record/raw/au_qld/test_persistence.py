import os
import unittest
from pathlib import Path

from meeting_record.model import Page, Line
from meeting_record.raw.au_qld.process import Process


class HansardPersistenceTestCase(unittest.TestCase):
    process: Process = None
    this_file_dir: str = None
    example_path: Path = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.process = Process()
        cls.this_file_dir = os.path.dirname(__file__)
        cls.example_path = Path(os.path.join(cls.this_file_dir, 'example.txt'))

    def test_fails_when_file_does_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            self.process.read(Path(os.path.join(self.this_file_dir, 'does_not_exist.txt')))

    def test_passes_when_file_does_exist(self):
        self.process.read(self.example_path)

    def test_has_expected_pages(self):
        result = self.process.read(self.example_path)
        self.assertListEqual(
            [i for i in range(1, 7 + 1)],
            [page.overall_number for page in result.pages]
        )

    def test_has_expected_lines(self):
        result = self.process.read(self.example_path)
        self.assertListEqual(
            sorted([i for i in range(1, 383 + 1)]),
            sorted(
                [line.overall_line_number for p in result.pages for line in p.body_lines] +
                [line.overall_line_number for p in result.pages for line in p.header_lines] +
                [line.overall_line_number for p in result.pages for line in p.footer_lines]
            )
        )

    def test_has_expected_files(self):
        result = self.process.read(self.example_path)
        self.assertEqual(self.example_path, result.path)

    def test_empty_page(self):
        result = self.process.read(self.example_path)
        page_number = 4
        expected = Page(overall_number=page_number)
        self.assertEqual(expected, result.pages[page_number - 1])

    def test_sample_line_matches(self):
        result = self.process.read(self.example_path)

        expected_items = [{
            'line_text': "                                  ISSN 1322-0330\n",
            'line_number': 1, 'page_number': 1, 'page_line_number': 1,
        }, {
            'line_text': "MINISTERIAL STATEMENTS ............................................................................................................................................... 206\n",
            'line_number': 27, 'page_number': 1, 'page_line_number': 27,
        }, {
            'line_text': "                Minister for Health and Minister for Ambulance Services............................................................................... 214\n",
            'line_number': 54, 'page_number': 2, 'page_line_number': 5,
        }, {
            'line_text': "                Bonney Electorate, Schools ............................................................................................................................. 290\n",
            'line_number': 186, 'page_number': 3, 'page_line_number': 61,
        }, {
            'line_text': "\n",
            'line_number': 269, 'page_number': 5, 'page_line_number': 68,
        }, {
            'line_text': "          for the Department of Natural Resources, Mines and Energy, December 2019\n",
            'line_number': 270, 'page_number': 5, 'page_line_number': 69,
        }, {
            'line_text': "        Division: Question put—That the motion be agreed to.\n",
            'line_number': 291, 'page_number': 6, 'page_line_number': 18,
        }, {
            'line_text': "\f296  Attendance  6 Feb 2020\n",
            'line_number': 344, 'page_number': 7, 'page_line_number': None,
        }, {
            'line_text': "\n",
            'line_number': 345, 'page_number': 7, 'page_line_number': None,
        }, {
            'line_text': "deliver the refurbishment of three learning spaces in block E, including new floor coverings, new joinery,\n",
            'line_number': 346, 'page_number': 7, 'page_line_number': 1,
        }, {
            'line_text': "new layout to cater for equitable access, replacement hoists, modification of windows and ceiling and\n",
            'line_number': 347, 'page_number': 7, 'page_line_number': 2,
        }, {
            'line_text': "Simpson, Sorensen, Stevens, Stewart, Trad, Watts, Weir, Whiting, Wilson\n",
            'line_number': 383, 'page_number': 7, 'page_line_number': 38,
        }]

        for expected_index, expected_item in enumerate(expected_items):
            expected_line_number = expected_item['line_number']
            expected_page_number = expected_item['page_number']
            expected_page_line_number = expected_item['page_line_number']
            expected_line_text = expected_item['line_text']
            with self.subTest(i=expected_index, **expected_item):
                actual_page = result.pages[expected_page_number - 1]
                actual_body_line = next(
                    (line for line in actual_page.body_lines if line.overall_line_number == expected_line_number), None)
                actual_header_line = next(
                    (line for line in actual_page.header_lines if line.overall_line_number == expected_line_number),
                    None)
                actual_footer_line = next(
                    (line for line in actual_page.footer_lines if line.overall_line_number == expected_line_number),
                    None)
                actual_line = actual_body_line or actual_header_line or actual_footer_line
                expected_line = Line(
                    raw_text=expected_line_text, overall_line_number=expected_line_number,
                    page_line_number=expected_page_line_number, page_number=expected_page_number)
                self.assertEqual(expected_page_number, actual_page.overall_number)
                self.assertEqual(expected_line, actual_line)

    def test_pages_have_expected_lines(self):
        result = self.process.read(self.example_path)
        expected = {
            1: {'body': (1, 47), 'header': None, 'title': None, 'header_number': None},
            2: {'body': (50, 123), 'header': (48, 49), 'title': 'Table of Contents – Thursday, 6 February 2020',
                'header_number': None},
            3: {'body': (126, 199), 'header': (124, 125), 'title': 'Table of Contents – Thursday, 6 February 2020',
                'header_number': None},
            4: {'body': None, 'header': None, 'title': None, 'header_number': None},
            5: {'body': (202, 270), 'header': (200, 201), 'title': 'Legislative Assembly', 'header_number': 205},
            6: {'body': (274, 343), 'header': (271, 273),
                'title': 'Public Health (Declared Public Health Emergencies) Amendment Bill', 'header_number': 228},
            7: {'body': (346, 383), 'header': (344, 345), 'title': 'Attendance', 'header_number': 296},
        }
        for page_number, page_details in expected.items():
            body_lines = page_details['body']
            header_lines = page_details['header']
            page_title = page_details['title']
            header_number = page_details['header_number']

            page = next((page for page in result.pages if page.overall_number == page_number), None)

            with self.subTest(page_number=page_number, page_title=page_title):
                self.assertIsNotNone(page)

                if body_lines:
                    body_lines_range = range(body_lines[0], body_lines[1] + 1)
                    self.assertEqual(len(body_lines_range), len(page.body_lines))
                    for line_number in body_lines_range:
                        with self.subTest('body', page_number=page_number, line_number=line_number):
                            body_line_index = line_number - (body_lines[0] - 1) - 1
                            self.assertEqual(line_number, page.body_lines[body_line_index].overall_line_number)
                else:
                    self.assertEqual([], page.body_lines)

                if header_lines:
                    header_lines_range = range(header_lines[0], header_lines[1] + 1)
                    self.assertEqual(len(header_lines_range), len(page.header_lines))
                    for line_number in header_lines_range:
                        with self.subTest('header', page_number=page_number, line_number=line_number):
                            header_line_index = line_number - (header_lines[0] - 1) - 1
                            self.assertEqual(line_number, page.header_lines[header_line_index].overall_line_number)
                else:
                    self.assertEqual([], page.header_lines)

                self.assertEqual([], page.footer_lines)

                self.assertEqual(page_title, page.header_title)
                self.assertEqual(header_number, page.header_number)
