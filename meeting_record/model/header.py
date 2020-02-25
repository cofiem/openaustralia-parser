import typing
from dataclasses import dataclass
from typing import List

from meeting_record.model import Base

if typing.TYPE_CHECKING:
    from meeting_record.model import Line


@dataclass
class Header(Base):
    """A header in a section or page."""

    lines: List['Line']
