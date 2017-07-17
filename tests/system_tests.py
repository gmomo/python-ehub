"""
This module contains all the tests.

This file must be called via

    python3.6 -m tests.system_tests

from the root directory.
"""
from run import create_logger
from tests.utils import test


# Tests' names can be more verbose than usual
# pylint: disable=invalid-name
class Tests:
    """
    The class that holds all the tests
    """

    @staticmethod
    @test('storages_of_same_type.xlsx')
    def storage_of_same_type_both_used(results):
        """Ensure that multiple storages that hold the same stream are all
        used."""
        variables = results['solution']

        assert variables['Grid'] == 0
        assert variables['income_from_exports'] == 0

        for t in [1, 2]:
            assert variables['energy_imported'][t]['PV'] == 50

        assert variables['storage_level'][3]['LeftBattery'] == 50
        assert variables['storage_level'][2]['RightBattery'] == 50

        assert variables['energy_from_storage'][3]['RightBattery'] == 50
        assert variables['energy_from_storage'][4]['LeftBattery'] == 50

        assert variables['storage_level'][5]['LeftBattery'] == 0
        assert variables['storage_level'][5]['RightBattery'] == 0

        assert variables['total_carbon'] == 0
        assert variables['total_cost'] == 17832.5

    @staticmethod
    @test('storage_looping.xlsx')
    def ensure_storage_levels_loop(results):
        """Ensure that the storage level can transfer levels from the end to
        beginning."""
        variables = results['solution']

        assert variables['Grid'] == 0
        assert variables['income_from_exports'] == 0

        assert variables['energy_imported'][3]['PV'] == 50
        assert variables['energy_to_storage'][3]['Battery'] == 50
        assert variables['storage_level'][4]['Battery'] == 50

        assert variables['storage_level'][0]['Battery'] == 50
        assert variables['energy_from_storage'][0]['Battery'] == 50

        assert variables['total_cost'] == 17832.5

    @staticmethod
    @test('storage_export_start.xlsx')
    def no_exporting_from_storage_on_first_time_step_with_no_demands(results):
        """Ensures that no energy is taken from a storage and immediately
        exported on the first time step when there is no energy in the
        storage."""
        variables = results['solution']
        parameters = results['solution']

        for t in range(0, 3):
            assert parameters['LOADS'][t]['Elec'] == 0
            assert variables['energy_from_storage'][t]['Battery'] == 0

        assert variables['income_from_exports'] == 0
        assert variables['total_cost'] == 0

    @staticmethod
    @test('chp.xlsx')
    def simple_chp(results):
        """Ensure a simple CHP converter works."""
        variables = results['solution']

        assert variables['Grid'] == 0  # Don't use any Grid

        energy_imported = variables['energy_imported']
        for t in range(0, 4):
            assert energy_imported[t]['CHP'] == 50

    @staticmethod
    @test('elec_and_heat_demands.xlsx')
    def elec_and_heat_demands(results):
        """Ensure that we can have multiple demand streams."""
        variables = results['solution']

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
        variables = results['solution']

        energy_imported = variables['energy_imported']
        for t in range(0, 4):
            assert energy_imported[t]['PV'] == 50
            assert energy_imported[t]['Grid'] == 0

        assert variables['income_from_exports'] == 0
        assert variables['total_cost'] == 17832.5

    @staticmethod
    @test('fixed_capital_costs.xlsx')
    def ensure_fixed_capital_costs_are_added(results):
        """Ensure there are fixed capital costs."""
        parameters = results['solution']

        assert parameters['FIXED_CAPITAL_COSTS']['PV'] == 100

    @staticmethod
    @test('storage.xlsx')
    def ensure_storage_works(results):
        """Ensure that storages work."""
        variables = results['solution']

        storage_level = variables['storage_level']
        battery = 'Battery'

        storage_levels = [0, 0, 50, 100, 50, 0]
        for t, level in enumerate(storage_levels):
            assert storage_level[t][battery] == level

        assert variables['income_from_exports'] == 0
        assert variables['total_cost'] == 17832.5

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
