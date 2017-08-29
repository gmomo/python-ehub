# Visualization Tool Documentation 

## Description

### Frontend
The module takes in various system parameters and optimized variables and plots various graphs in a new browser window. 
It has a tabbed layout with each tab containing plots related to a particular quantity. All plots are interactive with zoom/pan and hover features. Plots can also be saved onto the computer as a jpeg file. Some plots have dropdown menus beside them, which allow the user to select different hubs/forms or technologies for that particular plot. 

### Back End
The tool is designed as a class called VizTool. For each tab in the frontend, it has a corresponding function in the class. There are two additional functions, the first is to create the layout and the second is to draw a custom legend for the plots. The plots are drawn using the bokeh library for python. The class needs to import certain variables from the ehub tool which is a python notebook. The notebook_import.py file helps to import those variables. 

