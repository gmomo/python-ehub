

class Chart:
    def __init__(self, title):
        self._title = title

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    def _set_chart_title(self, axis):
        axis.set_title(self._title)

    def prepare(self, axis):
        raise NotImplementedError
