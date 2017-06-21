import os
from typing import Iterable

import sh


class CheckError(Exception):
    """The CI process detected an error."""


def lint(file: str) -> None:
    print(f"Running pylint on {file}")
    try:
        _ = sh.pylint(file)
    except sh.ErrorReturnCode as exc:
        print(f"Pylint output:\n{exc.stdout.decode('utf-8')}")
        raise CheckError
    else:
        print(f"pylint found no errors in {file}")


def get_files_to_check(directory: str) -> Iterable[str]:
    for file in os.listdir(directory):
        if file.endswith('.py'):
            yield file
        elif os.path.isdir(file):
            for inner_file in get_files_to_check(file):
                yield inner_file


def main() -> None:
    return_code = 0
    print("Running linting process...")
    for file in get_files_to_check('.'):
        try:
            lint(file)
        except CheckError:
            return_code = -1

    exit(return_code)


if __name__ == "__main__":
    main()
