# Style Guide

Follow PEP 8 guidelines unless otherwise noted below.

`pylint` also is a good way to ensure that code is up to the style guidelines.
You can run `ci.py` to run `pylint` on all files as well as tests.

## Docstrings

Docstrings should follow the Google Python docstring format.
An example of it is [here](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).

Note: Instead of saying the type in the docstring, add a type hint to the 
method/function.
This is picked up by PyCharm and allows better code completion and error 
linting. 

## Line length

Preferably stay within 80 characters but don't stress too much about it.
Going over it a little is fine but anything close to 100 or more is a sign you
are doing too much on one line.


