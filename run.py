"""
The CLI for the EHub Model.

The options for running the model are set in the `config.yaml` file or as
command-line arguments. See the `config.yaml` file for more information about
the `yaml` format.

Given the config.yaml file, solving the model is easy:

    $ python3.6 run.py

The program will then print out the output of whatever solver is configured in
the config.yaml file and then the solved variables, parameters, constraints,
etc..

If you want to learn how to use `run.py` as a command-line tool, run

    $ python3.6 run.py -h

to learn more about the arguments.

Note: You can use both the `config.yaml` and the command-line arguments
together in certain situations.
"""
import argparse
from collections import OrderedDict
from contextlib import redirect_stdout
from typing import Union
import logging

import pandas as pd
import yaml

from energy_hub import EHubModel


DEFAULT_CONFIG_FILE = 'config.yaml'
DEFAULT_LOG_FILE = 'logs.log'


def main():
    """The main function for the CLI."""
    create_logger(DEFAULT_LOG_FILE)

    arguments = get_command_line_arguments()
    settings = parse_arguments(arguments)

    model = EHubModel(excel=settings['input_file'])

    results = model.solve(settings['solver'], is_verbose=settings['verbose'])

    if not settings['quiet']:
        pretty_print(results)

    with open(settings['output_file'], 'w') as file:
        with redirect_stdout(file):
            pretty_print(results)


def get_command_line_arguments() -> dict:
    """
    Get the arguments from the command-line and return them as a dictionary.

    Returns:
        A dictionary holding all the arguments
    """
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet', help='Suppresses all output',
                       action='store_true', dest='is_quiet')
    group.add_argument('-v', '--verbose', help='Output everything',
                       action='store_true', dest='is_verbose')

    parser.add_argument('--model', help='The Excel file of the model to solve',
                        dest='input_file')
    parser.add_argument('--config',
                        help=f'The path to the config file to use. Defaults '
                             f'to `{DEFAULT_CONFIG_FILE}` in the current '
                             f'directory. This is only used if the relevant '
                             f'command-line argument is not given.',
                        default=DEFAULT_CONFIG_FILE, dest='config_file')
    parser.add_argument('--output', help='The file to output the results in',
                        dest='output_file')
    parser.add_argument('--solver', help='The solver to use',
                        choices=['glpk', 'cplex'], dest='solver')
    parser.add_argument('--solver_options', help='The rest of the arguments '
                                                 'are arguments to the solver',
                        action='store_true')

    known, unknown = parser.parse_known_args()

    if not known.solver_options and unknown:
        raise ValueError('Unknown arguments. Must specify `--solver_options` '
                         'to allow extra arguments.')

    known = known.__dict__
    known['unknown'] = {}
    for key, value in zip(unknown[::2], unknown[1::2]):
        key = key.split('--')[-1]

        if key not in known['unknown']:
            known['unknown'][key] = value
        else:
            raise ValueError

    # Combine two dictionaries into one
    return known


def parse_arguments(arguments: dict) -> dict:
    """
    Parse the command-line arguments along with the config file.

    Args:
        arguments: The dictionary containing the command-line arguments

    Returns:
        A dictionary with the command-line arguments combined with the config
        file's settings
    """
    with open(arguments['config_file'], 'r') as file:
        config_settings = yaml.safe_load(file)

    if not arguments['input_file']:
        input_file = config_settings['input_file']
    elif arguments['input_file']:
        input_file = arguments['input_file']
    else:
        raise ValueError('Must specify a model to solve')

    if arguments['output_file']:
        output_file = arguments['output_file']
    else:
        output_file = config_settings['output_file']

    if arguments['solver']:
        solver_name = arguments['solver']
    else:
        solver_name = config_settings['solver']['name']

    if arguments['solver_options']:
        solver_options = arguments['unknown']
    else:
        solver_options = config_settings['solver']['options']

    return {
        'input_file': input_file,
        'output_file': output_file,
        'verbose': arguments['is_verbose'],
        'quiet': arguments['is_quiet'],
        'solver': {
            'name': solver_name,
            'options': solver_options,
        },
    }


def pretty_print(results: dict) -> None:
    """Print the results in a prettier format.

    Args:
        results: The results dictionary to print
    """
    version = results['version']
    solver = results['solver']

    print("Version: {}".format(version))

    print("Solver")
    print(f"\ttermination condition: {solver['termination_condition']}")
    print(f"\ttime: {solver['time']}")

    print("Solution")
    print_section('Stuff', results['solution'])


def print_section(section_name: str, solution_section: dict) -> None:
    """
    Print all the attributes with a heading.

    Args:
        section_name: The heading
        solution_section: The dictionary with all the attributes
    """
    half_heading = '=' * 10
    print(f"\n{half_heading} {section_name} {half_heading}")

    attributes = OrderedDict(sorted(solution_section.items()))
    for name, value in attributes.items():
        if isinstance(value, dict):
            value = sort_dict(value)
            value = pd.DataFrame.from_dict(value, orient='index')

            # To remove confusion on what the column '0' means
            if list(value.columns) == [0]:
                value.columns = [name]

            # Make wide matrices fit on the screen
            num_rows, num_columns = value.shape
            if num_columns > num_rows:
                value = value.T

        print(f"\n{name}: \n{value}")


def sort_dict(mapping: Union[dict, OrderedDict]) -> OrderedDict:
    """
    Sorts a dictionary and all its sub-dicionaries as well.

    Examples:
        >>> sort_dict({1: 'a', 3: 'c', 2: 'b'})
        OrderedDict([(1, 'a'), (2, 'b'), (3, 'c')])
        >>> sort_dict({1: {3: 'c', 2: 'b', 1: 'a'}})
        OrderedDict([(1, OrderedDict([(1, 'a'), (2, 'b'), (3, 'c')]))])

    Args:
        mapping: The dictionary to be sorted

    Returns:
        The sorted dictionary as an OrderedDict
    """
    if not isinstance(mapping, dict):
        return mapping

    for key, value in mapping.items():
        mapping[key] = sort_dict(value)

    return OrderedDict(sorted(mapping.items()))


def create_logger(filename: str) -> None:
    """
    Add logging to the application.

    Args:
        filename: The name of the log file
    """
    # logging accepts all logs, which are then handled later
    logging.getLogger().setLevel(logging.DEBUG)

    add_console_handler()
    add_file_handler(filename)


def add_console_handler() -> None:
    """Add a logging handler for stderr."""
    # stderr
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(get_default_formatter())

    logging.getLogger().addHandler(console_handler)


def add_file_handler(filename: str) -> None:
    """
    Add a logging handler for a log file.

    Args:
        filename: The name of the log file
    """
    file_handler = logging.FileHandler(filename, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(get_default_formatter())

    logging.getLogger().addHandler(file_handler)


def get_default_formatter() -> logging.Formatter:
    """
    Return a default formatter for logging.

    The format is:
        Hours:Minutes:Second.Milliseconds - Location - [level]: message

    Returns:
        A logging.Formatter for the default format
    """
    return logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(filename)s:%(lineno)d - '
        '[%(levelname)s]: %(message)s',
        datefmt='%H:%M:%S'
    )


if __name__ == "__main__":
    main()
