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
`--port #portno.` adds which port to use on the localhost

