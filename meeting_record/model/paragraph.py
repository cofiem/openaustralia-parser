import typing
from dataclasses import field, dataclass
from datetime import datetime
from typing import List

from meeting_record.model import Base

if typing.TYPE_CHECKING:
    from meeting_record.model import Person, Line


@dataclass
class Paragraph(Base):
    """A paragraph, containing lines, in a section."""

    person: 'Person' = None
    date_time_start: datetime = None
    lines: List['Line'] = field(default_factory=list)
