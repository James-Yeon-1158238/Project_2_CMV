from dataclasses import dataclass, field
from typing import Any


class MatchMode:
    EXACT = "exact"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"

class LogicMode:
    AND = "and"
    OR = "or"

@dataclass
class ExampleMatcher:
    match_modes: dict[str, str] = field(default_factory = dict)
    logic_modes: dict[str, str] = field(default_factory=dict) 

    def with_match_mode(self, field: str, mode: str, logic: LogicMode = LogicMode.AND) -> 'ExampleMatcher':
        self.match_modes[field] = mode
        self.logic_modes[field] = logic.upper()
        return self

@dataclass
class Example:
    probe: Any
    matcher: ExampleMatcher = field(default_factory=ExampleMatcher)