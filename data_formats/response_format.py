from contextlib import suppress

from jsonschema import validate, ValidationError
from pyomo.core.base import Param, Var

schema = {
    'type': 'object',
    'properties': {
        'version': {
            'description': 'The SemVar version number for the format',
            'type': 'string',
            'enum': ['0.1.0'],
        },
        'solution': {
            'type': 'object',
            'properties': {
                'total_cost': {
                    'type': 'number',
                },
            },
            'required': ['total_cost'],
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

# Check that the schema does not contain any errors
# A ValidationError is only thrown when the instance ({}) does not match the
# schema.
with suppress(ValidationError):
    validate({}, schema)


def create_response(results, model):
    results = results.json_repn()

    solver = results['Solver'][0]
    solution = results['Solution'][1]

    parameters = {k: v.extract_values() for k, v in model.__dict__.items()
                  if isinstance(v, Param)}

    variables = {k: v for k, v in model.__dict__.items()
                 if isinstance(v, Var)}

    for key, var in variables.items():
        if hasattr(var, 'value'):
            var = var.value
        else:
            var = var.get_values()

        variables[key] = var

    result = {
        'version': '0.1.0',
        'solver': {
            'status': solver['Status'],
            'termination_condition': solver['Termination condition'],
            'time': solver['Time'],
        },
        'solution': {
            'total_cost': solution['Objective']['Total_Cost']['Value'],
        }
    }

    validate(result, schema)

    return result
