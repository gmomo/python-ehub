"""
Provides functionality for handling a request format's storage.
"""
from typing import Union


class Storage:
    """A wrapper for a request format storage."""

    def __init__(self, storage_request: dict, capacity_request: dict) -> None:
        """
        Create a new wrapper.

        Args:
            storage_request: The request format storage
            capacity_request: The request format capacity corresponding to the
                storage
        """
        self._storage = storage_request
        self._capacity = capacity_request

    @property
    def name(self) -> str:
        """Return the name of the storage."""
        return self._storage['name']

    @property
    def capacity(self) -> Union[float, str]:
        return self._storage['capacity']

    @property
    def stream(self) -> str:
        """The stream that this storage holds."""
        return self._storage['stream']

    @property
    def min_state(self) -> float:
        """The minimum state of charge of the storage."""
        return self._storage['min_state']

    @property
    def discharge_efficiency(self) -> float:
        """The discharge efficiency of the storage."""
        return self._storage['discharge_efficiency']

    @property
    def charge_efficiency(self) -> float:
        """The charge efficiency of the storage."""
        return self._storage['charge_efficiency']

    @property
    def lifetime(self) -> float:
        """The life time in years of the storage."""
        return self._storage['lifetime']

    @property
    def cost(self) -> float:
        """The cost of the storage."""
        return self._storage['cost']

    @property
    def max_charge(self) -> float:
        """The maximum charge of the storage."""
        return self._storage['max_charge']

    @property
    def max_discharge(self) -> float:
        """The maximum discharge of the storage."""
        return self._storage['max_discharge']

    @property
    def decay(self) -> float:
        """The decay of the storage."""
        return self._storage['decay']
