"""
Provides functionality for handling a request format capacity.
"""
from typing import Optional


class Capacity:
    """
    A wrapper for a request format capacity.
    """

    def __init__(self, capacity_request: dict) -> None:
        """
        Create a new wrapper.

        Args:
            capacity_request: The capacity in the capacities section of the
                request format
        """
        self._capacity = capacity_request

    @property
    def name(self) -> str:
        """The name of the capacity."""
        return self._capacity['name']

    @property
    def domain(self):
        """The domain of the capacity."""
        return self._capacity['type']

    @property
    def lower_bound(self) -> Optional[float]:
        """The lower bound of the capacity as a float."""
        if 'bounds' in self._capacity and 'lower' in self._capacity['bounds']:
            return self._capacity['bounds']['lower']

        return None  # Unbounded

    @property
    def upper_bound(self) -> Optional[float]:
        """The lower bound of the capacity as a float."""
        if 'bounds' in self._capacity and 'upper' in self._capacity['bounds']:
            return self._capacity['bounds']['upper']

        return None  # Unbounded
