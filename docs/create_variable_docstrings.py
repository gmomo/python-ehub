"""
This is a script that will print out the instance variables of the energy hub
model in Markdown.

To send the output of this script to a file do:

    python create_variable_docstrings.py > variable_docstrings.md

The docstring of the instance variable is NOT usable in the Python interpreter.
There is no such thing as an instance variable docstring. PEP 224, which tried
to introduce such a thing, was rejected.
"""
import re
from typing import Tuple, Iterator


def declaring_instance_variable(line: str, *, level: str = None) -> bool:
    """
    Is this line declaring an instance variable?

    Notes:
        Does not check if this is an assignment.

    Args:
        line: The line
        level: Optional. The type of instance variable to check. Defaults to
            any type. Can be either 'private' or 'public'.

    Returns:
        Whether or not the line is declaring an instance variable

    Examples:
        >>> declaring_instance_variable('self.public = 1')
        True
        >>> declaring_instance_variable('self._private = 1')
        True
        >>> declaring_instance_variable('self.__mangle = 0')
        False
        >>> declaring_instance_variable('x = self.public')
        False
        >>> declaring_instance_variable('self.public = 1', level='private')
        False
        >>> declaring_instance_variable('self._private = 1', level='public')
        False
    """
    line = line.strip()

    is_public = re.match(r'self\.[^_].* = ', line) is not None
    is_private = re.match(r'self\._[^_].* = ', line) is not None

    return {
        'private': is_private,
        'public': is_public,
        None: is_private or is_public,
    }[level]


def declaring_method(line: str) -> bool:
    """
    Is this line declaring a method?

    Args:
        line: A string of the line
    """
    return re.match(r'.*\(self(, \w*)*?\):', line) is not None


def starts_docstring(line: str) -> bool:
    """Does this line start a docstring?"""
    return line.strip().startswith('"""')


def parse_variable(content: str) -> Tuple[str, str]:
    """
    Parse the content to get the first instance variable and its docstring.

    Args:
        content: The content to look in

    Returns:
        A tuple of the name of the instance variable and its docstring
    """
    name_match = re.match(r'self\.(\w*?) =', content)

    name = name_match.group(1)
    docstring = ''

    content_after_name = content[name_match.end():]
    lines = content_after_name.splitlines()
    for i, line in enumerate(lines):
        if declaring_instance_variable(line) or declaring_method(line):
            break
        elif starts_docstring(line):
            content_with_docstring = '\n'.join(lines[i:])
            match = re.match(r'"""((?:.|\n)*?)"""', content_with_docstring)

            docstring = match.group(1).strip()
            break

    return name, docstring


def parse(content: str) -> Iterator[Tuple[str, str]]:
    """
    Return the instance variables and their docstrings in `content`.

    Args:
        content: The content of the file

    Returns:
        An iterator over the names of the instance variables and their
        docstrings.
    """
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if declaring_instance_variable(line, level='public'):
            # To preserve any drawings that use whitespace in docstrings
            indentation_level = re.match(r'\s*?\S', line).end() - 1
            new_lines = [line[indentation_level:] for line in lines[i:]]

            yield parse_variable('\n'.join(new_lines))

    raise StopIteration


def main():
    """The main function of the script."""
    with open('energy_hub/ehub_model.py') as file:
        content = file.read()

    print('# Model Variables')
    print('')
    print('This also doubles as the response format variables.')
    print('')
    for name, docstring in parse(content):
        if docstring:
            print(f'#### `{name}`\n\n{docstring}\n')
        else:
            print(f'#### `{name}`\n\n')


if __name__ == '__main__':
    main()
