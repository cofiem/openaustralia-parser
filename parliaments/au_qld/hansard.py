import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from boltons.strutils import slugify

from parliaments.content.conceptual import Document, Header, Section, Paragraph, Person, Vote
from parliaments.content.persistence import Page, Line, File


class Hansard:
    """Parse and process the Queensland Parliament Hansard."""

    # TODO: add built-in pdftotext

    # The Hansard has two representations:
    # - a persistence representation - `lines` and `pages` in a `file`
    # - a conceptual representation - `paragraphs`, `sections`, `headers`, `people`, `votes` in a `document`
    # These representations need to reference each other (e.g. refer to lines in a file as a reference for a paragraph)
    # However, they only partially overlap (e.g. a paragraph can be split over more than one page)

    def run(self, input_file):
        input_path = Path(input_file)

        prefix_id = 'au-qld'

        # First read the path into a file
        hansard_file = self._read_file(prefix_id, input_path)

        # Then build the document from the file
        hansard_doc = self._parse_lines(prefix_id, hansard_file)

        return hansard_doc

    def _read_file(self, prefix_id: str, path: Path):
        current_file_id = self._build_id([prefix_id, path.stem])
        current_file = File(file_id=current_file_id, path=path)

        lines = {}
        pages = {}

        current_line = None
        current_page = None

        # NOTE: A form feed (\f) indicates the end of the current page.
        # There can be more than one form feed (\f) on a line.
        # There is one page per form feed.
        # If there is more than one form feed on a line, all but the first one is a blank page.

        overall_line_number = 1
        page_line_number = 1
        overall_page_number = 1
        with open(str(path)) as f:
            for overall_line_index, original_text in enumerate(f):

                # this type of line is unexpected
                if '\f' in original_text and not original_text.startswith('\f'):
                    raise Exception("Not expecting a line with a form feed, "
                                    "where the first form feed is not the first character.")

                # the first line of the first page
                if overall_line_number == 1:
                    # create the first page
                    current_page = self._build_page(current_file, overall_page_number, None)

                # the line represents one or more last lines on a page
                if '\f' in original_text:

                    # if there is a current page
                    if current_page:
                        # save the current page
                        current_file.page_ids.append(current_page.page_id)
                        pages[current_page.page_id] = current_page
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
                        blank_page = self._build_page(current_file, overall_page_number, None)
                        current_file.page_ids.append(blank_page.page_id)
                        pages[blank_page.page_id] = blank_page

                    # increment the overall page number
                    overall_page_number += 1

                    # reset the page line number
                    page_line_number = 1

                    # create the current page
                    current_page = self._build_page(current_file, overall_page_number)

                # save the previous line
                if current_line:
                    lines[current_line.line_id] = current_line

                # create the current line
                current_line = self._build_line(current_file, overall_line_number, page_line_number, original_text)

                # assign the page header if necessary
                if '\f' in original_text:
                    page_header = self._get_page_header(current_line)
                    pdf_page_number = page_header[1]
                    current_page.pdf_page_number = pdf_page_number

                # assign the line's page and add the line to the page
                current_line.page_id = current_page.page_id
                current_page.line_ids.append(current_line.line_id)

                # increment the overall line number
                overall_line_number += 1

                # increment the page line number
                page_line_number += 1

        return {
            'files': {current_file_id: current_file},
            'lines': lines,
            'pages': pages
        }

    def _parse_lines(self, prefix_id: str, input_data: Dict[str, Any]):
        result = {**input_data}

        input_file = list(input_data['files'].values())[0]
        pages = input_data['pages']
        lines = input_data['lines']

        documents = {}
        headers = {}
        paragraphs = {}
        persons = {}
        sections = {}
        votes = {}

        result['documents'] = documents
        result['headers'] = headers
        result['paragraphs'] = paragraphs
        result['persons'] = persons
        result['sections'] = sections
        result['votes'] = votes

        document_id = self._build_id([prefix_id, input_file.path.stem, 'document', 1])
        current_document = Document(document_id=document_id)
        documents[document_id] = current_document

        current_page_header: Optional[Header] = None
        current_header: Optional[Header] = None

        previous_line: Optional[Line] = None
        next_line: Optional[Line] = None

        current_page: Optional[Page] = None
        current_paragraph: Optional[Paragraph] = None
        current_person: Optional[Person] = None
        current_section: Optional[Section] = None
        current_vote: Optional[Vote] = None

        current_year = datetime.strftime(datetime.now(), '%Y')

        paragraph_indent = 8

        is_preface_title_section = True
        is_preface_toc_section = False
        is_main_document = False

        preface_title_section = Section(
            section_id=self._build_id([document_id, 'preface', 'title', 'section']), document_id=document_id)
        sections[preface_title_section.section_id] = preface_title_section

        preface_title_para = Paragraph(
            paragraph_id=self._build_id([document_id, 'preface', 'title', 'paragraph']),
            section_id=preface_title_section.section_id)
        paragraphs[preface_title_para.paragraph_id] = preface_title_para
        preface_title_section.paragraph_ids.append(preface_title_para.paragraph_id)

        preface_toc_section = Section(
            section_id=self._build_id([document_id, 'preface', 'toc', 'section']), document_id=document_id)
        sections[preface_toc_section.section_id] = preface_toc_section
        preface_toc_para = Paragraph(
            paragraph_id=self._build_id([document_id, 'preface', 'toc', 'paragraph']),
            section_id=preface_toc_section.section_id)
        paragraphs[preface_toc_para.paragraph_id] = preface_toc_para
        preface_toc_section.paragraph_ids.append(preface_toc_para.paragraph_id)

        for current_line_id, current_line in lines.items():

            # line facts
            line_norm = current_line.normalised()
            line_norm_no_ws = current_line.normalised_no_whitespace()
            line_split_words = current_line.split_words()
            line_is_empty = current_line.is_empty()
            line_is_page_start = current_line.is_page_first_line()

            previous_line_id = current_line.previous_line_id()
            previous_line = lines[previous_line_id] if previous_line_id and previous_line_id in lines else None
            next_line_id = current_line.next_line_id()
            next_line = lines[next_line_id] if next_line_id and next_line_id in lines else None
            current_page = pages[current_line.page_id]

            # change to the preface toc
            if line_split_words == ['Subject', 'Page']:
                is_preface_title_section = False
                is_preface_toc_section = True
                is_main_document = False

            # end of the toc
            if previous_line and 'ATTENDANCE ...' in previous_line.raw_text:
                is_preface_title_section = False
                is_preface_toc_section = False
                is_main_document = True

            # parse the ISSN
            if is_preface_title_section and line_norm_no_ws.startswith('ISSN ') and current_document.international_standard_serial_number is None:
                current_document.international_standard_serial_number = line_norm_no_ws.replace('ISSN ', '')

            # parse the parliament session
            if is_preface_title_section and 'SESSION' in line_norm_no_ws and 'PARLIAMENT' in line_norm_no_ws and current_document.session is None:
                current_document.session = line_norm_no_ws.title()

            # parse the parliament sitting date
            if is_preface_title_section and line_norm_no_ws.endswith(current_year) and current_document.document_date is None:
                current_document.document_date = datetime.strptime(line_norm_no_ws, '%A, %d %B %Y')

            # add the line to the paragraph if is_preface_title_section
            if is_preface_title_section:
                preface_title_para.line_ids.append(current_line.line_id)

            # add the line to the paragraph if is_preface_toc_section
            if is_preface_toc_section:
                preface_toc_para.line_ids.append(current_line.line_id)

            # begin the page header
            if line_is_page_start and current_line.overall_line_number > 1:
                current_page_header = Header(
                    page_id=current_page.page_id, section_id=None, line_ids=[current_line],
                    header_id=self._build_id([current_page.page_id, 'header']))

            # continue the page header
            if current_page_header is not None and current_page.header_id is None and not line_is_empty and not line_is_page_start:
                current_page_header.line_ids.append(current_line.line_id)

            # finish the page header
            if current_page_header is not None and current_page.header_id is None and line_is_empty and not line_is_page_start:
                current_page.header_id = current_page_header.header_id
                headers[current_page_header.header_id] = current_page_header
                current_page_header = None

            # TODO
            if not line_is_page_start and not current_page_header and is_main_document:
                # section
                if not current_line.is_empty() and previous_line and previous_line.is_empty() and next_line and next_line.is_empty():
                    a = 1


                # paragraph

                # begin a paragraph
                if (previous_line and previous_line.is_empty() and not line_norm.startswith(' ')) or current_line.has_indent(paragraph_indent, ' '):
                    current_paragraph = Paragraph(
                        paragraph_id=self._build_id([document_id, 'paragraph', current_line.overall_line_number]),
                    )

                # continue a paragraph
                if not line_is_empty and not line_norm.startswith(' '):
                    a = 1

                # finish a paragraph
                if line_is_empty:
                    a = 1

        return result

    def _build_id(self, parts: List[str]) -> str:
        parts_norm = [str(i).replace('_', '-').replace('.', '-') for i in parts]
        return slugify('-'.join(parts_norm), delim='-', ascii=True).decode('utf-8')

    def _build_line(self, file: File, overall_line_number: int, page_line_number: int, raw_text: str):
        line_id = self._build_id([file.file_id, 'line', overall_line_number])
        return Line(line_id=line_id, raw_text=raw_text, overall_line_number=overall_line_number,
                    page_line_number=page_line_number)

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

    def _build_page(self, file: File, overall_page_number: int, pdf_page_number: Optional[int] = None):
        page_id = self._build_id([file.file_id, 'page', overall_page_number])
        return Page(page_id=page_id, overall_page_number=overall_page_number,
                    pdf_page_number=pdf_page_number, file_id=file.file_id)

    def _build_header_page(self, page: Page, lines: List[Line]):
        header_id = self._build_id([page.page_id, 'header'])
        header = Header(header_id=header_id, line_ids=[i.line_id for i in lines],
                        page_id=page.page_id, section_id=None)
        page.page_header_id = header_id
        return header

    def _build_header_section(self, section: Section, lines: List[Line]):
        header_id = self._build_id([section.section_id, 'header'])
        header = Header(header_id=header_id, line_ids=[i.line_id for i in lines],
                        section_id=section.section_id, page_id=None)
        section.header_id = header_id
        return header
