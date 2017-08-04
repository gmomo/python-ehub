"""
Contains functionality for dealing with a linear programming model.
"""
from typing import Iterable
from collections import namedtuple

import pulp
import pulp.solvers
from contexttimer import Timer

from pylp.constraint import Constraint

Status = namedtuple('Status', ['status', 'time'])


def solve(*, objective=None, constraints: Iterable[Constraint] = None,
          minimize: bool = False, solver: str = 'glpk',
          verbose: bool = False) -> Status:
    """
    Solve the linear programming problem.

    Args:
        objective: The objective function
        constraints: The collection of constraints
        minimize: True for minimizing; False for maximizing
        solver: The solver to use. Current supports 'glpk' and 'cplex'.
        verbose: If True, output the results of the solver

    Returns:
        A tuple of the status (eg: Optimal, Unbounded, etc.) and the elapsed
        time
    """
    if minimize:
        sense = pulp.LpMinimize
    else:
        sense = pulp.LpMaximize

    problem = pulp.LpProblem(sense=sense)

    # Objective function is added first
    problem += objective.construct()

    if constraints:
        for constraint in constraints:
            problem += constraint.construct()

    if solver == 'glpk':
        solver = pulp.solvers.GLPK(msg=verbose)
    elif solver == 'cplex':
        solver = pulp.solvers.CPLEX(msg=verbose)
    else:
        raise ValueError(f'Unsupported solver: {solver}')

    with Timer() as time:
        results = problem.solve(solver)

    status = pulp.LpStatus[results]

    return Status(status=status, time=time.elapsed)
