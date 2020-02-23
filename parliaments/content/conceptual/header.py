from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Header:
    """A header in a section."""

    header_id: str

    # the lines in the header
    line_ids: List[str]

    # this header is for this section
    section_id: Optional[str]

    # this header is for this page
    page_id: Optional[str]
