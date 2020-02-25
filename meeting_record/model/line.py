from dataclasses import dataclass
from typing import List, Optional

from meeting_record.model import Base


@dataclass
class Line(Base):
    """A line in a page, part of a paragraph or page or header."""

    raw_text: str
    overall_line_number: int
    page_line_number: Optional[int] = None

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

    def previous_line_number(self) -> Optional[int]:
        if self.is_file_first_line():
            return None
        return self.overall_line_number - 1

    def next_line_number(self) -> int:
        return self.overall_line_number + 1

    def has_indent(self, count: int, character: str = ' ') -> bool:
        indent = character * count
        return self.raw_text.startswith(indent) and self.raw_text[count] != character
