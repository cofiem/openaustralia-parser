import re
from pathlib import Path
from typing import Optional, Tuple

from meeting_record.model import File, Document, Page, Line, Section, Paragraph, Base


class Process(Base):
    """Extract information from the Queensland Parliament Hansard / Record of Proceedings files."""

    def run(self, input_file: str):
        input_path = Path(input_file)

        # First read the path into a file
        file_data = self.read(input_path)

        # Then build the document from the file
        doc_data = self.extract(file_data)

        return doc_data

    def read(self, path: Path) -> File:
        current_file = File(path=path)

        current_line: Optional['Line'] = None
        current_page: Optional['Page'] = None

        # NOTE: A form feed (\f) indicates the end of the current page.
        # There can be more than one form feed (\f) on a line.
        # There is one page per form feed.
        # If there is more than one form feed on a line, all but the first one is a blank page.

        overall_line_number = 1
        page_line_number = 1
        overall_page_number = 1
        is_page_header = False
        with open(str(path), encoding='utf8') as f:
            for overall_line_index, original_text in enumerate(f):

                # this type of line is unexpected
                if '\f' in original_text and not original_text.startswith('\f'):
                    raise Exception("Not expecting a line with a form feed, "
                                    "where the first form feed is not the first character.")

                # the first line of the first page
                if overall_line_number == 1:
                    # create the first page
                    current_page = self._build_page(overall_page_number)

                # the line represents one or more last lines on a page
                if '\f' in original_text:

                    # if there is a current page
                    if current_page:
                        # save the current page
                        current_file.pages.append(current_page)
                        current_page = None

                    # get each page represented by the line
                    page_items = original_text.split('\f')

                    # the last page does not have any pages after it
                    if len(page_items) == 2 and page_items[0] == '' and page_items[1] == '':
                        # a line with only a form feed is not a real line, just a marker for the end of a page
                        continue

                    # create the blank pages
                    # the first item is the indicator of the end of the current page, skip it
                    # the last item is the first line of the next non-blank page, skip it
                    blank_pages = page_items[1:-1]

                    # this type of line is unexpected
                    if any([i != '' for i in blank_pages]):
                        raise Exception("Not expecting a line with more than one form feed "
                                        "to have content between the form feeds.")

                    for _ in blank_pages:
                        # for each starting line for a page

                        # increment the overall page number
                        overall_page_number += 1

                        # add any additional blank page(s)
                        blank_page = self._build_page(overall_page_number)
                        current_file.pages.append(blank_page)

                    # increment the overall page number
                    overall_page_number += 1

                    # reset the page line number
                    page_line_number = None

                    # create the current page
                    current_page = self._build_page(overall_page_number)

                    # the first line of a page with content should not be included in the body lines
                    is_page_header = True

                # create the current line
                current_line = self._build_line(overall_line_number, page_line_number, original_text)
                current_line.page_number = current_page.overall_number

                if is_page_header:
                    # add the line to the page
                    current_page.header_lines.append(current_line)

                    # assign the page header
                    if '\f' in original_text:
                        page_header = self._get_page_header(current_line)
                        current_page.header_title = page_header[0]
                        current_page.header_number = int(page_header[1]) if page_header[1] else None
                    elif original_text != '\n':
                        current_page.header_title += f' {original_text.strip()}'
                    elif original_text == '\n':
                        is_page_header = False
                        page_line_number = 1
                else:
                    # add the line to the page
                    current_page.body_lines.append(current_line)

                    # increment the page line number
                    page_line_number += 1

                # increment the overall line number
                overall_line_number += 1

        return current_file

    def extract(self, file_data: File) -> Document:
        current_document: Document = Document()

        paragraph_indent = 8
        header_indent = 17  # TODO: also use the toc to identifier header (particularly headers over more than one line)
        position_marker = 'preface'
        gather_lines = []

        current_section: Optional[Section] = None

        for current_page in file_data.pages:
            current_body_lines = current_page.body_lines
            current_body_numbers = [i.overall_line_number for i in current_body_lines]
            current_body_line_count = len(current_body_lines)
            has_current_page_header_number = current_page.header_number is not None
            for current_body_line in current_body_lines:

                # --- calculate line facts ---

                line_norm = current_body_line.normalised()
                line_norm_no_ws = current_body_line.normalised_no_whitespace()
                line_split_words = current_body_line.split_words()
                line_is_empty = current_body_line.is_empty()
                line_is_page_start = current_body_line.is_page_first_line()

                # --- activities that extract info from a line but want to group the line ---

                # parse the ISSN
                if current_document.identifier is None and line_norm_no_ws and line_norm_no_ws.startswith('ISSN '):
                    current_document.identifier = line_norm_no_ws.replace('ISSN ', '')

                # parse the parliament session
                if current_document.session is None and line_norm_no_ws and \
                        all(i in line_norm_no_ws for i in ['SESSION', 'PARLIAMENT']):
                    current_document.session = line_norm_no_ws.title()

                # parse the parliament sitting date
                if current_document.session_date is None and line_norm_no_ws:
                    current_document.session_date = self._get_datetime(line_norm_no_ws)

                # --- activities that group lines ---

                # change to the preface toc (current line is first line of toc)
                if position_marker == 'preface' and line_split_words == ['Subject', 'Page']:
                    current_document.sections.append(Section(paragraphs=[Paragraph(lines=gather_lines)]))
                    position_marker = 'toc'
                    gather_lines = []

                # change to the main part (current line is the first line of the main part)
                if position_marker == 'toc' and has_current_page_header_number and line_is_page_start and \
                        self._get_datetime(line_norm_no_ws) is not None:
                    current_document.sections.append(Section(paragraphs=[Paragraph(lines=gather_lines)]))
                    position_marker = 'main'
                    gather_lines = []

                # start a new section
                if position_marker == 'main' and \
                        current_body_line.has_readable_text() and \
                        current_body_line.has_indent_at_least(header_indent):
                    if current_section:
                        current_document.sections.append(current_section)
                    current_section = Section()

                # end the current group
                if position_marker == 'main' and current_body_line.raw_text == '\n':
                    a = 1

                # add current line to gathering
                gather_lines.append(current_body_line)

        return current_document

    def _build_page(self, overall_number: int):
        return Page(overall_number=overall_number)

    def _build_line(self, overall_line_number: int, page_line_number: int, raw_text: str) -> 'Line':
        return Line(raw_text=raw_text, overall_line_number=overall_line_number, page_line_number=page_line_number)

    def _get_page_header(self, line: Line) -> Tuple[str, Optional[int]]:
        line_norm_no_ws = line.normalised_no_whitespace()

        matcher_right = re.compile(r'^(.+?) {2,}(.+?) {2,}([^ ]+)$')
        matches_right = matcher_right.findall(line_norm_no_ws)
        if matches_right:
            return matches_right[0][1], matches_right[0][2]

        matcher_left = re.compile(r'^([^ ]+) {2,}(.+?) {2,}(.+?)$')
        matches_left = matcher_left.findall(line_norm_no_ws)
        if matches_left:
            return matches_left[0][1], matches_left[0][0]

        return line_norm_no_ws, None
