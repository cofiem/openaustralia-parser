from datetime import datetime
from typing import List, Optional

from boltons.strutils import slugify


class Base:

    def _build_id(self, parts: List[str]) -> str:
        parts_norm = [str(i).replace('_', '-').replace('.', '-') for i in parts]
        return slugify('-'.join(parts_norm), delim='-', ascii=True).decode('utf-8')

    def _get_datetime(self, value: str, date_format: str = '%A, %d %B %Y') -> Optional[datetime]:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            return None
