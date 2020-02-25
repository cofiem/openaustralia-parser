from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Page:
    """A page in a document, containing lines."""

    page_id: str

    # page number in the pdftotext text file (from 1)
    overall_page_number: int

    # the file that contains this line
    file_id: str

    # page number from the pdf (from 1) (metadata)
    pdf_page_number: Optional[int] = None

    # the page title from the pdf (metadata)
    pdf_page_title: Optional[str] = None

    # the page header
    header_id: str = None

    # the lines in this page (excluding the 'metadata' lines)
    line_ids: List[str] = field(default_factory=list)
