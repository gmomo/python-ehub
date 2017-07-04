"""
Test the EHubModel using a standard test file and it's actual total cost. No
other variables are checked.
"""

import numpy as np

from config import SETTINGS
from energy_hub.ehub_model import EHubModel

TEST_INPUT_FILE = "excel_files/General_input_new_simple.xlsx"
# There is only the total_cost, but there could be more things we can check
# to make sure nothing happens in refactorings.
TEST_OUTPUT = {
    'total_cost': 3444.89158311401,
}

SOLVER = "glpk"
SOLVER_OPTIONS = {
    'mipgap': 0.05,
}


def main():
    """Run the test."""
    model = EHubModel(excel=TEST_INPUT_FILE)

    SETTINGS['solver']['name'] = SOLVER
    SETTINGS['solver']['options'] = SOLVER_OPTIONS

    results = model.solve()

    total_cost = results['solution']['variables']['total_cost']

    assert np.isclose(total_cost, TEST_OUTPUT['total_cost'])

    print("\n\ntest is OK")


if __name__ == "__main__":
    main()
