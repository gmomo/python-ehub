"""
Provides a class that can either be a reference to a value or to a variable.
"""
from typing import List, Dict


class ConstantOrVar:
    """
    Provides access to data that can either be a constant or a variable.

    The values can either be a constant (like a float) or can be a str, which
    is a reference to a variable in the model.
    """

    def __init__(self, *indices: List, model=None,
                 values: Dict = None) -> None:
        """
        Create a new class.

        Args:
            *indices: The indices of which to index by
            model: The model that holds the variables
            values: The dictionary to initialize the object. The keys are
                indexed by *indices and their values are either constants or
                strings that reference a variable.
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

    def _get_values(self, matrix: Dict) -> Dict:
        for key, value in matrix.items():
            if isinstance(value, dict):
                value = self._get_values(value)
            elif hasattr(value, 'value'):
                value = value.name

            matrix[key] = value

        return matrix

    @property
    def values(self):
        """Return the values."""
        return self._get_values(self._values)
