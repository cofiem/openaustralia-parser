from dataclasses import dataclass
from datetime import date


@dataclass
class Document:
    """A document."""

    document_id: str

    session: str = None

    international_standard_serial_number: str = None

    document_date: date = None
