from dataclasses import field, dataclass
from typing import List, TYPE_CHECKING

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Line, Document


@dataclass
class TableOfContents(Base):
    """A block of text indicating the headings and page numbers."""

    document: 'Document'
    lines: List['Line'] = field(default_factory=list)

    def structure(self) -> List[int]:
        return [i.structure() for i in self.lines]

    def __str__(self):
        return self._make_ranges(self.lines)
