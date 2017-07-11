PyHub
=====

A program to solve a energy hub model in Python.

Requirements
------------

- Python 3.6.1
- pip for Python 3.6.1
- `glpk` or another solver supported by Pyomo

Running a Model
---------------

To run a energy hub model, use the `General_input.xlsx` file to enter your data.
The data **must** be in the same format.

Check the `config.yaml` file to see if the input file and output file is where
you want to load and output the results of the model respectively.

While inside the `config.yaml` file, be sure to set the settings for using a
specific solver that is installed on your system.
The default one is `glpk` with some options, but you can set it to any other
solver that is supported by Pyomo.

Once you have configured the `config.yaml` file, run:
```
python cli.py
```
to solve the model.
The results should be in the file you specified in `config.yaml`.

Development
-----------

### Installation

To install PyHub, make a new directory and then `cd` into it.
```
mkdir pyhub
cd pyhub
```

Download the repo:
```
git clone https://github.com/hues-platform/python-ehub.git
```

Install the libraries needed for PyHub to run:
```
pip install -r requirements.txt
```

Also install glpk or another solver.
Edit the `config.yaml` file to use a selected solver.

Run the `cli.py` script to see if everything works.
```
python cli.py
```

### Docs

Can be found [here](docs/explanation.md).

Contributing
------------

### Features/Bug fixes

If you are fixing a bug or making a new feature, first get the lastest master branch.
```
git checkout master
git pull
```

Then create your own branch for you to work on:
```
git branch <your-branch-name>
git checkout <your-branch-name>
```

Once you are done, please submit a pull request.


