

class Config:
    """
    Contains all configurations for the EHub Model
    """

    def __init__(self, args):
        """
        Creates the Config object using the command-line arguments.

        Arguments:
            args - The object from argparse.parse_args()
        """
        self._input_file = args.input_file
        self._output_file = args.output_file
        if args.solver:
            self._solver = args.solver

    @property
    def input_file(self):
        """
        The input file of data for the EHub Model
        """
        return self._input_file

    @property
    def output_file(self):
        """
        The output file for the results of the model
        """
        return self._output_file

    @property
    def solver(self):
        """
        The solver to be used.
        """
        if self._solver:
            return self._solver
        else:
            raise RuntimeError("No solver was specified.")

    @property
    def solver_options(self):
        """
        The options that are passed to the solver.
        """
        options = {
            "mipgap": 0.05,
            # "FeasibilityTol": 1e-05,
        }
        return options
