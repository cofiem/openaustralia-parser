import datetime
from dataclasses import field, dataclass
from typing import List, TYPE_CHECKING

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Line, Document


@dataclass
class Preface(Base):
    """A block of text before the table of contents."""

    document: 'Document'
    session: str = None
    session_date: datetime.date = None
    identifier: str = None
    lines: List['Line'] = field(default_factory=list)

    def structure(self) -> List[int]:
        return [i.structure() for i in self.lines]

    def __str__(self):
        return f'{self._make_ranges(self.lines)}: {self.identifier} for {self.session} on {self.session_date.isoformat()}'
