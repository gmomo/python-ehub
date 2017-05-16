PyHub
=====

A program to solve a energy hub model in Python.


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
git clone https://<username>@bitbucket.org/hues/pyhub.git
```

Install the libraries needed for PyHub to run:
```
sudo pip3 install -r requirements.txt
```

Also install glpk or another solver.
Edit the `config.yaml` file to use a selected solver.

Run the `cli.py` script to see if everything works.
```
python3 cli.py
```

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
