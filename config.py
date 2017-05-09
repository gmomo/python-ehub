config = None


class Config:
    def __init__(self, args):
        self._input_file = args.input_file
        self._output_file = args.output_file

    @property
    def input_file(self):
        return self._input_file

    @property
    def output_file(self):
        return self._output_file
