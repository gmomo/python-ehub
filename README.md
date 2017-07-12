Python e-hub
============

Requirements
------------

- Python 2.7+ (pandas, numpy, matplotlib libraries)
- Pyomo
- `glpk` or another solver supported by Pyomo

Running a Model
---------------

To run an energy hub model, use the `General_input.xlsx` file to enter your data.
The data **must** be in the same format.


1.	In `General` tab the following information has to be filled:
•	**fuel data (Price and CO2)** for all used types of fuel
•	**Interest rate**
•	 **Export price** for each demand (0 if it is not available)
•	**Number of hubs** - In this number nodes that have no demand (e.g. for network layout) have to be inputed
2.	In `Demand data` tab the following information has to be filled:
•	**Number of demands** that has to be met
•	**Demand name** - the names will be used for result output
•	**Hub** - to which hub the demand corresponds
•	**Values** - even if there is no demand still 0 has to be filled
3.	In `Technology` tab the following information has to be filled:

      •	Each column corresponds to new technology. Fill in the information accordingly to the row name. If the information is unknown put in 0. Row **hubs** specifies for each technology in which hub(s) it is present.

      •	**Output** matrix has to have as many rows as there are demands. Allowed values are: 1, 0, -negative_real. 1 means that the technology is producing this demand, 0 means it is not pro-ducing this demand and negative number means it is using this demand. E.g. if a specific tech-nology has an output column equal to 1, -1, -3 it means that for 1 kWh of demand 1 that it produces, it consumes 1 kWh of demand 2 and 3 kWh of demand 3.

      •	**Technology Carbon Factors** - for each technology it has to be inputed how much CO2 is produced for producing 1 kWh of energy. This value is connected to the fuel type. Based on the *technology carbon factors* value, it will be matched with *Fuel data* in `General` tab to calculate the fuel cost for the specific technology.

      •	**Storages** - for each demand storage data has to be filled. *Hubs* row specifies in which hubs the storage is available for each demand.

4.	In `Solar data` tab the solar irradiation has to be filled which will be used for all roof technology in all buildings
5.	In `Network` tab the following information has to be filled:

      •	**Demand** - for which demands a network is available in order in which demands have been defined in `Demand data` tab. E.g. if demands are electricity, heat and cooling, and a network is available for electricity and cooling, one would put values in the cell `1,3`.
      •	**Link ID** - just a number in the increasing manner.
      •	**Node 1** - from which node a connection is available
      •	**Node 2** - to which node a connection is available
      •	**Length (m)** - what is the length of this connection (used for calculating investment cost and/or losses)
---------------

In the python code set the correct path to excel file and run the needed code (cells).

---------------
In order to have bidirectional decentralized network change the domain of variable `DH_Q` to `Reals`. In order to have unidirectional network change the domain of variable `DH_Q` to `NonNegativeReals`. 

---------------
In order to have network layout optimization change the value of variable `fixednetwork` to 0.
In order to have fixed network layout change the value of variable `fixednetwork` to 1.




