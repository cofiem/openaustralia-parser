from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from meeting_record.model import Line


class Base:

    def _get_datetime(self, value: str, date_format: str = '%A, %d %B %Y') -> Optional[datetime]:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            return None

    def _make_ranges(self, lines: List['Line']) -> str:
        if not lines:
            return ''
        result = []

        line_num = lines[0].overall_line_number
        current = [line_num, line_num - 1]
        result.append(current)
        for line in lines:
            line_num = line.overall_line_number
            if current is not None and line_num == (current[1] + 1):
                current[1] = line_num
            else:
                current = [line_num, line_num]
                result.append(current)

        return f"{','.join([f'{i[0]}-{i[1]}' for i in result])} ({len(lines)})"

    def _display_lines(self, lines: List['Line']) -> str:
        return ' '.join([line.normalised_no_whitespace() for line in lines])
