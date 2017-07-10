# Glossary

This file contains terminology that is used throughout the project.

## Table of Contents

- [Pyomo](#pyomo)
- [Request Format/Excel Sheet](#request-formatexcel-sheet)
- [Civil Engineering](#civil-engineering)

## Pyomo

#### Set

A mathematical set of values.

These are often used to index Pyomo variables, parameters, and constraints.

#### Variable

Some mathematical variable you want to solve for.

#### Parameter

Some mathematical parameter that is passed into the model.

#### Constraint

An equation that relates variables and parameters; the same as a mathematical 
constraint.

## Request Format/Excel Sheet

#### Capacity

A variable essentially. You can reference this capacity in certain places in 
order to introduce a variable amount of something.

For example, you can create a capacity in the capacities tab and then reference
it in the capacity row in the Converters tab. This makes it so that it finds 
the most optimal converter capacity as well as the other variables.

## Energy Hub Model

For a paper on some background information, see 
[this paper](http://www.sciencedirect.com/science/article/pii/S0360544214007270).

#### Stream

This is an abstract representation of some sort of energy.

Examples:
- Electricity
- Heat
- Solar Irradiation
- Gas

#### Converter

A piece of technology or machine that converts one or more input energy streams 
into one or more output energy streams.

Examples:
- Solar panels
    - Takes solar irradiation and converts it into electricity.
- Gas heater
    - Takes gas and converts it into heat

#### Storage

A piece of technology that stores an energy stream.

Examples: 
- Battery
    - stores electricity
- Hot water tank
    - stores heat

#### Time Series

Some data that has time associated with it.

Examples:
- Energy demands
- Solar irradiation

#### PV

Short for photovoltaic.
Usually used to refer to solar panels.

#### Solar

Anything that uses the sun.
Does **not** have to refer to solar panels.

#### Capacity
