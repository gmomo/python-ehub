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


def _get_value(value: Any) -> Any:
    if isinstance(value, Variable):
        return value.evaluate()
    elif isinstance(value, range):
        return list(value)
    elif isinstance(value, ConstantOrVar):
        return _get_value(value.values)
    elif isinstance(value, dict):
        return {key: _get_value(value) for key, value in value.items()}

    return value


def _get_stuff(model: Dict) -> Dict[str, Any]:
    return {name: _get_value(value) for name, value in model.items()}


def create_response(status: Status, model: Dict) -> Dict[str, Any]:
    """
    Create a new response format dictionary.

    Args:
        status: The status of the problem
        model: A dictionary of the variables and their values that were used in
            the model
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
