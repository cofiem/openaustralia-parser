from dataclasses import field, dataclass
from datetime import datetime
from typing import List, TYPE_CHECKING

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Person, Line, Section


@dataclass
class Paragraph(Base):
    """A block of text, which might be a transcribed block of text spoken by one person."""

    section: 'Section'
    person: 'Person' = None
    date_time_start: datetime = None
    lines: List['Line'] = field(default_factory=list)

    def structure(self) -> List[int]:
        return [i.structure() for i in self.lines]

    def __str__(self):
        return f"{self._make_ranges(self.lines)}: {self.person} - {self.date_time_start.isoformat() if self.date_time_start else None}"
