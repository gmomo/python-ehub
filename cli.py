from collections import OrderedDict
from contextlib import redirect_stdout

import numpy as np

from config import settings
from energy_hub import EHubModel


def pretty_print(results):
    np.set_printoptions(linewidth=1000, suppress=True)

    version = results['version']
    solver = results['solver']

    print("Version: {}".format(version))

    print("Solver")
    print("time: {}".format(solver['time']))
    print("termination condition: {}".format(solver['termination_condition']))

    print("Solution")

    print("Objective")
    objectives = results['solution']['objective']
    objectives = OrderedDict(sorted(objectives.items()))
    for name, value in objectives.items():
        print("\t{}: {}".format(name, value))

    print("Variables")

    variables = results['solution']['variables']
    variables = OrderedDict(sorted(variables.items()))
    for name, value in variables.items():
        if isinstance(value, list):
            value = np.array(value)

        print("\n{}: \n{}".format(name, value))


def main():
    model = EHubModel(excel=settings["input_file"])

    results = model.solve()

    pretty_print(results)

    with open(settings["output_file"], 'w') as f:
        with redirect_stdout(f):
            pretty_print(results)


if __name__ == "__main__":
    main()
