"""
Provides functionality for handling the response format.

Examples:

    If you want to validate a dictionary against the response format::

    >>> from data_formats import response_format
    >>> example = {}
    >>> response_format.validate(example)
    Traceback (most recent call last):
        ...
    data_formats.response_format.ResponseValidationError
"""
from collections import defaultdict
from typing import Dict, Any, Union
import io

import jsonschema
from pyomo.core.base import Param, Var, Model, Constraint, Set
from pyomo.opt import SolverResults

from energy_hub.param_var import ConstantOrVar

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
    """
    Validate the instance against the schema.

    Args:
        instance: The potential instance of the schema

    Raises:
        ValidationError: the instance does not match the schema
    """
    try:
        jsonschema.validate(instance, SCHEMA)
    except jsonschema.ValidationError as exc:
        raise ResponseValidationError from exc


def _to_matrix(matrix: Union[Dict, Any]) -> Union[Dict, Any]:
    """
    Convert a dictionary into a format for pandas's DataFrames.

    Examples:
        >>> _to_matrix({1: 'a', 2: 'b'})
        {1: 'a', 2: 'b'}
        >>> _to_matrix({(1, 1): 'a', (1, 2): 'b', (2, 2): 'c'})
        {1: {1: 'a', 2: 'b'}, 2: {2: 'c'}}

    Args:
        matrix: The dictionary to convert

    Returns:
        The converted dictionary
    """
    if not isinstance(matrix, dict):
        return matrix

    temp = defaultdict(dict)
    for key, value in matrix.items():
        if isinstance(key, tuple):
            key, *rest = key
            rest = tuple(rest)

            # Don't want to recurse on an empty tuple
            if len(rest) == 1:
                rest = rest[0]

            temp[key][rest] = value
        else:
            temp[key] = value

    for key, value in temp.items():
        temp[key] = _to_matrix(value)

    return dict(temp)


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


def _get_constraints(model: Model) -> Dict[str, str]:
    def _to_string(constraint):
        if hasattr(constraint, 'expr'):
            return str(constraint.expr)

        expression = io.StringIO()
        constraint.display(ostream=expression)
        return expression.getvalue()

    return {name: _to_string(constraint)
            for name, constraint in model.__dict__.items()
            if isinstance(constraint, Constraint)}


def _get_sets(model: Model) -> Dict[str, str]:
    return {name: str(set_.data())
            for name, set_ in model.__dict__.items()
            if (isinstance(set_, Set)
                and not (name.endswith('_index')
                         or name.endswith('_index_0')))}


def _get_variable_parameters(model: Model) -> Dict[str, str]:
    return {name: _to_matrix(value.values)
            for name, value in model.__dict__.items()
            if isinstance(value, ConstantOrVar)}


def create_response(results: SolverResults, model: Model) -> Dict[str, Any]:
    """
    Create a new response format dictionary.

    Args:
        results: The results outputed by Pyomo
        model: The model that was used by Pyomo to generate results
    """
    results = results.json_repn()

    solver = results['Solver'][0]

    if 'Solution' in results:
        solution = results['Solution'][1]
    else:
        solution = {'Objective': {'total_cost_objective': {'Value': None}}}

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
            'variables': _get_variables(model),
            'parameters': _get_parameters(model),
            'param_or_var': _get_variable_parameters(model),
            'sets': _get_sets(model),
            'parameters': {},
        }
    }

    validate(result)

    return result
