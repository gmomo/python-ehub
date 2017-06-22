"""
Provides functionality for handling the response format.

Examples:

    If you want to validate a dictionary against the response format::

    >>> from data_formats import response_format
    >>> example = {}
    >>> response_format.validate(example)
    Traceback (most recent call last):
        ...
    data_formats.response_format.ValidationError
"""

from typing import Dict, Any, List, Union

import jsonschema
from pyomo.core.base import Param, Var, Model
from pyomo.opt import SolverResults

SCHEMA = {
    'type': 'object',
    'properties': {
        'version': {
            'description': 'The SemVer version number for the format',
            'type': 'string',
            'enum': ['0.1.0'],
        },
        'solution': {
            'type': 'object',
            'properties': {
                'objective': {
                    'type': 'object',
                    'properties': {},
                    'additionalProperties': True,
                },
                'variables': {
                    'type': 'object',
                    'properties': {},
                    'additionalProperties': True,
                },
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'additionalProperties': True,
                },
                'constraints': {},
            },
            'required': ['objective', 'variables'],
        },
        'solver': {
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                },
                'termination_condition': {
                    'type': 'string',
                },
                'time': {
                    'type': 'number',
                },
            },
            'required': ['status', 'termination_condition', 'time'],
            'additionalProperties': False,
        },
    },
    'required': ['version', 'solution', 'solver'],
    'additionalProperties': False,
}


class ResponseValidationError(Exception):
    """The instance failed to validate against the SCHEMA."""


def validate(instance: dict) -> None:
    """Validate the instance against the schema.

    Args:
        instance: The potential instance of the schema

    Raises:
        ValidationError: the instance does not match the schema
    """
    try:
        jsonschema.validate(instance, SCHEMA)
    except jsonschema.ValidationError:
        raise ResponseValidationError from None


def _to_matrix(var: Any) -> Union[List[Any], List[List[Any]]]:
    # Determine the dimension of the matrix
    try:
        dim = len(list(var.keys())[0])
    except TypeError:
        dim = 1

    if dim == 1:
        return list(var.values())
    elif dim == 2:
        keys = var.keys()

        num_rows = max(keys, key=lambda t: t[0])[0]
        num_columns = max(keys, key=lambda t: t[1])[1]

        matrix = [[0] * num_columns for _ in range(num_rows)]

        for index, value in var.items():
            row = index[0] - 1
            col = index[1] - 1

            matrix[row][col] = value

        return matrix
    else:
        raise NotImplementedError


def _get_value(attribute: Union[Var, Param]) -> Any:
    if hasattr(attribute, 'value'):
        return attribute.value
    elif hasattr(attribute, 'get_values'):
        return _to_matrix(attribute.get_values())
    elif hasattr(attribute, 'extract_values'):
        return _to_matrix(attribute.extract_values())

    return None


def _get_variables(model: Model) -> Dict[str, Any]:
    return {name: _get_value(variable)
            for name, variable in model.__dict__.items()
            if isinstance(variable, Var)}


def _get_parameters(model: Model) -> Dict[str, Any]:
    return {name: _get_value(parameter)
            for name, parameter in model.__dict__.items()
            if isinstance(parameter, Param)}


def create_response(results: SolverResults, model: Model) -> Dict[str, Any]:
    """Create a new response format dictionary.

    Args:
        results: The results outputed by Pyomo
        model: The model that was used by Pyomo to generate results
    """
    results = results.json_repn()

    solver = results['Solver'][0]
    solution = results['Solution'][1]

    result = {
        'version': '0.1.0',
        'solver': {
            'status': solver['Status'],
            'termination_condition': solver['Termination condition'],
            'time': solver['Time'],
        },
        'solution': {
            'objective': {
                'total_cost': solution['Objective']['total_cost_objective']['Value'],
            },
            'variables': {},
        }
    }

    variables = _get_variables(model)
    for key, value in variables.items():
        result['solution']['variables'][key] = value

    validate(result)

    return result
