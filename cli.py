import argparse
import config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Finds the optimal solution to a energy hub model.")
    parser.add_argument("--input_file",
                        default="General_input.xlsx",
                        help="The Excel 2003 file used as input into "
                        "the model.")
    parser.add_argument("--output_file",
                        default="output.txt",
                        help="The text file to save the results "
                        "of the solution.")

    return parser.parse_args()


def main():
    args = parse_args()

    config.config = config.Config(args)

    # run the script
    import EhubModel


if __name__ == "__main__":
    main()
