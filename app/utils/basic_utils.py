from typing import Callable, List, TypeVar, Dict, MutableMapping
from functools import reduce

T = TypeVar('T')  # list item type
K = TypeVar('K')  # key type
V = TypeVar('V')  # value type
M = TypeVar('M', bound=MutableMapping)  # map container type


def to_map(items: List[T], key_fn: Callable[[T], K], value_fn: Callable[[T], V], merge_fn: Callable[[V, V], V]) -> Dict[K, V]:
    """
    Create a map from a list of items using the provided key and value extractors.
    When duplicate keys are encountered, values are merged using the merge_fn.
    Uses standard dict as the backing map.
    """
    return to_map_supplier(items, key_fn, value_fn, merge_fn, lambda: {})


def to_map_supplier(items: List[T], key_fn: Callable[[T], K], value_fn: Callable[[T], V], merge_fn: Callable[[V, V], V], map_supplier: Callable[[], M]) -> M:
    """
    Create a map from a list of items using the provided key and value extractors.
    Supports custom map container via map_supplier, and a merge function for duplicate keys.
    """
    def reducer(acc: M, item: T) -> M:
        key = key_fn(item)
        value = value_fn(item)
        if key in acc:
            acc[key] = merge_fn(acc[key], value)
        else:
            acc[key] = value
        return acc

    return reduce(reducer, items, map_supplier())


def to_grouped_map(items: List[T], key_fn: Callable[[T], K], value_fn: Callable[[T], V], map_supplier: Callable[[], MutableMapping[K, List[V]]]) -> MutableMapping[K, List[V]]:
    """
    Groups values by key. The result is a mapping from key to a list of values.
    Accepts a custom map supplier (e.g., dict, OrderedDict, defaultdict).
    """
    result = map_supplier()
    for item in items:
        key = key_fn(item)
        value = value_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(value)
    return result