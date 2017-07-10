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
        _ = subprocess.check_output(['pylint', file])
    except subprocess.CalledProcessError as exc:
        pylint_output = exc.stdout.decode('utf-8')

        raise CheckError(pylint_output)


def get_files_to_check(directory: str) -> Iterable[str]:
    """
    Iterate over the files to check in the directory.

    Args:
        directory: The directory to check files in

    Returns:
        An iterator over the Python files
    """
    for file in os.listdir(directory):
        # Don't show the '.'.  It's noise.
        if directory != '.':
            file = os.path.join(directory, file)

        if file.endswith('.py'):
            yield file
        elif os.path.isdir(file):
            inner_directory = file

            for inner_file in get_files_to_check(inner_directory):
                yield inner_file


def main() -> None:
    """The main function that runs the script."""
    return_code = 0
    print("Running linting process...")
    for file in get_files_to_check('.'):
        try:
            lint(file)
        except CheckError as exc:
            print(exc)
            return_code = -1

    print("Running tests...")
    result = subprocess.run(['python3.6', '-m', 'tests.tests'])
    if result.returncode != 0:
        exit(result.returncode)

    exit(return_code)


if __name__ == "__main__":
    main()
