"""
Contains classes for linear programming variables.
"""
from numbers import Number
from typing import Union

import pulp

from pylp.expression import Expression
from pylp.constraint import Constraint

ValidOperand = Union[Expression, Number, 'Variable']


class Variable:
    """
    Represents a linear programming variable.

    This is the parent class of all variable classes that you should be using.
    ie. do NOT use this class directly.
    """
    _NAME = 0

    @classmethod
    def pulp_name(cls) -> str:
        """Return a unique name for a new variable."""
        cls._NAME += 1
        return 'x' + str(cls._NAME)

    def __init__(self, *, name: str = None, category: str = 'Continuous') -> None:
        """
        Create a new variable.

        Args:
            name: The name of the variable
            category: The type of variable to create.
        """
        if name is None:
            self._name = Variable.pulp_name()
        else:
            self._name = name
        self._category = category
        self._pulp_var = pulp.LpVariable(self._name, cat=self._category)

    def __str__(self) -> str:
        return f'({self._name} = {self.evaluate()})'

    def __add__(self, other: ValidOperand) -> Expression:
        return Expression('+', [self, other])

    def __radd__(self, other: ValidOperand) -> Expression:
        return Expression('+', [other, self])

    def __sub__(self, other: ValidOperand) -> Expression:
        return Expression('-', [self, other])

    def __rsub__(self, other: ValidOperand) -> Expression:
        return Expression('-', [other, self])

    def __neg__(self):
        return Expression('-', [0, self])

    def __mul__(self, other: ValidOperand) -> Expression:
        if isinstance(other, Variable):
            raise TypeError('Cannot multiply variables in linear programming')

        return Expression('*', [self, other])

    def __rmul__(self, other: ValidOperand) -> Expression:
        if isinstance(other, Variable):
            raise TypeError('Cannot multiply variables in linear programming')

        return Expression('*', [other, self])

    def __truediv__(self, other):
        return Expression('*', [self, 1 / other])

    def __rtruediv__(self, other):
        raise TypeError('Cannot divide by a variable in linear programming')

    def __lt__(self, other: ValidOperand) -> 'Constraint':
        return Constraint(self, '<', other)

    def __le__(self, other: ValidOperand) -> 'Constraint':
        return Constraint(self, '<=', other)

    def __gt__(self, other: ValidOperand) -> 'Constraint':
        return Constraint(self, '>', other)

    def __ge__(self, other: ValidOperand) -> 'Constraint':
        return Constraint(self, '>=', other)

    def __eq__(self, other: ValidOperand) -> 'Constraint':
        return Constraint(self, '==', other)

    def __ne__(self, other: ValidOperand) -> 'Constraint':
        raise TypeError('Cannot have != in linear programming.')

    def construct(self) -> pulp.LpVariable:
        """Build the variable for use in the solver."""
        return self._pulp_var

    def evaluate(self) -> float:
        """The value of the variable found by the solver."""
        return self._pulp_var.varValue


class RealVariable(Variable):
    """
    A variable that represents a real number.
    """

    def __init__(self, name: str = None):
        """Create a new real-valued variable."""
        super().__init__(name=name, category='Continuous')


class IntegerVariable(Variable):
    """
    A variable that represents an integer number.
    """

    def __init__(self, name: str = None):
        """Create a new inter-valued variable."""
        super().__init__(name=name, category='Integer')


class BinaryVariable(Variable):
    """
    A variable that represents a binary variable.

    ie: it only has two value: 0 or 1.
    """

    def __init__(self, name: str = None):
        """Create a new binary variable."""
        super().__init__(name=name, category='Binary')
