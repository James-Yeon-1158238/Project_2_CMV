from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class QueryExample:
    
    conditions: Dict[str, Any]
    fields: Optional[List[str]] = None
    order_by: Optional[str] = None
    page: Optional[int] = None
    size: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None