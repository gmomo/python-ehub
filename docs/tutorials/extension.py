"""
This is a file for a tutorial on how to extend the model without modifying it.

To run this file, from the root directory of this project, do

    python3.6 -m docs.tutorials.extension
"""
import os

from cli import pretty_print
from energy_hub import EHubModel
from energy_hub.ehub_model import constraint


class MyModel(EHubModel):
    """
    This is a subclass of EHubModel.

    Here, we can add our own constraints.
    """

    @staticmethod
    @constraint()
    def new_constraint(model):
        """
        This is a new constraint of the model.

        We can set up whatever constraint we want here.

        Args:
            model: The model instance that we can use to get Pyomo variables,
            parameters, etc..

        Returns:
            Some constraint that relates variables, parameters, etc. with each
            other.
        """
        return model.TankSize + model.BatSize <= 200

    @staticmethod
    @constraint('time', 'energy_carrier')
    def indexed_constraint(model, t, output_stream):
        """
        This is an example of a constraint that is indexed by some Pyomo sets.

        Each of the arguments to `@contraint` are the names of Pyomo sets. The
        constraint is then passed each element of those sets to this method.

        It acts much like:

            for t in model.time:
                for output_stream in model.energy_carrier:
                    indexed_constraint(model, t, output_stream)

        Args:
            model: The model instance containing everything Pyomo
            t: A specific time step in `model.time`
            output_stream: A specific output energy stream from
                `model.energy_carrier`.

        Returns:
            Something similar to the above non-indexed constraint.
        """
        # This says the the energy exported at every time step and every output
        # stream has to be 0. This could mean that we don't want to export any
        # energy at all and just use it to fill storages instead.
        return model.energy_exported[t, output_stream] == 0

# This is a cross-platform way of getting the path to the Excel file
current_directory = os.path.dirname(os.path.realpath(__file__))
excel_file = os.path.join(current_directory, 'extension.xlsx')

# Here's where we instantiate our model. Nothing is solved at this point.
my_model = MyModel(excel=excel_file)

# Now we solve the model and get back our results
results = my_model.solve()

# Now we print the results to the console so we can view them in a nice way
pretty_print(results)
