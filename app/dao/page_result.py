from dataclasses import dataclass
from typing import List, TypeVar, Generic

T = TypeVar('T')

@dataclass
class PageResult(Generic[T]):
    data: List[T]
    total: int
    page: int
    size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.size - 1) // self.size
