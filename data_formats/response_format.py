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
from contextlib import suppress
from typing import Dict, Any, Union

import jsonschema

from energy_hub.param_var import ConstantOrVar
from pylp import Variable, Status

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
        },
        'solver': {
            'type': 'object',
            'properties': {
                'termination_condition': {
                    'type': 'string',
                },
                'time': {
                    'type': 'number',
                    'minimum': 0,
                },
            },
            'required': ['termination_condition', 'time'],
            'additionalProperties': False,
        },
    },
    'required': ['version', 'solution', 'solver'],
    'additionalProperties': False,
}


class ResponseValidationError(Exception):
    """The instance failed to validate against the SCHEMA."""


def _is_valid_json_type(json: Any) -> bool:
    if json is None:
        return True

    return any(isinstance(json, t) for t in [str, float, int, dict, list])


def _is_valid(mapping: Union[dict, list, str, float, int]) -> bool:
    if isinstance(mapping, list):
        return all(_is_valid(x) for x in mapping)
    elif isinstance(mapping, dict):
        return all(_is_valid(key) and _is_valid(value)
                   for key, value in mapping.items())

    return _is_valid_json_type(mapping)


def validate(instance: dict) -> None:
    """
    Validate the instance against the schema.

    Args:
        instance: The potential instance of the schema

    Raises:
        ValidationError: the instance does not match the schema
    """
    if not _is_valid(instance):
        raise ResponseValidationError

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
        # Some values might be variable so get their actual value
        with suppress(AttributeError):
            matrix = matrix.evaluate()

        return matrix

    temp = defaultdict(dict)
    for key, value in matrix.items():
        # Some values might be variable so get their actual value
        with suppress(AttributeError):
            value = value.evaluate()

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


def _get_stuff(model: Dict) -> Dict[str, Any]:
    result = {}
    for name, value in model.items():
        if isinstance(value, dict):
            result[name] = _to_matrix(value)
        elif isinstance(value, range):
            result[name] = list(value)
        elif isinstance(value, Variable):
            result[name] = value.evaluate()
        elif isinstance(value, ConstantOrVar):
            result[name] = _to_matrix(value.values)
        else:
            result[name] = value

    return result


def create_response(status: Status, model: Dict) -> Dict[str, Any]:
    """
    Create a new response format dictionary.

    Args:
        status: The status of the problem
        model: The model that was used by Pyomo to generate results
    """
    result = {
        'version': '0.1.0',
        'solver': {
            'termination_condition': status.status,
            'time': status.time,
        },
        'solution': _get_stuff(model),
    }

    validate(result)

    return result
