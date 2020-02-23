from dataclasses import dataclass, field
from typing import List


@dataclass
class Person:
    """A person responsible for a paragraph or vote."""

    person_id: str

    # the person's last name
    last_name: str

    # the person's initial
    initial_name: str

    # the person's electorate
    electorate: str

    # the person's party
    party: str

    # the person's titles
    titles: List[str] = field(default_factory=list)

    # the person's roles
    roles: List[str] = field(default_factory=list)

    # the paragraphs this person is responsible for
    paragraph_ids: List[str] = field(default_factory=list)
