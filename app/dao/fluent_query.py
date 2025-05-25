from typing import Any, Callable, Optional
from app.dao.example import Example, MatchMode
from app.dao.query_example import QueryExample 


class FluentQuery:
    def __init__(self, example: Example):
        self.example = example
        self._sort: Optional[tuple[str, str]] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._projection: Optional[Callable[[Any], Any]] = None
        self._page: Optional[int] = None
        self._size: Optional[int] = None

    def sort(self, field: str, direction: str = "ASC") -> 'FluentQuery':
        self._sort = (field, direction.upper())
        return self

    def limit(self, size: int) -> 'FluentQuery':
        self._limit = size
        return self

    def offset(self, offset: int) -> 'FluentQuery':
        self._offset = offset
        return self

    def page(self, page: int, size: int) -> 'FluentQuery':
        self._page = page
        self._size = size
        return self

    def project(self, fn: Callable[[Any], Any]) -> 'FluentQuery':
        self._projection = fn
        return self

    def execute(self, repo):
        query_example = self._build_query_example()
        if self._page is not None and self._size is not None:
            return repo._execute_page_query(query_example, projection=self._projection)
        return repo.find_all_by_example(query_example, projection=self._projection)

    def _build_query_example(self):
        conditions = {}
        for field, value in vars(self.example.probe).items():
            if value is None:
                continue

            match_mode = self.example.matcher.match_modes.get(field, MatchMode.EXACT)
            logic_mode = self.example.matcher.logic_modes.get(field, "AND") if hasattr(self.example.matcher, "logic_modes") else "AND"

            op_suffix = "__like" if match_mode != MatchMode.EXACT else ""
            logic_suffix = "__or__" if logic_mode == "OR" else ""

            key = f"{field}{op_suffix}{logic_suffix}"
            val = (
                f"%{value}%" if match_mode == MatchMode.CONTAINS else
                f"{value}%" if match_mode == MatchMode.STARTS_WITH else
                f"%{value}" if match_mode == MatchMode.ENDS_WITH else
                value
            )

            conditions[key] = val

        order_by = f"{self._sort[0]} {self._sort[1]}" if self._sort else None

        return QueryExample(
            conditions=conditions,
            fields=["*"],
            order_by=order_by,
            page=self._page,
            size=self._size,
            limit=self._limit,
            offset=self._offset
        )