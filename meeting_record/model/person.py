from dataclasses import dataclass, field
from typing import List

from meeting_record.model import Base


@dataclass
class Person(Base):
    """A person responsible for a paragraph or vote."""

    last_name: str
    initial_name: str
    electorate: str
    party: str
    titles: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
