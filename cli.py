"""
The CLI for the EHub Model.

The options for running the model are set in the config.yaml file. See that
file for more information.

Given the config.yaml file, solving the model is easy:

    $ python3.6 cli.py

The program will then print out the solved variables as well as show the
output of whatever solver is configured in the config.yaml file.
"""

from collections import OrderedDict
from contextlib import redirect_stdout

import numpy as np

from config import settings
from energy_hub import EHubModel


def pretty_print(results: dict) -> None:
    """Print the results in a prettier format.

    Args:
        results: The results dictionary to print
    """
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
    """The main function for the CLI."""
    model = EHubModel(excel=settings["input_file"])

    results = model.solve()

    pretty_print(results)

    with open(settings["output_file"], 'w') as file:
        with redirect_stdout(file):
            pretty_print(results)


if __name__ == "__main__":
    main()
