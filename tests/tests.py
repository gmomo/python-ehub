"""
This module contains all the tests.

This file must be called via

    python3.6 -m tests.tests

from the root directory.
"""
import os
import io
from contextlib import redirect_stdout
import functools

from run import create_logger
from energy_hub import EHubModel


def test(excel_file):
    """
    A function decorator for a test method.

    The method will be passed the results of solving the model specified in
    excel_file.

    Args:
        excel_file: The file to test

    Returns:
        The decorated method
    """
    def _decorator(func):
        func.is_test = True

        @functools.wraps(func)
        def _wrapper():
            current_directory = os.path.dirname(os.path.realpath(__file__))
            excel = os.path.join(current_directory, excel_file)

            model = EHubModel(excel=excel)

            glpk_output = io.StringIO()
            # Don't want to clutter the stdout
            with redirect_stdout(glpk_output):
                results = model.solve()

            func(results)

        return _wrapper
    return _decorator


# Tests' names can be more verbose than usual
# pylint: disable=invalid-name
class Tests:
    """
    The class that holds all the tests
    """

    @staticmethod
    @test('chp.xlsx')
    def simple_chp(results):
        """Ensure a simple CHP converter works."""
        variables = results['solution']['variables']

        assert variables['Grid'] == 0  # Don't use any Grid

        energy_imported = variables['energy_imported']
        for t in range(0, 4):
            assert energy_imported[t]['CHP'] == 50

    @staticmethod
    @test('elec_and_heat_demands.xlsx')
    def elec_and_heat_demands(results):
        """Ensure that we can have multiple demand streams."""
        variables = results['solution']['variables']

        energy_imported = variables['energy_imported']
        for t in range(0, 4):
            assert energy_imported[t]['PV'] == 50
            assert energy_imported[t]['Boiler'] == 50
            assert energy_imported[t]['Grid'] == 0

        assert variables['total_cost'] == 1039

    @staticmethod
    @test('pv.xlsx')
    def ensure_pv_works(results):
        """Ensure that PV works."""
        variables = results['solution']['variables']

        energy_imported = variables['energy_imported']
        for t in range(0, 4):
            assert energy_imported[t]['PV'] == 50
            assert energy_imported[t]['Grid'] == 0

        assert variables['total_cost'] == 17832.5

    @staticmethod
    @test('fixed_capital_costs.xlsx')
    def ensure_fixed_capital_costs_are_added(results):
        """Ensure there are fixed capital costs."""
        parameters = results['solution']['parameters']

        assert parameters['FIXED_CAPITAL_COSTS']['PV'] == 100

    @staticmethod
    @test('storage.xlsx')
    def ensure_storage_works(results):
        """Ensure that storages work."""
        variables = results['solution']['variables']

        storage_level = variables['storage_level']
        battery = 'Battery'

        storage_levels = [0, 50, 100, 50, 0]
        for t, level in enumerate(storage_levels):
            assert storage_level[t][battery] == level

        assert variables['total_cost'] == 17818.5

    def run(self):
        """Run all the tests."""
        methods = [getattr(self, method)
                   for method in dir(self)
                   if callable(getattr(self, method))]
        tests = (test_ for test_ in methods if hasattr(test_, 'is_test'))

        for test_ in tests:
            try:
                test_()
            except AssertionError as exc:
                print(f"TEST {test_.__name__} FAILED")

                raise exc from None

        print("ALL TESTS PASSED")


if __name__ == "__main__":
    # Makes it easier to read logs from both sides
    create_logger('test_logs.log')

    Tests().run()
