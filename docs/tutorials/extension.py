"""
This is a file for a tutorial on how to extend the model without modifying it.

To run this file, from the root directory of this project, do

    python3.6 -m docs.tutorials.extension
"""
import os

from run import pretty_print
from energy_hub import EHubModel
from energy_hub.utils import constraint, constraint_list


class MyModel(EHubModel):
    """
    This is a subclass of EHubModel.

    Here, we can add our own constraints.
    """

    @constraint()
    def new_constraint(self):
        """
        This is a new constraint of the model.

        We can set up whatever constraint we want here.

        Returns:
            Some constraint that relates variables, parameters, etc. with each
            other.
        """
        # Since these variables on loaded on run-time, PyCharm and pylint won't
        # see them. They think they don't exist. So we just tell them to trust
        # us and ignore the warnings.
        # pylint: disable=no-member
        # noinspection PyUnresolvedReferences
        return self.TankSize + self.BatSize <= 200

    @constraint('time', 'output_streams')
    def indexed_constraint(self, t, output_stream):
        """
        This is an example of a constraint that is indexed by some Pyomo sets.

        Each of the arguments to `@contraint` are the names of Pyomo sets. The
        constraint is then passed each element of those sets to this method.

        It acts much like:

            for t in model.time:
                for output_stream in model.energy_carrier:
                    indexed_constraint(model, t, output_stream)

        Args:
            t: A specific time step in `model.time`
            output_stream: A specific output energy stream from
                `model.energy_carrier`.

        Returns:
            Something similar to the above non-indexed constraint.
        """
        # This says the the energy exported at every time step and every output
        # stream has to be 0. This could mean that we don't want to export any
        # energy at all and just use it to fill storages instead.
        return self.energy_exported[t][output_stream] == 0

    @constraint_list()
    def constraint_list_example(self):
        """
        This is an example of using the constraint_list decorator.

        This makes a method "return" a list of constraints for some data.

        This is mostly used for some data that would make it too complicated to
        have it in a lot of regular @constraint methods. It could also be used
        to check if a constraint is valid before adding it to the model.

        Yields:
            Constraints
        """
        for t in range(len(self.time)):
            if 10 <= t <= 18:
                # Lookup Python generators to learn more on that this does
                yield self.energy_imported[t]['Grid'] >= 10


def main():
    """
    This is the main executing function of the script.

    It is considered good practise to have a main function for a script.
    """
    # This is a cross-platform way of getting the path to the Excel file
    current_directory = os.path.dirname(os.path.realpath(__file__))
    excel_file = os.path.join(current_directory, 'extension.xlsx')

    # Here's where we instantiate our model. Nothing is solved at this point.
    my_model = MyModel(excel=excel_file)

    # Now we solve the model and get back our results
    results = my_model.solve()

    # Now we print the results to the console so we can view them in a nice way
    pretty_print(results)


# If we are being run as a script
if __name__ == '__main__':
    main()
