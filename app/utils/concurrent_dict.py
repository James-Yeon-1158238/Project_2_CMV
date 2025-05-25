from collections.abc import MutableMapping
from typing import TypeVar, Generic, Optional
import threading

K = TypeVar("K")
V = TypeVar("V")

class ConcurrentDict(MutableMapping, Generic[K, V]):
    """
    A thread-safe dictionary implementation.

    `ConcurrentDict` is a dictionary-like data structure that ensures safe 
    concurrent access from multiple threads using a reentrant lock (`RLock`).

    This class implements the `MutableMapping` interface, making it compatible 
    with standard dictionary operations such as setting, getting, deleting items, 
    and iteration.

    Attributes:
        _dict (dict[K, V]): The underlying dictionary storing key-value pairs.
        _lock (threading.RLock): A reentrant lock to ensure thread-safe operations.

    Example:
        ```python
        from concurrent.futures import ThreadPoolExecutor

        cdict = ConcurrentDict[str, int]()

        def worker():
            for i in range(100):
                cdict[f"key-{i}"] = i

        with ThreadPoolExecutor(max_workers=4) as executor:
            for _ in range(4):
                executor.submit(worker)

        print(len(cdict))  # Expected output: 100
        ```
    """

    
    def __init__(self) -> None:
        """Initializes an empty thread-safe dictionary."""
        self._dict: dict[K, V] = {}
        self._lock = threading.RLock()

    def __setitem__(self, key: K, value: V) -> None:
        """
        Sets a key-value pair in the dictionary.

        This method ensures that write operations are thread-safe.

        Args:
            key (K): The key to set.
            value (V): The value to associate with the key.

        Example:
            ```python
            cdict["user_id"] = 123
            ```
        """
        with self._lock:
            self._dict[key] = value

    def __getitem__(self, key: K) -> V:
        """
        Retrieves the value associated with the given key.

        Ensures thread-safe read access.

        Args:
            key (K): The key to look up.

        Returns:
            V: The value associated with the key.

        Raises:
            KeyError: If the key is not found.

        Example:
            ```python
            value = cdict["user_id"]
            ```
        """
        with self._lock:
            return self._dict[key]

    def __delitem__(self, key: K) -> None:
        """
        Deletes the key-value pair from the dictionary.

        Ensures thread-safe deletion.

        Args:
            key (K): The key to delete.

        Raises:
            KeyError: If the key does not exist.

        Example:
            ```python
            del cdict["user_id"]
            ```
        """
        with self._lock:
            del self._dict[key]

    def __iter__(self):
        """
        Returns an iterator over the keys of the dictionary.

        A shallow copy of the keys is created to avoid race conditions during iteration.

        Returns:
            Iterator[K]: An iterator over dictionary keys.

        Example:
            ```python
            for key in cdict:
                print(key)
            ```
        """
        with self._lock:
            return iter(self._dict.copy())

    def __len__(self) -> int:
        """
        Returns the number of key-value pairs in the dictionary.

        Ensures thread-safe access to the size of the dictionary.

        Returns:
            int: The number of stored items.

        Example:
            ```python
            size = len(cdict)
            ```
        """
        with self._lock:
            return len(self._dict)

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Retrieves the value for a given key, returning a default value if not found.

        This method is thread-safe.

        Args:
            key (K): The key to look up.
            default (Optional[V], optional): The default value if key is not found. Defaults to None.

        Returns:
            Optional[V]: The retrieved value or the default.

        Example:
            ```python
            value = cdict.get("non_existent_key", 42)
            ```
        """
        with self._lock:
            return self._dict.get(key, default)

