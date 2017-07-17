"""
A simple library for doing mixed-integer linear programming.

Exports:
    All the variables that can be used
    >>> from pylp import (RealVariable, BinaryVariable, IntegerVariable,
    ... Variable)

    The function to solve a linear programming model
    >>> from pylp import solve
"""
from pylp.variable import (
    Variable, RealVariable, BinaryVariable,
    IntegerVariable,
)
from pylp.problem import solve
