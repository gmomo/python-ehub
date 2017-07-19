# Glossary

This file contains terminology that is used throughout the project.

## Table of Contents

- [Linear Programming](#linear-programming)
- [Request Format/Excel Sheet](#request-formatexcel-sheet)
- [Civil Engineering](#civil-engineering)

## Linear Programming

Linear programming is a technique for maximizing or minimizing a linear
objective function with linear inequality constraints.

#### Objective Function

This is the linear function we want to max or min.

#### Variable

Some mathematical variable you want to solve for.

#### Constraint

An equation that relates variables and parameters; the same as a mathematical 
constraint.

### Example Problem

Say we are at a candy store and would like to buy either chocolate bars and
popsicles.
We'll denote the number of chocolate bars we get as `c` and pipsicles as `p`.
These will be our variables.

We would like to minimize the cost of the chocolate bars and popsicles we buy.
For our example, we let the price of a chocolate bar be $2 and of a popsicle
$1.
Our objective function would then be `$2*x + $1*y`.

However, we would like at least one of both, a total number of both
chocolate bars and popsicles to be at least 5, and also have more chocolate
bars than popsicles.
So our constraints would be:
- `c >= 1`
- `p >= 1`
- `c + p >= 5`
- `c > p`

Now you hopefully have an idea of what an objective function, a variable, and a
constraint is in the context of linear programming.

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
