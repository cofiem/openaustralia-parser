import re
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

from meeting_record.model import Base


@dataclass
class Line(Base):
    """A line in a page, part of a paragraph or page or header."""

    raw_text: str
    overall_line_number: int
    page_line_number: Optional[int] = None
    page_number: Optional[int] = None

    def contains(self, value: str) -> bool:
        if self.raw_text and value:
            return value.casefold() in self.raw_text.casefold()
        return False

    def contains_word(self, value: str) -> bool:
        if self.raw_text and value:
            words = self.split_words()
            value_cf = value.casefold()
            return any(word.casefold() == value_cf for word in words)
        return False

    def normalised(self) -> str:
        return self.raw_text.strip('\f\n\t') if self.raw_text else ''

    def normalised_no_whitespace(self) -> str:
        norm = self.normalised()
        return norm.strip() if norm else ''

    def split_words(self) -> List[str]:
        norm_no_ws = self.normalised_no_whitespace()
        if not norm_no_ws:
            return []
        return [i for i in re.split(r'\b', norm_no_ws) if i and any(c.isalpha() for c in i)]

    def is_page_first_line(self):
        return self.page_line_number == 1

    def is_file_first_line(self):
        return self.overall_line_number == 1

    def is_empty(self) -> bool:
        return self.normalised_no_whitespace() == ''

    def previous_overall_line_number(self) -> Optional[int]:
        if self.is_file_first_line():
            return None
        return self.overall_line_number - 1

    def next_overall_line_number(self) -> int:
        return self.overall_line_number + 1

    def previous_page_line_number(self) -> Optional[int]:
        if self.is_page_first_line():
            return None
        return self.page_line_number - 1

    def next_page_line_number(self) -> int:
        return self.page_line_number + 1

    def has_indent_at_least(self, count: int, character: str = ' ') -> bool:
        indent = character * count
        return self.raw_text.startswith(indent)

    def has_indent(self, counts: List[int], character: str = ' ') -> bool:
        for count in counts:
            if self.has_indent_at_least(count, character) and self.raw_text[count] != character:
                return True
        return False

    def has_readable_text(self) -> bool:
        return self.raw_text and any(c.isalpha() for c in self.normalised_no_whitespace())

    def structure(self) -> int:
        return self.overall_line_number

    def __str__(self):
        return f'{self.overall_line_number}-{self.page_number}-{self.page_number}: "{self.raw_text}"'
