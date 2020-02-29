import re
from pathlib import Path
from typing import Optional, Tuple, Type

from meeting_record.model import File, Document, Page, Line, Section, Base, Preface, \
    TableOfContents, Header, Paragraph, Attendance, Vote


class Process(Base):
    """Extract information from the Queensland Parliament Hansard / Record of Proceedings files."""

    paragraph_indents = [8, 10]
    header_indent = 17

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
        result: Document = Document()
        current_item: Optional[Base] = result

        block_dispatch = {
            self._get_class_name(Attendance): self._process_attendance,
            self._get_class_name(Document): self._process_document,
            self._get_class_name(Header): self._process_header,
            self._get_class_name(Paragraph): self._process_paragraph,
            self._get_class_name(Preface): self._process_preface,
            self._get_class_name(Section): self._process_section,
            self._get_class_name(TableOfContents): self._process_toc,
            self._get_class_name(Vote): self._process_vote,
        }

        # Note: lines that are empty will not be included in some data classes, e.g. document, section, paragraph

        for current_page in file_data.pages:
            for current_line in current_page.body_lines:

                # while the new block type does not equal the previous block type, try processing the line again
                # The current_item is the parent of the current block.
                # The block_type is the type of block that needs to be processed
                while True:
                    key = self._get_instance_name(current_item)
                    new_item = block_dispatch[key](current_page, current_line, current_item)

                    if self._get_instance_name(new_item) == self._get_instance_name(current_item):
                        break
                    else:
                        current_item = new_item

        # TODO: also use the toc to identify headers (particularly headers over more than one line)

        return result

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

    def _process_attendance(self, page: Page, line: Line, item: Attendance) -> Base:
        self._assert_type(Attendance, item)

        # TODO: parse people present

        if not line.is_empty():
            item.lines.append(line)
            return item

        return item

    def _process_document(self, page: Page, line: Line, item: Document) -> Base:
        self._assert_type(Document, item)

        if item.preface is None:
            item.preface = Preface(document=item)
            return item.preface

        if item.toc is None:
            item.toc = TableOfContents(document=item)
            return item.toc

        if not line.is_empty():
            section = Section(document=item)
            return section

        return item

    def _process_header(self, page: Page, line: Line, item: Header) -> Base:
        self._assert_type(Header, item)

        if line.has_readable_text():
            item.lines.append(line)
            return item

        if line.is_empty():
            # go back up to the parent section
            return item.section

        return item

    def _process_paragraph(self, page: Page, line: Line, item: Paragraph) -> Base:
        self._assert_type(Paragraph, item)

        # TODO: parse person and time

        # start a paragraph or continue the current paragraph
        if self._is_paragraph_start(line) or self._is_paragraph_continuation(line):
            item.lines.append(line)
            return item

        if self.is_vote_start(line):
            return item.section

        if line.is_empty():
            # go back up to the parent section
            return item.section

        return item

    def _process_preface(self, page: Page, line: Line, item: Preface) -> Base:
        self._assert_type(Preface, item)

        line_no_ws = line.normalised_no_whitespace().casefold()
        line_split_words = [i.casefold() for i in line.split_words()]

        # change to the preface toc (current line is first line of toc)
        text_toc_header = [i.casefold() for i in ['Subject', 'Page']]
        if line_split_words == text_toc_header:
            return item.document

        # add the line to the preface
        item.lines.append(line)

        # parse the ISSN
        text_issn = 'ISSN '.casefold()
        if item.identifier is None and line_no_ws and line_no_ws.startswith(text_issn):
            item.identifier = line_no_ws.replace(text_issn, '')
            return item

        # parse the parliament session
        text_session = [i.casefold() for i in ['SESSION', 'PARLIAMENT']]
        if item.session is None and line_no_ws and all(i in line_no_ws for i in text_session):
            item.session = line_no_ws.title()
            return item

        # parse the parliament sitting date
        if item.session_date is None and line_no_ws:
            item.session_date = self._get_datetime(line_no_ws)
            return item

        if line.is_empty():
            return item

        return item

    def _process_section(self, page: Page, line: Line, item: Section) -> Base:
        self._assert_type(Section, item)

        # change to the top-level header and ensure there is a section in the document
        # this will also change to the next section each time a header 1 is found
        if self._is_header_1(line):
            section = Section(document=item.document)
            item.document.sections.append(section)
            section.header = Header(section=section)
            return section.header

        # a level 2 header
        # a section header line, level 2
        if self._is_header_2(line):
            section = Section(document=item.document, section=item)
            item.sections.append(section)
            section.header = Header(section=section)
            return section.header

        # start or continue attendance
        if item.is_attendance() and not line.is_empty():
            attendance = Attendance(section=item)
            item.attendance = attendance
            return attendance

        # start a vote
        if self.is_vote_start(line):
            vote = Vote(section=item)
            item.votes.append(vote)
            return vote

        # start a paragraph
        if self._is_paragraph_start(line):
            paragraph = Paragraph(section=item)
            item.paragraphs.append(paragraph)
            return paragraph

        # continue a paragraph
        if self._is_paragraph_continuation(line):
            paragraph = item.paragraphs[-1]
            return paragraph

        if line.is_empty():
            return item

        return item

    def _process_toc(self, page: Page, line: Line, item: TableOfContents) -> Base:
        self._assert_type(TableOfContents, item)

        # change to the main part (current line is the first line of the main part)
        if page.header_number is not None and line.is_page_first_line():
            return item.document

        # add the line to the toc
        item.lines.append(line)

        return item

    def _process_vote(self, page: Page, line: Line, item: Vote) -> Base:
        self._assert_type(Vote, item)

        line_empty = line.is_empty()
        vote_start = self.is_vote_start(line) or item.question_lines
        vote_yes = self._is_vote_yes(line) or item.yes_lines
        vote_no = self._is_vote_no(line) or item.no_lines
        vote_pair = self._is_vote_pair(line) or item.pair_lines
        vote_resolution = self._is_vote_resolution(line) or item.resolution_lines
        vote_outcome = self._is_vote_outcome(line) or item.outcome_lines

        if vote_start and not vote_yes and not line_empty:
            item.question_lines.append(line)
            return item

        if vote_yes and vote_start and not vote_no and not line_empty:
            item.yes_lines.append(line)
            return item

        if vote_no and vote_yes and not vote_pair and not line_empty:
            item.no_lines.append(line)
            return item

        if vote_pair and vote_no and not vote_resolution and not line_empty:
            item.pair_lines.append(line)
            return item

        if vote_resolution and vote_no and not vote_outcome and not line_empty:
            item.resolution_lines.append(line)
            return item

        if vote_outcome and vote_resolution and not line_empty:
            item.outcome_lines.append(line)
            return item

        if line_empty and vote_outcome:
            return item.section

        return item

    def _is_paragraph_start(self, line: Line):
        return line.has_readable_text() and \
               (line.has_indent(self.paragraph_indents) or not line.normalised().startswith(' ')) and \
               (not line.contains('Division: Question put—'))

    def _is_paragraph_continuation(self, line: Line):
        return line.has_readable_text() and not line.normalised().startswith(' ') and \
               (not line.contains('Division: Question put—'))

    def _is_header_1(self, line: Line):
        return line.has_readable_text() and line.normalised_no_whitespace().isupper()

    def _is_header_2(self, line: Line):
        return line.has_readable_text() and not line.normalised_no_whitespace().isupper() \
               and not line.has_indent(self.paragraph_indents) \
               and line.normalised().startswith(' ')

    def is_vote_start(self, line: Line) -> bool:
        return line.has_readable_text() and line.contains('Division: Question put—') and \
               line.has_indent(self.paragraph_indents)

    def _is_vote_yes(self, line: Line) -> bool:
        line_no_ws = line.normalised_no_whitespace()
        return line_no_ws.startswith('AYES, ') and line_no_ws.endswith(':')

    def _is_vote_no(self, line: Line) -> bool:
        line_no_ws = line.normalised_no_whitespace()
        return line_no_ws.startswith('NOES, ') and line_no_ws.endswith(':')

    def _is_vote_pair(self, line: Line) -> bool:
        line_no_ws = line.normalised_no_whitespace()
        return line_no_ws.startswith('Pair: ')

    def _is_vote_resolution(self, line: Line) -> bool:
        return line.contains_word('affirmative') or line.contains_word('negatived')

    def _is_vote_outcome(self, line: Line) -> bool:
        return line.contains('agreed to')

    def _assert_type(self, expected_type: Type[Base], item):
        if not isinstance(item, expected_type):
            raise ValueError(
                f"Expected a '{self._get_class_name(expected_type)}', got a '{self._get_instance_name(item)}'.")

    def _get_class_name(self, value: Type[Base]) -> str:
        return value.__name__

    def _get_instance_name(self, value: Base) -> str:
        return value.__class__.__name__
