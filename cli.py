import argparse
from ehub_model import EHubModel
from config import Config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Finds the optimal solution to a energy hub model.")
    parser.add_argument("--input_file",
                        default="General_input.xlsx",
                        help="The Excel 2003 file used as input into the "
                        "model.")
    parser.add_argument("--output_file",
                        default="output.txt",
                        help="The text file to save the results of the "
                        "solution.")
    parser.add_argument("--solver",
                        required=True,
                        help="The solver to use for solving the model. The "
                        "solver must already be installed on the system.")

    return parser.parse_args()


def main():
    args = parse_args()

    config = Config(args)

    model = EHubModel(excel=config.input_file)

    results = model.solve(config.solver, config.solver_options)

    print(results)

    with open(config.output_file, 'w') as f:
        f.write(str(results))


if __name__ == "__main__":
    main()
