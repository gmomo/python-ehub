# Glossary

This file contains terminology that is used throughout the project.

## Table of Contents

- [Pyomo](#pyomo)
- [Request Format/Excel Sheet](#reqest-format/excel-sheet)
- [Civil Engineering](#civil-engineering)

## Pyomo

#### Variable

Much like a mathematical variable.

This is usually something we want to solve for.

#### Parameter

Much like a mathematical parameter.

This is some constant that should not change.

#### Constraint

Much like a mathematical constraint.

An equation that relates variables and parameters.

## Request Format/Excel Sheet

#### Capacity

A variable essentially. You can reference this capacity in certain places in 
order to introduce a variable amount of something.

For example, you can create a capacity in the capacities tab and then reference
it in the capacity row in the Converters tab. This makes it so that it finds 
the most optimal converter capacity as well as the other variables.

## Civil Engineering

#### Stream

This is an abstract representation of some sort of energy. Something like Heat 
or Electricity is considered a stream.

#### Converter

A piece of technology or machine that converts one or more input energy streams 
into one or more output energy streams.

#### Storage

A piece of technology that stores an energy stream.

#### Time Series

Some data that has time associated with it.

For example, the energy that is demanded per time step is a time series.

#### Capacity
