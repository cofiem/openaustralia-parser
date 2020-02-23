from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class File:
    """A file containing pages."""

    file_id: str

    # the path to this file
    path: Path

    # the document built from this file
    document_id: str = None

    page_ids: List[str] = field(default_factory=list)
