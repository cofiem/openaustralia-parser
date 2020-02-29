from dataclasses import dataclass, field
from enum import Enum, unique, auto
from typing import List, Set, Dict, TYPE_CHECKING, Optional, Any

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Person, Line, Section


@unique
class Outcome(Enum):
    AGREED = auto()
    NEGATIVED = auto()


@unique
class Response(Enum):
    AFFIRMATIVE = auto()
    NEGATIVE = auto()


@dataclass
class Vote(Base):
    """An expression of opinion of members of a group."""

    section: 'Section'

    # e.g. Division: Question put—That the motion be agreed to.
    question_lines: List['Line'] = field(default_factory=list)

    # ayes, with names
    yes_lines: List['Line'] = field(default_factory=list)

    # noes, with names
    no_lines: List['Line'] = field(default_factory=list)

    # Pair:
    pair_lines: List['Line'] = field(default_factory=list)

    # e.g. Resolved in the affirmative.
    resolution_lines: List['Line'] = field(default_factory=list)

    # e.g. Motion agreed to.
    outcome_lines: List['Line'] = field(default_factory=list)

    # the people who voted for the question
    yes_people: List['Person'] = field(default_factory=list)

    # the people who voted against the question
    no_people: List['Person'] = field(default_factory=list)

    # the people who paired and did not vote
    pair_people: List['Person'] = field(default_factory=list)

    def total_voters(self):
        return len(self.yes_people) + len(self.no_people)

    def total_vote_yes(self):
        return len(self.yes_people)

    def total_vote_no(self):
        return len(self.no_people)

    def party_vote_yes(self, party_name) -> List['Person']:
        return self._get_people_in_party(self.yes_people, party_name)

    def party_vote_no(self, party_name) -> List['Person']:
        return self._get_people_in_party(self.no_people, party_name)

    def party_vote_paired(self, party_name) -> List['Person']:
        return self._get_people_in_party(self.pair_people, party_name)

    def question_text(self) -> Optional[str]:
        if not self.question_lines:
            return None

        text = ' '.join(i.normalised_no_whitespace() for i in self.question_lines).strip()
        if not text:
            return None

        result = text.replace(self.text_division(), '').replace(self.text_question_put(), '').strip()
        return result

    def question_phrasing(self) -> Optional[Response]:
        question_text = self.question_text()
        if not question_text:
            return None

        return Response.AFFIRMATIVE if 'be agreed to' in question_text else Response.NEGATIVE

    def text_division(self) -> str:
        return 'Division:'

    def text_question_put(self) -> str:
        return 'Question put—'

    def resolution(self) -> Optional[Response]:
        result_yes = any(line.contains_word('affirmative') for line in self.resolution_lines)
        result_no = any(line.contains_word('negatived') for line in self.resolution_lines)
        if result_yes:
            return Response.AFFIRMATIVE
        if result_no:
            return Response.NEGATIVE
        return None

    def outcome(self) -> Optional[Outcome]:
        result_yes = any(line.contains('agreed to') for line in self.outcome_lines)
        if result_yes:
            return Outcome.AGREED
        return Outcome.NEGATIVED

    def _get_people_in_party(self, people, party_name) -> List['Person']:
        people_party: Dict[str, Set['Person']] = {}
        for person in people:
            if person.party not in people:
                people_party[person.party] = set()
            people_party[person.party].add(person)

        if party_name in people_party:
            return list(people_party[party_name])
        else:
            return []

    def structure(self) -> Dict[str, Any]:
        return {
            'question': [i.structure() for i in self.question_lines],
            'yes': [i.structure() for i in self.yes_lines],
            'no': [i.structure() for i in self.no_lines],
            'pair': [i.structure() for i in self.pair_lines],
            'resolution': [i.structure() for i in self.resolution_lines],
            'outcome': [i.structure() for i in self.outcome_lines],
        }

    def __str__(self):
        return f"{str(self.question_text())} ({self.total_voters()} - " \
               f"yes: {len(self.yes_lines)} no: {len(self.no_lines)} pair: {len(self.pair_lines)} - " \
               f"{self.resolution()} - {self.outcome()}"
