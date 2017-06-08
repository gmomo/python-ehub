import matplotlib.pyplot as plt


class Figures:
    """A collection of Figure objects."""
    def __init__(self):
        self._figures = []

    def __len__(self):
        return len(self._figures)

    def append(self, figure):
        self._figures.append(figure)

    def add(self, figure):
        self.append(figure)

    def __iter__(self):
        return self._figures.__iter__()

    def __getitem__(self, index):
        return self._figures[index]

    def show(self, *, figures=None):
        if figures is None:
            # They want to show all the figures
            for num, figure in enumerate(self, start=1):
                fig = plt.figure(num)

                figure.prepare(fig)

            plt.show()
