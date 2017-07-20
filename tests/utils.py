"""
Contains utilities for testing.
"""
import os
import functools

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

            results = model.solve(is_verbose=False)

            func(results)

        return _wrapper
    return _decorator


def test_will_fail(excel_file):
    """
    A test that will not have a solution.

    Args:
        excel_file: The file to test

    Returns:
        The decorated method
    """
    def _decorator(func):
        @test(excel_file)
        @functools.wraps(func)
        def _wrapper(results):
            assert results['solver']['termination_condition'] == 'infeasible'

        return _wrapper
    return _decorator
