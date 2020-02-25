from typing import List

from boltons.strutils import slugify


class Base:

    def _build_id(self, parts: List[str]) -> str:
        parts_norm = [str(i).replace('_', '-').replace('.', '-') for i in parts]
        return slugify('-'.join(parts_norm), delim='-', ascii=True).decode('utf-8')
