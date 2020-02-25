import typing
from dataclasses import dataclass, field
from typing import List, Tuple, Set, Dict

if typing.TYPE_CHECKING:
    from meeting_record.model import Paragraph, Person


@dataclass
class Vote:
    """A vote in a section."""

    # the result of the vote
    resolution: bool

    # the paragraphs that are part of this vote
    paragraphs: List['Paragraph'] = field(default_factory=list)

    # the people who voted for the question
    affirmative_vote_people: List['Person'] = field(default_factory=list)

    # the people who voted against the question
    negative_vote_people: List['Person'] = field(default_factory=list)

    # the people who paired and did not vote
    pair_people: List[Tuple['Person', 'Person']] = field(default_factory=list)

    def total_voters(self):
        return len(self.affirmative_vote_people) + len(self.negative_vote_people)

    def party_voters_affirmative(self, party_name) -> List['Person']:
        return self._get_people_in_party(self.affirmative_vote_people, party_name)

    def party_voters_negative(self, party_name) -> List['Person']:
        return self._get_people_in_party(self.negative_vote_people, party_name)

    def party_voters_pair(self, party_name) -> List['Person']:
        people: List['Person'] = []
        for person1, person2 in self.pair_people:
            people.append(person1)
            people.append(person2)
        return self._get_people_in_party(people, party_name)

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
