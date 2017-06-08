import numpy as np

from plotting.plots import LineChart


class StackedLineChart(LineChart):
    def __init__(self, title):
        super().__init__(title)

    @property
    def y_axes(self):
        raise NotImplementedError

    @property
    def legend_locations(self):
        raise NotImplementedError

    def prepare(self, axis):
        self._set_chart_title(axis)
        axis.set_xlabel(self._x_axis)

        legend_location = self._legend_locations[0]
        y_axis = self._y_axes[0]  # Only allow 1 y-axis
        lines = self._lines

        x = np.array(lines[0].x)  # Assume the same x for each line
        ys = np.row_stack([np.array(line.y).T for line in lines])
        labels = [line.label for line in lines]

        axis.stackplot(x, ys, labels=labels)

        axis.set_ylabel(y_axis)
        axis.legend(loc=legend_location)
