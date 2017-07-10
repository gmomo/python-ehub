"""
Provides functionality for handling a request format's time series.
"""
from typing import Dict, List


class TimeSeries:
    """A wrapper for a request format time series."""

    def __init__(self, time_series_request: dict) -> None:
        """
        Create a new wrapper.

        Args:
            time_series_request: The request format time series
        """
        self._series = time_series_request

    @property
    def stream(self) -> str:
        """Return the name of the stream."""
        return self._series['stream']

    @property
    def is_source(self) -> bool:
        """Is this time series a source?"""
        return self._series['type'] == 'Source'

    @property
    def is_demand(self) -> bool:
        """Is this time series a demand?"""
        return self._series['type'] == 'Demand'

    @property
    def name(self) -> str:
        """The name of the time series."""
        return self._series['id']

    @property
    def is_solar(self) -> bool:
        """Is this time series for solar data?"""
        return self.is_source and (self._series['id'] == 'Solar'
                                   or self._series['id'] == 'Irradiation')

    @property
    def data(self) -> List[float]:
        """The raw data as a list."""
        return self._series['data']

    @property
    def pyomo_data(self) -> Dict[int, float]:
        """A dictionary for use with Pyomo."""
        return {
            column: value
            for column, value in enumerate(self._series['data'])
        }
