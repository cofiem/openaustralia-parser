from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Person, Line, Section


@dataclass
class Attendance(Base):
    """The members who were present at some point in the day."""

    section: 'Section'
    lines: List['Line'] = field(default_factory=list)
    people_present: List['Person'] = field(default_factory=list)

    def structure(self) -> List[int]:
        return [i.structure() for i in self.lines]

    def __str__(self):
        return f"{self._make_ranges(self.lines)}: {', '.join([str(i) for i in self.people_present])}"
