from typing import List, Dict

from pyomo.core.base import Model, Set


class ConstantOrVar:
    def __init__(self, *indices: List[Set], model: Model = None,
                 values: Dict = None) -> None:
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
