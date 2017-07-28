"""
This is a file that shows how to remove a constraint.
"""
import os

from energy_hub import EHubModel
from energy_hub.utils import constraint_list
from run import pretty_print


class MyModel(EHubModel):
    """
    This is a subclass of the original EHubModel.

    We create a subclass so that we can modify the superclass (or parent
    class) without modifying the superclass's source code.

    For this tutorial, say we want to remove the continuity constraint.
    """

    # We disable the constraint by using `enabled=False` in the function
    # decorator's arguments
    @constraint_list(enabled=False)
    def storage_looping(self):
        """Now this constraint won't be used."""
        # We can test this by raising an Exception and then testing if we
        # caught it later on.
        raise Exception


def main():
    """The main function of this script."""
    # This is a cross-platform way of getting the path to the Excel file
    current_directory = os.path.dirname(os.path.realpath(__file__))
    excel_file = os.path.join(current_directory, 'extension.xlsx')

    # This should be throwing an exception if the constraint is not disabled
    my_model = MyModel(excel=excel_file)
    # Since it is disabled, we won't see an exception

    # Now we solve the model and get back our results
    results = my_model.solve()

    # Now we print the results to the console so we can view them in a nice way
    pretty_print(results)


if __name__ == '__main__':
    main()
