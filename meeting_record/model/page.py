import typing
from dataclasses import dataclass, field
from typing import List, Optional

from meeting_record.model import Base

if typing.TYPE_CHECKING:
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
