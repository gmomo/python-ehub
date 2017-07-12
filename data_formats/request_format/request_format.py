"""
Provides functionality for handling the request format.

Examples:

    If you want to validate a dictionary against the request format::

    >>> from data_formats import request_format
    >>> example = {}
    >>> request_format.validate(example)
    Traceback (most recent call last):
        ...
    data_formats.request_format.request_format.RequestValidationError
"""
import jsonschema

SCHEMA = {
    'title': 'EHub Model Request Format',
    'description': 'A JSON Schema used to validate an incoming request to '
                   'solve a model',
    'type': 'object',
    'properties': {
        'version': {
            'description': 'The SemVar version number for the format',
            'type': 'string',
            'enum': ['0.1.0'],
        },
        'general': {
            'type': 'object',
            'properties': {
                'interest_rate': {
                    'type': 'number',
                    'minimum': 0,
                },
                'constraints': {
                    'description': 'A list of extra constraints',
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                },
            },
            'required': ['interest_rate'],
            'additionalProperties': False,
        },
        'capacities': {
            'description': 'A list of capacities a converter or storage can '
                           'have',
            'type': 'array',
            'items': {
                'description': 'A specific capacity',
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                    },
                    'units': {
                        'type': 'string',
                    },
                    'type': {
                        'type': 'string',
                        'enum': ['Binary', 'Integer', 'List', 'Continuous'],
                    },
                    'options': {
                        'anyOf': [
                            {
                                'type': 'null',
                            },
                            {
                                'type': 'array',
                                'items': {
                                    'type': 'number',
                                },
                            },
                        ],
                    },
                    'bounds': {
                        'type': 'object',
                        'properties': {
                            'lower': {
                                'type': 'number',
                            },
                            'upper': {
                                'type': 'number',
                            },
                        },
                        'additionalProperties': False,
                    },
                },
                'required': ['name', 'type'],
                'additionalProperties': False,
            },
        },
        'streams': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                    },
                    'availability': {
                        'type': 'string',
                    },
                    'price': {
                        'anyOf': [
                            {
                                'type': 'number',
                                'minimum': 0,
                            },
                            {
                                'description': 'A reference to a time series',
                                'type': 'string',
                            },
                        ],
                    },
                    'export_price': {
                        'type': 'number',
                        'minimum': 0,
                    },
                    'co2': {
                        'type': 'number',
                        'minimum': 0,
                    },
                },
                'required': ['name', 'price', 'export_price', 'co2'],
                'additionalProperties': False,
            },
        },
        'converters': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                    },
                    'capacity': {
                        'anyOf': [
                            {
                                'description': 'A reference to a capacity',
                                'type': 'string',
                                'default': '',
                            },
                            {
                                'type': 'number',
                                'minimum': 0,
                            },
                        ],
                    },
                    'fixed_capital_cost': {
                        'type': 'number',
                        'minimum': 0,
                        'default': 0,
                    },
                    'capital_cost': {
                        'type': 'number',
                        'minimum': 0,
                        'default': 0,
                    },
                    'annual_maintenance_cost': {
                        'type': 'number',
                        'minimum': 0,
                    },
                    'usage_maintenance_cost': {
                        'type': 'number',
                    },
                    'efficiency': {
                        'type': 'number',
                    },
                    'lifetime': {
                        'type': 'number',
                    },
                    'output_ratio': {
                        'type': 'number',
                    },
                    'min_load': {
                        'type': 'number',
                    },
                    'inputs': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                    'outputs': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                },
                'additionalProperties': False,
            },
        },
        'storages': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                    },
                    'stream': {
                        'type': 'string',
                    },
                    'capacity': {
                        'anyOf': [
                            {
                                'description': 'A reference to a capacity',
                                'type': 'string',
                            },
                            {
                                'type': 'number',
                                'minimum': 0,
                            },
                        ],
                    },
                    'cost': {
                        'type': 'number',
                        'minimum': 0,
                    },
                    'lifetime': {
                        'type': 'number',
                        'minimum': 0,
                    },
                    'charge_efficiency': {
                        'type': 'number',
                    },
                    'discharge_efficiency': {
                        'type': 'number',
                    },
                    'decay': {
                        'type': 'number',
                    },
                    'max_charge': {
                        'type': 'number',
                    },
                    'max_discharge': {
                        'type': 'number',
                    },
                    'min_state': {
                        'type': 'number',
                    },
                },
                'additionalProperties': False,
            },
        },
        'system_types': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                    },
                    'technologies': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                },
                'additionalProperties': False,
            },
        },
        'time_series': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'string',
                    },
                    'type': {
                        'type': 'string',
                        'enum': ['Demand', 'Source', 'Price'],
                    },
                    'stream': {
                        'type': 'string',
                    },
                    'node': {
                        'anyOf': [
                            {
                                'description': 'A reference to a network node',
                                'type': 'integer',
                            },
                            {
                                'type': 'null',
                            },
                        ],
                    },
                    'units': {
                        'type': 'string',
                    },
                    'source': {
                        'type': 'null',
                    },
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'number',
                        },
                    },
                },
                'additionalProperties': False,
            },
        },
        'network': {
            'type': 'object',
            'properties': {
                'nodes': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {
                                'type': 'number',
                            },
                            'coords': {
                                'type': 'object',
                                'properties': {
                                    'latitude': {
                                        'type': 'number',
                                    },
                                    'longitude': {
                                        'type': 'number',
                                    },
                                    'x': {
                                        'type': 'number',
                                    },
                                    'y': {
                                        'type': 'number',
                                    },
                                },
                                'dependencies': {
                                    'latitude': ['longitude'],
                                    'longitude': ['latitude'],
                                    'x': ['y'],
                                    'y': ['x'],
                                },
                                'additionalProperties': False,
                            },
                            'building': {
                                'type': 'object',
                                'properties': {
                                    'id': {
                                        'type': 'integer',
                                    },
                                    'type': {
                                        'type': 'string',
                                    },
                                },
                                'additionalProperties': False,
                            },
                            'system': {
                                'type': 'object',
                                'properties': {
                                    'id': {
                                        'type': 'integer',
                                    },
                                    'type': {
                                        'description': 'A reference to a '
                                                       'system in the system '
                                                       'types',
                                        'type': 'string',
                                    },
                                },
                                'additionalProperties': False,
                            },
                        },
                        'additionalProperties': False,
                    },
                },
                'links': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {
                                'type': 'integer',
                            },
                            'start_id': {
                                'description': 'A reference to a network node',
                                'type': 'integer',
                            },
                            'end_id': {
                                'description': 'A reference to a network node',
                                'type': 'integer',
                            },
                            'type': {
                                'type': 'string',
                            },
                            'length': {
                                'type': 'number',
                            },
                            'capacity': {
                                'type': 'number',
                            },
                            'voltage': {
                                'type': 'number',
                            },
                            'electrical_resistance': {
                                'type': 'number',
                            },
                            'electrical_reactance': {
                                'type': 'number',
                            },
                            'total_thermal_loss': {
                                'type': 'number',
                            },
                            'total_pressure_loss': {
                                'type': 'number',
                            },
                            'operating_temperature': {
                                'type': 'number',
                            },
                        },
                        'additionalProperties': False,
                    },
                },
            },
            'required': ['nodes', 'links'],
            'additionalProperties': False,
        },
    },
    'required': ['version', 'general', 'capacities', 'streams', 'converters',
                 'storages', 'system_types', 'time_series'],
    'additionalProperties': False,
}


class RequestValidationError(Exception):
    """The request format instance failed to validate against the SCHEMA."""


def validate(instance: dict) -> None:
    """Validate the instance against the schema.

    Args:
        instance: The potential instance of the schema

    Raises:
        ValidationError: the instance does not match the schema
    """
    try:
        jsonschema.validate(instance, SCHEMA)
    except jsonschema.ValidationError as exc:
        raise RequestValidationError from exc
