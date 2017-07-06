"""
A script for running as part of a CI system.

It currently only runs Pylint on any `.py` files in the directory. Pylint
checks for style and some common errors. See the `.pylintrc` file for Pylint
config options. If you have an objection with the style, make a PR to change
it.

To run the script, just do:

    $ python3.6 ci.py

in the same directory as `ci.py`.

Returns:
    A standard error code: 0 for success, non-zero for failure
"""
import os
import subprocess
from typing import Iterable

import sh


class CheckError(Exception):
    """The CI process detected an error."""


def lint(file: str) -> None:
    """
    Call pylint on a file.

    Args:
        file: The relative path of the file to `ci.py`
    """
    print(f"Running pylint on {file}")
    try:
        _ = sh.pylint(file)
    except sh.ErrorReturnCode as exc:
        print(f"Pylint output:\n{exc.stdout.decode('utf-8')}")
        raise CheckError
    else:
        print(f"pylint found no errors in {file}")


def get_files_to_check(directory: str) -> Iterable[str]:
    """
    Iterate over the files to check in the directory.

    Args:
        directory: The directory to check files in

    Returns:
        An iterator over the Python files
    """
    for file in os.listdir(directory):
        if file.endswith('.py'):
            yield file
        elif os.path.isdir(file):
            for inner_file in get_files_to_check(file):
                yield file + '/' + inner_file


def main() -> None:
    """The main function that runs the script."""
    return_code = 0
    print("Running linting process...")
    for file in get_files_to_check('.'):
        try:
            lint(file)
        except CheckError:
            return_code = -1

    print("Running tests...")
    result = subprocess.run(['python3.6', '-m', 'tests.tests'])
    if result.returncode != 0:
        print("TESTS FAILED")
        exit(result.returncode)
    else:
        print("TESTS PASSED")

    exit(return_code)


if __name__ == "__main__":
    main()
