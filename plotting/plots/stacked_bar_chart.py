import numpy as np

from plotting.plots import BarChart


class StackedBarChart(BarChart):
    def prepare(self, axis):
        axis.set_title(self._title)
        axis.set_xlabel(self._x_axis)
        axis.set_ylabel(self._y_axis)

        bars = self._bars

        bar_width = self.GROUP_WIDTH

        left = np.arange(len(self.x))  # Position of the left-side of the bar

        # Have the previous bar be at 0 for all bars
        previous_bar = [0 for _ in range(len(self.x))]

        for i, bar in enumerate(bars):
            axis.bar(left, bar.y, bar_width, align='edge', label=bar.label,
                     bottom=previous_bar)

            previous_bar = [previous_y + float(y[0])
                            for previous_y, y
                            in zip(previous_bar, bar.y.tolist())]

        # Align the x labels to the center of the group
        axis.set_xticks(left + self.GROUP_WIDTH / 2)
        axis.set_xticklabels(self._groups)
        axis.grid()

        axis.legend(loc=self.legend_location)
