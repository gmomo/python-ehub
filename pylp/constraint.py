"""
Contains a class for a linear programming constraint.

Exports:
    >>> from pylp.constraint import Constraint

"""
from contextlib import suppress


class Constraint:
    """
    Represents a linear programming constraint.
    """

    def __init__(self, lhs, operator: str, rhs) -> None:
        """
        Create a new constraint between lhs and rhs.

        Args:
            lhs: The left-hand side of the constraint
            operator: The boolean operator as a str
            rhs: The right-hand side of the constraint
        """
        self._constraint = (lhs, operator, rhs)

    def __str__(self) -> str:
        lhs, operator, rhs = self._constraint
        return f'{lhs} {operator} {rhs}'

    @property
    def rhs(self):
        return self._constraint[2]

    @property
    def lhs(self):
        return self._constraint[0]

    @property
    def operator(self):
        return self._constraint[1]

    def construct(self):
        """Build the constraint for use in the solver."""
        lhs, operator, rhs = self._constraint

        # lhs and rhs may not be expressions
        with suppress(AttributeError):
            lhs = lhs.construct()
        with suppress(AttributeError):
            rhs = rhs.construct()

        # Lazy evaluate to avoid errors
        return {
            '<=': lambda: lhs <= rhs,
            '>=': lambda: lhs >= rhs,
            '<': lambda: lhs < rhs,
            '>': lambda: lhs > rhs,
            '==': lambda: lhs == rhs,
        }[operator]()
