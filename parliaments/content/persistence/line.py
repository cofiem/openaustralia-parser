from dataclasses import dataclass
from typing import List


@dataclass
class Line:
    """A line in a page, part of a paragraph or header."""

    line_id: str

    # the raw line content
    raw_text: str

    # line number in the pdftotext text file (from 1)
    overall_line_number: int

    # line number in the page (from 1)
    page_line_number: int

    # the page that contains this line
    page_id: str = None

    # the paragraph that contains this line
    paragraph_id: str = None

    # the paragraph that contains this line
    header_id: str = None

    def normalised(self) -> str:
        return self.raw_text.strip('\f\n\t') if self.raw_text else ''

    def normalised_no_whitespace(self) -> str:
        norm = self.normalised()
        return norm.strip() if norm else ''

    def split_words(self) -> List[str]:
        norm_no_ws = self.normalised_no_whitespace()
        return [i for i in norm_no_ws.split(' ') if i] if norm_no_ws else []

    def is_page_first_line(self):
        return self.page_line_number == 1

    def is_file_first_line(self):
        return self.overall_line_number == 1

    def is_empty(self) -> bool:
        return self.normalised_no_whitespace() == ''

    def previous_line_id(self):
        if self.is_file_first_line():
            return None
        return '-'.join(self.line_id.split('-')[0:-1] + [str(self.overall_line_number - 1)])

    def next_line_id(self):
        return '-'.join(self.line_id.split('-')[0:-1] + [str(self.overall_line_number + 1)])

    def has_indent(self, count: int, character: str = ' ') -> bool:
        indent = character * count
        return self.raw_text.startswith(indent) and self.raw_text[count] != character
