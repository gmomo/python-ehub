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
    def calculate_operating_cost(self):
        """
        Calculate a new operating cost that uses a price per time step.

        Instead of using a fixed price for electricity from the grid, we
        instead use a time series that contains the price per time step.
        """
        # Here we find the specific time series called `GridPrice`
        grid_price = [series for series in self._data.time_series_list
                      if series.name == 'GridPrice'][0]

        operating_cost = 0
        for tech in self._data.converters:
            if 'Grid' in tech.inputs:
                operating_cost += sum(grid_price.data[t]
                                      * self.energy_imported[t][tech.name]
                                      for t in self.time)
            else:
                # Default to the fixed price for non `Grid` converters
                total_energy_imported = sum(self.energy_imported[t][tech.name]
                                            for t in self.time)

                operating_cost += (self.OPERATING_PRICES[tech.name]
                                   * total_energy_imported)

        return self.operating_cost == operating_cost


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
