import typing
from dataclasses import dataclass, field
from typing import List

from meeting_record.model import Base

if typing.TYPE_CHECKING:
    from meeting_record.model import Paragraph, Header


@dataclass
class Section(Base):
    """A section in a document, possibly with a parent section,
    containing a header as well as paragraphs and child sections."""

    header: 'Header' = None
    paragraphs: List['Paragraph'] = field(default_factory=list)
    sub_sections: List['Section'] = field(default_factory=list)
