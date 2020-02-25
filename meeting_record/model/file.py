import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from meeting_record.model import Base

if typing.TYPE_CHECKING:
    from meeting_record.model import Document, Page


@dataclass
class File(Base):
    """A file containing pages to make a document."""

    path: Path
    document: 'Document' = None
    pages: List['Page'] = field(default_factory=list)
