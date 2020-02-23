from dataclasses import field, dataclass
from datetime import datetime
from typing import List


@dataclass
class Paragraph:
    """A paragraph, containing lines, in a section."""

    paragraph_id: str

    # the section that contains this paragraph
    section_id: str

    # the person who is responsible for this paragraph
    person_id: str = None

    # the date and time this paragraph began
    date_time_start: datetime = None

    # the lines in this paragraph
    line_ids: List[str] = field(default_factory=list)
