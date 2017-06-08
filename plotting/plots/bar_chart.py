from collections import namedtuple

import numpy as np

from plotting.plots.chart import Chart

Bar = namedtuple('Bar', ['y', 'label', 'color'])


class BarChart(Chart):
    GROUP_WIDTH = 0.8

    def __init__(self, title, horizontal=False):
        super().__init__(title)

        self._x_axis = ''
        self._y_axis = ''
        self._legend_location = 'best'
        self._horizontal = horizontal
        self._groups = []
        self._bars = []

    @property
    def y_axis(self):
        return self._y_axis

    @y_axis.setter
    def y_axis(self, label):
        self._y_axis = label

    @property
    def x(self):
        return self._groups

    @x.setter
    def x(self, value):
        self._groups = value

    @property
    def legend_location(self):
        return self._legend_location

    @legend_location.setter
    def legend_location(self, location):
        self._legend_location = location

    def plot(self, *, y=None, label='', color=''):
        if y is None:
            raise ValueError("Must specify the bar's y coordinates")
        if len(y) != len(self.x):
            raise ValueError("Must specify the same number of y's as x. "
                             "len(y) = {} != len(x) = {}"
                             .format(len(y), len(self.x)))

        self._bars.append(Bar(y, label, color))

    def prepare(self, axis):
        axis.set_title(self._title)
        axis.set_xlabel(self._x_axis)
        axis.set_ylabel(self._y_axis)

        bars = self._bars

        bar_width = self.GROUP_WIDTH / len(bars)

        left = np.arange(len(self.x))  # Position of the left-side of the bar

        # Have the previous bar be at 0 for all bars
        previous_bar = [0 for _ in range(len(self.x))]

        for i, bar in enumerate(bars):
            axis.bar(left + i * bar_width, bar.y, bar_width, align='edge',
                     label=bar.label, bottom=previous_bar)

        # Align the x labels to the center of the group
        axis.set_xticks(left + self.GROUP_WIDTH / 2)
        axis.set_xticklabels(self._groups)
        axis.grid()

        axis.legend(loc=self.legend_location)
