"""
Provides functionality for handling the streams in the request format.
"""


class Stream:
    """A wrapper for a request format stream."""

    def __init__(self, stream_request: dict, request: dict) -> None:
        """
        Create a new wrapper.

        Args:
            stream_request: The request format stream
            request: The request format
        """
        self._stream = stream_request
        self._request = request

    @property
    def co2(self) -> float:
        """The C02 factor of the stream."""
        return self._stream['co2']

    @property
    def price(self) -> float:
        """The price of the stream."""
        return self._stream['price']

    @property
    def export_price(self) -> float:
        """The export price of the stream."""
        return self._stream['export_price']

    @property
    def is_output(self) -> bool:
        """Is this an output stream?"""
        for tech in self._request['converters']:
            if self.name in tech['outputs']:
                return True

        return False

    @property
    def name(self) -> str:
        """The name of the stream."""
        return self._stream['name']
