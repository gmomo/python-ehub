

class Figure:
    def __init__(self, title, *, num_rows=1, num_cols=1, padding=1):
        self._num_rows = num_rows
        self._num_cols = num_cols
        self._padding = padding
        self._title = title

        self._plots = [[None] * num_cols for _ in range(num_rows)]

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def num_rows(self):
        return self._num_rows

    @num_rows.setter
    def num_rows(self, num_rows):
        self._num_rows = num_rows

    @property
    def num_cols(self):
        return self._num_cols

    @num_cols.setter
    def num_cols(self, num_cols):
        self._num_cols = num_cols

    @property
    def padding(self):
        return self._padding

    def add(self, plot, *, row=1, col=1):
        if not (1 <= row <= self.num_rows):
            raise IndexError('row must be between 1 and {}'
                             .format(self.num_rows))
        if not (1 <= col <= self.num_cols):
            raise IndexError('col must be between 1 and {}'
                             .format(self.num_cols))

        self._plots[row - 1][col - 1] = plot

    def prepare(self, fig):
        fig.set_tight_layout({
            'pad': self.padding
        })

        fig.canvas.set_window_title(self._title)
        # fig.suptitle(self._title)

        i = 0
        for row, row_of_plots in enumerate(self._plots):
            for col, plot in enumerate(row_of_plots):
                i += 1
                if plot:
                    axis = fig.add_subplot(self.num_rows, self.num_cols, i)

                    plot.prepare(axis)

