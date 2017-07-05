"""
This is a file for a tutorial on how to extend the model without modifying it.

To run this file, from the root directory of this project, do

    python3.6 -m docs.tutorials.extension
"""
import os

from cli import pretty_print
from energy_hub import EHubModel
from energy_hub.ehub_model import constraint


# noinspection PyShadowingNames
class MyModel(EHubModel):
    """
    This is a subclass of EHubModel.

    Here, we can add our own constraints.
    """

    @staticmethod
    @constraint()
    def new_constraint(model):
        return model.TankSize + model.BatSize <= 200

current_directory = os.path.dirname(os.path.realpath(__file__))
model = MyModel(excel=f"{current_directory}/extension.xlsx")

results = model.solve()

pretty_print(results)
