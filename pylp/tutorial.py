"""
This file serves as a tutorial/example of using PyLP.

To run the file from the root directory of this project, do

    python3.6 -m pylp.tutorial

This is because this tutorial is inside the package it is using.
"""
import pylp
from pylp import RealVariable, IntegerVariable


def main():
    """The main function of the tutorial.

    For this tutorial, we will be finding a selection of candy that minimizes
    our costs but we get at least 400 grams of sugar.
    """
    sugar_amount = 400  # We want to have at least this amount of sugar

    # The candy shop only has a selection of chocolate bars, lollipops, and ice
    # cream.
    sweets = ['Chocolate Bar', 'Lollipop', 'Ice Cream']

    sugar_per_sweet = {
        'Chocolate Bar': 40,  # grams per bar
        'Lollipop': 20,  # grams per item
        'Ice Cream': 0.20,  # grams per gram
    }
    cost_per_sweet = {
        'Chocolate Bar': 2.40,  # dollars per bar
        'Lollipop': 1.20,  # dollars per item
        'Ice Cream': 0.02,  # dollars per gram
    }
    amount_per_sweet = {
        'Chocolate Bar': IntegerVariable(),  # Can't have a fraction of a bar
        'Lollipop': IntegerVariable(),  # Can't have a fraction of a lollipop
        'Ice Cream': RealVariable(),  # Amount in grams
    }

    # The total cost of our selection
    total_cost = sum(cost_per_sweet[sweet] * amount_per_sweet[sweet]
                     for sweet in sweets)

    # Constrain our model so we get at least 400 grams of sugar
    sugar_constraint = sum(sugar_per_sweet[sweet] * amount_per_sweet[sweet]
                           for sweet in sweets) >= sugar_amount

    # Ensure we can't have negative amounts of anything. By defining a
    # variable, we don't constrain its values at all.
    amount_constraints = [amount_per_sweet[sweet] >= 0 for sweet in sweets]

    # Our total list of constraints
    constraints = [sugar_constraint] + amount_constraints

    # Here we solve the problem by minimizing the total cost with respect to
    # the list of constraints. For us, we will use GLPK to solve the problem.
    status = pylp.solve(objective=total_cost, constraints=constraints,
                        minimize=True, solver='glpk')

    # Print the status of the model
    print(f'Terminated in {status.time}s with a(n) {status.status} '
          f'solution/problem')

    for sweet in sweets:
        print(f'Amount of {sweet}: {amount_per_sweet[sweet].evaluate()}')

    print(f'Total Cost: {total_cost.evaluate()}')

    # You can play around with the constraints just like you would with any
    # regular Python boolean comparisons.


if __name__ == '__main__':
    main()
