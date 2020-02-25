import typing
from dataclasses import dataclass, field
from datetime import date
from typing import List

from meeting_record.model import Base

if typing.TYPE_CHECKING:
    from meeting_record.model import Section


@dataclass
class Document(Base):
    """A document from a file."""

    session: str
    session_date: date = None
    identifier: str = None
    sections: List['Section'] = field(default_factory=list)
