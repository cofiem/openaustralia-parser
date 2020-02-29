from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Line, Section


@dataclass
class Header(Base):
    """A header in a section or page."""

    section: 'Section'
    lines: List['Line'] = field(default_factory=list)

    def normalised(self) -> str:
        return ' '.join([line.normalised() for line in self.lines])

    def normalised_no_whitespace(self) -> str:
        return ' '.join([line.normalised_no_whitespace() for line in self.lines])

    def structure(self) -> List[int]:
        return [i.structure() for i in self.lines]

    def __str__(self):
        return f"{self._make_ranges(self.lines)}: {self._display_lines(self.lines)}"
