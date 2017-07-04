"""
Provides a class that can either be a reference to a value or a Pyomo variable.
"""
from typing import List, Dict

from pyomo.core.base import Model, Set


class ConstantOrVar:
    """
    Like a combination of a Pyomo Param or Var.

    It's used just like a Pyomo Param or Var but allows its values to be either
    a constant (Param) or a variable (a str that maps to a Var).
    """

    def __init__(self, *indices: List[Set], model: Model = None,
                 values: Dict = None) -> None:
        """
        Create a new class.

        Args:
            *indices: The indices of which to index by
            model: The model that holds the Pyomo variables
            values: The dictionary to initialize the object. The keys are
                indexed by *indices and their values are either constants or
                strings that reference a Pyomo variable.
        """
        if model is None or values is None:
            raise ValueError
        self._model = model
        self._indices = indices
        self._values = values

    def __getitem__(self, item):
        value = self._values[item]
        if isinstance(value, str):
            # References a variable
            return getattr(self._model, value)

        return value

    @property
    def values(self):
        """Return the values."""
        return self._values
