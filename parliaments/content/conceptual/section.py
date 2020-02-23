from dataclasses import dataclass, field
from typing import List


@dataclass
class Section:
    """A section in a document, possibly with a parent section,
    containing a header as well as paragraphs and child sections."""

    section_id: str

    # the document that contains this section
    document_id: str

    # the header of the section
    header_id: str = None

    # sections within this section
    sub_section_ids: List[str] = field(default_factory=list)

    # the paragraphs in the section
    paragraph_ids: List[str] = field(default_factory=list)
