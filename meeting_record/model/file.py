from dataclasses import dataclass, field
from pathlib import Path
from typing import List, TYPE_CHECKING

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Document, Page


@dataclass
class File(Base):
    """A digital container for data."""

    path: Path
    document: 'Document' = None
    pages: List['Page'] = field(default_factory=list)

    def __str__(self):
        return f'{len(self.pages)} pages in {str(self.document)}'
