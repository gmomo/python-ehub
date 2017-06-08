from collections import namedtuple

from plotting.plots.chart import Chart

Line = namedtuple('Line', ['x', 'y', 'label', 'color', 'y_axis'])


class LineChart(Chart):
    def __init__(self, title):
        super().__init__(title)

        self._x_axis = ''
        self._y_axes = ['']
        self._lines = []
        self._legend_locations = ['best']

    @property
    def x_axis(self):
        return self._x_axis

    @x_axis.setter
    def x_axis(self, label):
        self._x_axis = label

    @property
    def y_axis(self):
        return self._y_axes[0]

    @y_axis.setter
    def y_axis(self, label):
        self._y_axes[0] = label

    @property
    def legend_location(self):
        return self._legend_locations[0]

    @legend_location.setter
    def legend_location(self, location):
        self._legend_locations[0] = location

    @property
    def legend_locations(self):
        return self._legend_locations

    @legend_locations.setter
    def legend_locations(self, locations):
        self._legend_locations = locations

    @property
    def y_axes(self):
        return self._y_axes

    @y_axes.setter
    def y_axes(self, axes):
        self._y_axes = axes

    def plot(self, *, x=None, y=None, label=None, y_axis=None, color=''):
        if x is None:
            raise ValueError("Must specify the points' x coordinates")
        if y is None:
            raise ValueError("Must specify the points' y coordinates")

        self._lines.append(Line(x, y, label, color, y_axis))

    def prepare(self, axis):
        self._set_chart_title(axis)
        axis.set_xlabel(self._x_axis)

        legend_locations = self._legend_locations
        y_axes = self._y_axes
        lines = self._lines

        if len(y_axes) == 2:
            # Assume we are sharing the x-axis
            axes = [axis, axis.twinx()]
        else:
            axes = [axis]

        for line in lines:
            if line.y_axis in y_axes:
                axis = axes[y_axes.index(line.y_axis)]
            else:
                axis = axes[0]

            axis.plot(line.x, line.y, line.color, label=line.label)

        for axis, label, location in zip(axes, y_axes, legend_locations):
            axis.set_ylabel(label)
            axis.legend(loc=location)
