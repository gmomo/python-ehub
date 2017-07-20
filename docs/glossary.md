# Glossary

This file contains terminology that is used throughout the project.

## Table of Contents

- [Linear Programming](#linear-programming)
- [Energy hub model](#energyhubmodel)
- [Request Format/Excel Sheet](#request-formatexcel-sheet)

## Linear Programming

Linear programming is a technique for minimizing a linear
objective function of many variables subject to linear equality and 
inequality constraints.

#### Objective Function

This is the function we want to optimize.
By convention it is always to be minimized.

#### Variable

The set of variables you want to solve for.

#### Constraint

A linear equation that relates variables to constant values and/or to each
other.
Constraints can be equalities or inequalities.
By convention inequalities are always less-than or less-than-or-equal, however
we can express them as greater-than or greater-than-or-equal-to and they are
converted later.

### Example Problem

Say we are at a candy store and would like to buy either chocolate bars and
popsicles.
We'll denote the number of chocolate bars we get as `c` and popsicles as `p`.
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

## Energy Hub Model

The energy hub model is a form of linear programme that describes an energy
conversion and storage problem over multiple time steps. 
For some background information, see
[this paper](http://www.sciencedirect.com/science/article/pii/S0360544214007270).

#### Stream

This is an abstract representation of some particular sort of energy.

Examples:
- Electricity
- Heat
- Solar irradiation
- Gas

#### Time series

A series of values for something changing over time, usually at a fixed
interval that matches the time step of the model.

Examples:
- Energy demands to be met each time step
- Solar irradiation available each time step

#### Energy balance

A constraint that enforces the balance of energy into and out of the system
(since energy can be neither created nor destroyed).
The constraint is applied for every energy stream, for every time step.
In order to achieve this balance, energy may have to be converted between
streams and/or stored between time steps (see below).

#### Converter

A component that converts one or more input energy streams into one or more
output energy streams.
Each converter has a variable associated with it that defines how much energy
is converted at each time step.
The value of this variable is determined based on the energy balance
constraints and the overall desire to minimise the objective function.

Examples:
- Gas boiler / furnace
    - Takes gas and converts it into heat
- Heat pump
    - Takes electricity and converts it into heat
- PV (photovoltaic) panels
    - Takes solar irradiation and converts it into electricity
- Combined heat and power plant
    - Takes gas and converts it into both heat and electricity

#### Storage

A component that stores a given energy stream.
Each storage has three variables associated with it for every time step:
- how much energy enters the store
- how much leaves the store
- how much is currently in the store

The first two appear in the energy balance constraints; all three appear in a
storage continuity constraint.

Examples: 
- Battery
    - Stores electricity
- Hot water tank
    - Stores heat

#### Capacity

The size of a component (converter or storage).

The capacity is the same for all time steps, and determines the maximum energy
converted by a converter or stored in a storage.

The capacity may be fixed (set to a constant value before the model is run) or
variable (assigned to an optimisation variable). 

## Request Format/Excel Sheet

To see the actual schema, go to the `request_format.py` file.

#### Capacity

An optimisation variable that relates to the capacity of a component (converter
or storage).
You can reference this capacity in other places in the input data.

For example, you can create a capacity in the Capacities tab and then reference
it in the capacity row in the Converters tab.
This sets the capacity of that component to be an optimization variable.
