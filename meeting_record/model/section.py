from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Dict, Any, Optional

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Paragraph, Header, Vote, Attendance, Document


@dataclass
class Section(Base):
    """A section in a document, possibly with a parent section,
    containing a header as well as paragraphs and child sections."""

    document: 'Document'
    section: Optional['Section'] = None
    header: 'Header' = None
    paragraphs: List['Paragraph'] = field(default_factory=list)
    attendance: 'Attendance' = None
    votes: List['Vote'] = field(default_factory=list)
    sections: List['Section'] = field(default_factory=list)

    def is_attendance(self) -> bool:
        return self.header and self.header.normalised_no_whitespace().casefold() == 'ATTENDANCE'.casefold()

    def structure(self) -> Dict[str, Any]:
        result = {
            'header': self.header.structure() if self.header else None,
            'paragraphs': [line for para in self.paragraphs for line in para.structure()],
            'votes': [i.structure() for i in self.votes],
            'sections': [i.structure() for i in self.sections],
            'attendance': self.attendance.structure() if self.attendance else None,
        }
        for key in list(result.keys()):
            if not result[key]:
                del result[key]
        return result

    def __str__(self):
        return f"{self.header} with {len(self.paragraphs)} paras, {len(self.votes)} votes, " \
               f"and {len(self.sections)} sections"
