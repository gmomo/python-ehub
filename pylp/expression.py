"""
Contains functionality for dealing with expressions.

Exports:
    >>> from pylp.expression import Expression
"""
from contextlib import suppress
from typing import Iterable, List

from pylp.constraint import Constraint


class Expression:
    """
    Represents an expression in a linear programming problem.

    Notes:
        A list of operands is given in order to reduce the height of the
        expression tree.

        Normally, an operator operates on two operands. Thus the expression:
            5 + 5 + 5
        can be represented as a tree:
            +
           /\
          5  +
            / \
           5   5

        But as the expression gets longer, a naive approach would result in
        a very tall tree. In order to evaluate the tree, we would have to
        traverse all the way to its leafs, which at its deepest part would
        probably result in a stack overflow (maximum recursion error).

        But treating the operands as a list, results in a nicer tree:
           +
         / | \
        5  5  5

        And this tree stays at the same height the more operands it holds.

        This prevents a stack overflow from occurring. This also results in
        better performance as well.
    """

    def __init__(self, operator: str, operands: list) -> None:
        """
        Create a new expression for the given operator and operands.

        Args:
            operator: The str of the operator
            operands: A list of operands
        """
        self.operator = operator

        self.arguments = []
        self._set_arguments(operands)

    def _set_arguments(self, arguments: list) -> None:
        for arg in arguments:
            if isinstance(arg, Expression) and self.is_same_type(arg):
                self.arguments += arg.arguments
            else:
                self.arguments += [arg]

    def is_same_type(self, other: 'Expression') -> bool:
        """Return True if the other expression is of the same type."""
        return self.operator == other.operator

    def __str__(self) -> str:
        arguments = (str(arg) for arg in self.arguments)

        expression = f' {self.operator} '.join(arguments)

        return f'({expression})'

    def __le__(self, other) -> Constraint:
        return Constraint(self, '<=', other)

    def __ge__(self, other) -> Constraint:
        return Constraint(self, '>=', other)

    def __eq__(self, other) -> Constraint:
        return Constraint(self, '==', other)

    def __ne__(self, other) -> Constraint:
        raise TypeError('Cannot have != in linear programming.')

    def __lt__(self, other) -> Constraint:
        return Constraint(self, '<', other)

    def __gt__(self, other) -> Constraint:
        return Constraint(self, '>', other)

    def __sub__(self, other) -> 'Expression':
        return Expression('-', [self, other])

    def __rsub__(self, other) -> 'Expression':
        return Expression('-', [other, self])

    def __add__(self, other) -> 'Expression':
        return Expression('+', [self, other])

    def __radd__(self, other) -> 'Expression':
        return Expression('+', [other, self])

    def __mul__(self, other) -> 'Expression':
        return Expression('*', [self, other])

    def __rmul__(self, other) -> 'Expression':
        return Expression('*', [other, self])

    def __neg__(self) -> 'Expression':
        return Expression('*', [-1, self])

    def __truediv__(self, other) -> 'Expression':
        return Expression('*', [self, 1 / other])

    def __rtruediv__(self, other):
        # An expression will always have a variable in it. Otherwise, it would
        # use the regular int's or float's operations.
        raise TypeError('Cannot divide by a variable in linear programming.')

    def _handle(self, arguments):
        # Lazy evaluate to prevent errors and reduce computation
        return {
            '+': lambda: self._handle_add(arguments),
            '*': lambda: self._handle_multiplication(arguments),
            '-': lambda: self._handle_subtraction(arguments),
        }[self.operator]()

    @staticmethod
    def _handle_add(arguments: Iterable['Expression']):
        result = 0
        for arg in arguments:
            result += arg

        return result

    @staticmethod
    def _handle_subtraction(arguments: List['Expression']):
        result = arguments[0]
        for arg in arguments[1:]:
            result -= arg

        return result

    @staticmethod
    def _handle_multiplication(arguments: Iterable['Expression']):
        result = 1
        for arg in arguments:
            result *= arg

        return result

    def evaluate(self):
        """Evaluate the expression."""
        arguments = []
        for arg in self.arguments:
            with suppress(AttributeError):
                arg = arg.evaluate()
            arguments.append(arg)

        try:
            return self._handle(arguments)
        except KeyError:
            raise ValueError(f'Using unsupported operator: {self.operator}')

    def construct(self):
        """Build the expression for use in the solver."""
        arguments = []
        for arg in self.arguments:
            with suppress(AttributeError):
                arg = arg.construct()
            arguments.append(arg)

        try:
            return self._handle(arguments)
        except KeyError:
            raise ValueError(f'Using unsupported operator: {self.operator}')
