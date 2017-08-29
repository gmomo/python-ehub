# Visualization Tool Documentation 

## Description

### Frontend
The module takes in various system parameters and optimized variables and plots various graphs in a new browser window. 
It has a tabbed layout with each tab containing plots related to a particular quantity. All plots are interactive with zoom/pan and hover features. Plots can also be saved onto the computer as a jpeg file. Some plots have dropdown menus beside them, which allow the user to select different hubs/forms or technologies for that particular plot. 

### Back End
The tool is designed as a class called VizTool. For each tab in the frontend, it has a corresponding function in the class. There are two additional functions, the first is to create the layout and the second is to draw a custom legend for the plots. The plots are drawn using the bokeh library for python. The class needs to import certain variables from the ehub tool which is a python notebook. The notebook_import.py file helps to import those variables. 

## Installation

### Dependencies

1. bokeh 0.12.6 and bkcharts
2. networkx

The notebook_import.py and vis_class.py files must be in the same directory as the Python Notebook.

## Usage

The Visualization module can be run from the terminal with the command.

`bokeh serve --show vis_class.py --port #portno.`

or if executing directly from the IPython Notebook

`! bokeh serve --show vis_class.py --port #portno.`

`bokeh serve` starts the bokeh server
`--show` opens up a new window to display the plots
`--port #portno.` adds which port to use on the localhost. Usually 500xx. Default port 5006. 

It should open up a new browser window like the one shown below. All plots are have a toolbar on the side, with various options. Box Zoom, Wheel Zoom,Reset,Save plots to desktop. Hover over plots to see data points. Line Graph legends are also interactive, they can be used to hide/show plots.  

![alt text][logo]

[logo]: https://github.com/gmomo/python-ehub/blob/master/docs/screenshot_1.png "Viz Tool Frontend"



## Contributing

### Basic Code Structure

The `vis_class.py` file basically consists of a class `VizTool`. Certain class variables are given below.

`self.n_hubs` = Number of hubs

`self.n_forms` = Number of forms

`self.n_techs` = Number of techs

`self.demand` = Demand data from the ehub tool

`self.model` = Pyomo Model

`self.cmatrix` = Efficiency Matrix

`self.cap_dict` = Capacities

`self.time_steps` = Time Steps

`self.time_weeks` = Weeks if any, otherwise 0

`self.nodes` = Node List 

`self.e_forms` = Form List

`self.e_techs` = Tech List


This class has functions corresponding to each section of the tabbed interface. Each function lays out returns its individual plots. In the `layout()` function, all these plots are assembled into a tabbed interface. It also has a function `create_legend()` to create a custom legend for the technologies. Each individual function uses a certain `ColumnDataSource` object or a dictionary in `bokeh` to plot. Each `ColumnDataSource` object wraps a dictionary which contains the quantities to plot. Each dictionary contains lists. Functions,plots and their corresponding dictionaries with their accompanying lists are given below.

#### `demand_plot()` 
1. data_dict 

Value = Contains demand data by node and form indexed by timestep. 
Key = 'n' + form_number

#### `production()`
1. prod_data
2. prod_dataw = For week plots

Value = Contains production data indexed by timestep or weeks respectively.
Key = 'n' + hub_number + form_number + tech_number

#### `capacities()`
1. cap_source






