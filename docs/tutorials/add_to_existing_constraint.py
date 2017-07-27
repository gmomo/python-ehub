"""
This is a file that shows how to add something to a constraint.
"""
import os

from energy_hub import EHubModel
from energy_hub.utils import constraint
from run import pretty_print


class MyModel(EHubModel):
    """
    This is a subclass of the original EHubModel.

    We create a subclass so that we can modify the superclass (or parent
    class) without modifying the superclass's source code.
    """

    @constraint()
    def calculate_total_cost(self):
        """Calculate a new total cost that allows for subsidies."""
        # This gets the constraint object from the parent class's
        # `calculate_total_cost`. If this function has arguments, you should
        # pass in the arguments from the arguments of this new function.
        parent_constraint = super().calculate_total_cost()

        # Now that we have the constraint, we also need to know how the
        # constraint is structured. Is the LHS of the constraint the calculated
        # total cost or is it the RHS? The only way to know is to look at the
        # parent class's soruce code for `calculate_total_cost`.
        #
        # In our case, the RHS is the calculated total cost.
        old_total_cost = parent_constraint.rhs

        # Now we calculate the total income we get from the subsidies. In this
        # case we get $1000 from each converter we use.
        total_subsidy = sum(1000
                            * self.is_installed[tech]
                            for tech in self.techs_without_grid)

        # Now we return the new calculated total cost
        return self.total_cost == old_total_cost - total_subsidy


def main():
    """The main function of this script."""
    # This is a cross-platform way of getting the path to the Excel file
    current_directory = os.path.dirname(os.path.realpath(__file__))
    excel_file = os.path.join(current_directory, 'extension.xlsx')

    # Here's where we instantiate our model. Nothing is solved at this point.
    my_model = MyModel(excel=excel_file)

    # Now we solve the model and get back our results
    results = my_model.solve()

    # Now we print the results to the console so we can view them in a nice way
    pretty_print(results)


if __name__ == '__main__':
    main()
