from enum import Enum, unique, auto


@unique
class BlockType(Enum):
    ATTENDANCE = auto()
    DOCUMENT = auto()
    HEADER = auto()
    PARAGRAPH = auto()
    PREFACE = auto()
    SECTION = auto()
    TABLE_OF_CONTENTS = auto()
    VOTE = auto()
