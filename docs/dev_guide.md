# Developer Guide

This document contains information for extending and modifying the Energy Hub 
Model.

For more concrete API details, see the code.
That will be more up-to-date than any other documentation.

## How to Contribute

### Core Development

When fixing a bug or adding a new feature, first create a branch for you to
work in:
```bash
git branch my_bug_fix
git checkout my_bug_fix
```

Then make your changes to this branch only.

When you are done making your changes, make a pull request on the GitHub repo.
Then add one of the main collaborators as a reviewer.
We'll review your changes, make suggestions, and merge it when it's good.

### Non-core Development

If you want to extend the functionality of the model, and you don't have push
access to the repo, create a fork of the project on GitHub.
Then develop on your fork as you wish.
If you think your changes might be useful to the main core, create a pull
request from your fork to the repo.
Then follow the same instructions as for core development.

## Tutorials/Examples

- For a tutorial on how to extend the model for your use without modifying the
model, see [here](tutorials/extension.py).

## "What are all these @s?"

This is the function decorator syntax.

A great tutorial on how to use them can be found
[here](https://www.thecodeship.com/patterns/guide-to-python-function-decorators/).

