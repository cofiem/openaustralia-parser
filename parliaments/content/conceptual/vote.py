from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Vote:
    """A vote in a section."""

    vote_id: str

    # the result of the vote
    resolution: bool

    # the paragraphs that are part of this vote
    paragraph_ids: List[str] = field(default_factory=list)

    # the people who voted for the question
    affirmative_vote_person_ids: List[str] = field(default_factory=list)

    # the people who voted against the question
    negative_vote_person_ids: List[str] = field(default_factory=list)

    # the people who paired and did not vote
    pair_person_ids: List[Tuple[str, str]] = field(default_factory=list)

    def total_voters(self):
        return len(self.affirmative_vote_person_ids) + len(self.negative_vote_person_ids)

    def party_voters_affirmative(self, party_name):
        pass

    def party_voters_negative(self, party_name):
        pass

    def party_voters_pair(self, party_name):
        pass
