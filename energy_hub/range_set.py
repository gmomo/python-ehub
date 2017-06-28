from typing import Optional

from pyomo.core.base import RangeSet, Set


class RangeSet(RangeSet):
    """
    A wrapper for a Pyomo RangeSet that operates more like Python's `range`.
    """
    def __init__(self, *, start: int = 0, stop: Optional[int] = None,
                 step: int = 1, within: Optional[Set] = None, **kwargs):
        """
        Create a new set [start, start+step, ..., stop).

        This acts much more like Python's `range`.

        Args:
            start: The starting point
            stop: The end point. The set does not contain this point.
            step: The step between elements of the set
            within: The superset of this set
            **kwargs:
        """
        if stop is None:
            raise ValueError("Must specify a stopping point")

        super().__init__(start, stop - 1, step, within=within, **kwargs)
