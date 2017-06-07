from contextlib import suppress

from jsonschema import validate, ValidationError
from pyomo.core.base import Param, Var

schema = {
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

# Check that the schema does not contain any errors
# A ValidationError is only thrown when the instance ({}) does not match the
# schema.
with suppress(ValidationError):
    validate({}, schema)


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

        num_rows = max(keys, key=lambda t: t[0])[0]
        num_columns = max(keys, key=lambda t: t[1])[1]

        matrix = [[0] * num_columns for _ in range(num_rows)]

        for index, value in var.items():
            x = index[0] - 1
            y = index[1] - 1

            matrix[x][y] = value

        return matrix
    else:
        raise NotImplemented


def get_variables(model):
    variables = {k: v for k, v in model.__dict__.items()
                 if isinstance(v, Var)}

    for key, var in variables.items():
        if hasattr(var, 'value'):
            var = var.value
        else:
            var = var.get_values()
            var = to_matrix(var)

        variables[key] = var

    return variables


def get_parameters(model):
    parameters = {k: v for k, v in model.__dict__.items()
                  if isinstance(v, Param)}

    for key, var in parameters.items():
        if hasattr(var, 'value'):
            var = var.value
        else:
            var = var.extract_values()
            var = to_matrix(var)

        parameters[key] = var

    return parameters


def create_response(results, model):
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
                'total_cost': solution['Objective']['Total_Cost']['Value'],
            },
            'variables': {},
        }
    }

    variables = get_variables(model)
    for key, value in variables.items():
        result['solution']['variables'][key] = value

    validate(result, schema)

    return result
