# Documentation

## User Installation

A tutorial on how to install on Linux-based systems can be found
[here](install/linux.sh).

## Command-line Usage

```bash
python3.6 cli.py --help
```

Also, look at the top of the [cli.py](../cli.py) file for more up-to-date 
details.

## How to run a Model

Given that you have a proper Excel file, first edit the `config.yaml` file to
point to your file. See the `config.yaml` for more details.

Once the `config.yaml` is correctly configured, all you have to do is run:
```bash
python3.6 cli.py
```

This will print out the results to the command line and also put the results in
the output file specified in the `config.yaml` file.

## Glossary

A glossary of terms can be found [here](glossary.md).

## Developer Guide

Can be found [here](dev_guide.md).
