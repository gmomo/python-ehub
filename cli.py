from collections import OrderedDict
from contextlib import redirect_stdout

import numpy as np
from pyomo.core.base import Var

from ehub_model import EHubModel
from config import settings


def to_matrix(var):
    # Determine the dimension of the matrix
    try:
        dim = len(list(var.keys())[0])
    except TypeError:
        dim = 1

    if dim == 1:
        return list(var.values())
    elif dim == 2:
        keys = var.keys()

        length = (max(keys, key=lambda t: t[0])[0],
                  max(keys, key=lambda t: t[1])[1])

        matrix = [[0 for _ in range(length[1])] for _ in range(length[0])]

        for index, value in var.items():
            x = index[0] - 1
            y = index[1] - 1

            matrix[x][y] = value

        return np.matrix(matrix)
    else:
        raise NotImplemented


def pretty_print(results, model):
    print("Problem")
    print(results['Problem'])
    print("Solver")
    print(results['Solver'])

    print("Solution")
    solution = results['Solution'][0]

    # Get the objective and print it
    print("Objective")
    print("\ttotal_cost: {}".format(solution['Objective']['Total_Cost']['Value']))

    # Print the variables
    variables = {k: v for k, v in model.__dict__.items()
                 if isinstance(v, Var)}
    variables = OrderedDict(sorted(variables.items()))

    print("Variables")
    for name, value in variables.items():
        if hasattr(value, 'value'):
            value = value.value
        else:
            value = value.get_values()

        if isinstance(value, dict):
            value = to_matrix(value)

            print("\n{}:\n{}".format(name, value))
            # for x, row in enumerate(value):
            #     print("\t\t{}: {}".format(x, row))
        else:
            print("\n{}: {}".format(name, value))


def main():
    model = EHubModel(excel=settings["input_file"])

    results = model.solve()

    np.set_printoptions(linewidth=1000, suppress=True)

    # Pretty bad, but it is temporary
    pretty_print(results, model._model)

    with open(settings["output_file"], 'w') as f:
        with redirect_stdout(f):
            pretty_print(results, model._model)


if __name__ == "__main__":
    main()
