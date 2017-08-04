# PyLP

A mixed integer linear programming library for Python.

## Comparisons

Here is a list of pros and cons of various other libraries.
There is also a section for PyLP.

#### Pyomo

Pros:
- long tutorial on how to use it
- lots of other features
- mature

Cons:
- source code is bad
- really complex for simple problems
- heavily ties the code to Pyomo

#### PuLP

Currently, PyLP is a wrapper over PuLP.

Pros:
- very basic functionality

Cons:
- naming scheme is not Pythonic
    - Example: `LpVariable` should be just `Variable` and could be called via
    `pulp.Variable` if need be
- awkward way of adding constraints and objective
    - there is potential to overwrite the objective function
    - constraints are added by using `+=` on a `LpProblem` instance
    
#### PyLP

Pros:
- very basic functionality
- easy to read source code
- tries to be Pythonic

Cons:
- documentation is sparse
    - have to read the docstrings really
    - only one tutorial
- more verbose for constrained variables
    - can't define limits for a variable when declaring the variable; you have
    to do that yourself in another constraint.
- young library

## Example

Can be found [here](../pylp/tutorial.py)
