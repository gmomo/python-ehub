from ehub_model import EHubModel
from config import settings


def main():
    model = EHubModel(excel=settings["input_file"])

    results = model.solve()

    print(results)

    with open(settings["output_file"], 'w') as f:
        f.write(str(results))


if __name__ == "__main__":
    main()
