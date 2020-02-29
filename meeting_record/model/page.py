from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Line


@dataclass
class Page(Base):
    """A page in a file."""

    overall_number: int
    header_number: Optional[int] = None
    header_title: Optional[str] = None
    header_lines: List['Line'] = field(default_factory=list)
    footer_lines: List['Line'] = field(default_factory=list)
    body_lines: List['Line'] = field(default_factory=list)

    def __str__(self):
        return f'Page {self.overall_number} "{self.header_title} - {self.header_number}"; ' \
               f'lines: {self._make_ranges(self.header_lines)} header, ' \
               f'{self._make_ranges(self.body_lines)} body, {self._make_ranges(self.footer_lines)} footer'
