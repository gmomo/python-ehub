# Overview of Project

This file contains info on how the project as a whole is structured.
This will mostly look at the folder structure of this repo.

For more specific information on packages/modules, see the package/module
docstring for more info.

## Folder Structure

Quick view:
```
data_formats
  |-- request_format
docs
  |-- install
  |-- tutorials
energy_hub
excel_files
pylp
tests
```

### `data_formats`

Contains files associated with the request and response format.

#### `data_formats/request_format`

Contains all the files associated with the request format, which includes the
wrapper classes.

### `docs`

Contains all the files for external documentation.

Documentation for anything Python related should be in the Python file itself.

#### `docs/install`

Contains files that show how to install and run the energy hub model on various
platforms.

#### `docs/tutorials`

Contains example tutorials for dealing with the energy hub model.

### `energy_hub`

Contains the main source code for the model.

### `excel_files`

Contains excel files for the model.

### `pylp`

Contains files for the PyLP library.

### `tests`

Contains files for the system tests.

It contains the file that runs the tests and all the excel files for use in the
system tests.

## Prominent Files

The following is a list of prominent top-level files.
ie: files in the root directory of the project.

Python files are ignored.
They should have a module docstring describing what they do.

### `config.yaml`

Contains the arguments to the command-line program.
They can be overwritten by command-line arguments.

### `pylintrc`

Contains the style settings for [Pylint](https://www.pylint.org/).

### `requirements.txt`

Contains the libraries the project uses.
They are to be installed by `pip` via:
```bash
python3.6 -m pip install -r requirements.txt
```
