from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Generator, Any, Dict

from meeting_record.model import Base

if TYPE_CHECKING:
    from meeting_record.model import Section, Paragraph, Vote, Preface, TableOfContents


@dataclass
class Document(Base):
    """A document from a file."""

    preface: 'Preface' = None
    toc: 'TableOfContents' = None
    sections: List['Section'] = field(default_factory=list)

    def all_sections(self) -> List['Section']:
        return [i for i in self._get_sections(self.sections)]

    def all_paragraphs(self) -> List['Paragraph']:
        found_sections = self.all_sections()
        return [para for sec in found_sections for para in sec.paragraphs]

    def all_votes(self) -> List['Vote']:
        found_paras = self.all_paragraphs()
        result = [para for para in found_paras if para.__class__.__name__ == 'Vote']  # type: List[Vote]
        return result

    def structure(self) -> List[Dict[str, Any]]:
        return [i.structure() for i in self.sections]

    def _get_sections(self, sections: List['Section']) -> Generator['Section', Any, None]:
        for section in sections:
            if section:
                yield section
            if section.sections:
                self._get_sections(section.sections)

    def __str__(self):
        return f'{str(self.preface)}; {str(self.toc)}; {len(self.sections)} sections'
