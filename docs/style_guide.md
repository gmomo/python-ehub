# Style Guide

Follow PEP 8 guidelines unless otherwise noted below.

Run `python3.6 ci.py` in order to run all the tests and check for any style
problems.

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


