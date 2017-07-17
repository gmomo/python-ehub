"""
Provides functionality for handling a request format's converter.
"""
from typing import List, Optional, Union, Dict


class Converter:
    """A wrapper for a request format converter."""

    def __init__(self, converter_request: dict, capacity_converter: dict) -> None:
        """Create a new wrapper for a converter.

        Args:
            converter_request: The converter in the request format
            capacity_converter: The capacity associated with the converter
        """
        self._converter = converter_request
        self._capacity = capacity_converter

    @property
    def capacity(self) -> Union[float, str]:
        """Return the capacity of the converter."""
        return self._converter['capacity']

    @property
    def min_load(self) -> Optional[float]:
        """Return the minimum load of the tech if it has one."""
        if 'min_load' in self._converter:
            return self._converter['min_load'] / 100
        return None

    @property
    def is_solar(self) -> bool:
        """Is the converter solar?"""
        return self.is_roof_tech

    @property
    def max_capacity(self) -> float:
        """The maximum capacity of the converter."""
        return self.capacity

    @property
    def has_part_load(self) -> bool:
        """Does the converter have a part load?"""
        if 'min_load' in self._converter:
            part_load = self._converter['min_load']

            return part_load > 0

        return False

    @property
    def inputs(self) -> List[str]:
        """The names of the input streams for the converter."""
        return self._converter['inputs']

    @property
    def name(self) -> str:
        """The name of the converter."""
        return self._converter['name']

    @property
    def outputs(self) -> List[str]:
        """The names of the output streams for the converter."""
        return self._converter['outputs']

    @property
    def efficiency(self) -> float:
        """The efficiency of the converter."""
        return self._converter['efficiency']

    @property
    def output_ratios(self) -> Dict[str, float]:
        """The output ratios for each output stream."""
        output_ratios = {}
        for output in self.outputs:
            if output == 'Elec':
                output_ratios['Elec'] = 1
            else:
                output_ratios[output] = self._output_ratio

        return output_ratios

    @property
    def _output_ratio(self) -> float:
        """The output efficiency of the converter."""
        if 'output_ratio' in self._converter:
            return self._converter['output_ratio']

        return 1.0

    @property
    def usage_maintenance_cost(self) -> float:
        """The usage maintenance cost of the converter."""
        return self._converter['usage_maintenance_cost']

    @property
    def lifetime(self) -> float:
        """The lifetime in years of the tech."""
        return self._converter['lifetime']

    @property
    def is_roof_tech(self) -> bool:
        """Is this converter on the roof?"""
        return 'Irradiation' in self.inputs

    @property
    def is_dispatch(self) -> bool:
        """Is this a dispatch converter?"""
        return (not self.is_solar
                and self.name != 'Grid')

    @property
    def fixed_capital_cost(self) -> float:
        """
        Return the fixed capital cost of the converter.

        Returns:
            The fixed capital cost if it has one or 0.
        """
        if 'fixed_capital_cost' in self._converter:
            return self._converter['fixed_capital_cost']

        return 0

    @property
    def capital_cost(self) -> float:
        """Return the capital cost of the converter."""
        return self._converter['capital_cost']

    @property
    def is_grid(self) -> bool:
        """Is this converter the grid?"""
        return self._converter['name'] == 'Grid'

    @property
    def area(self) -> Optional[float]:
        """Return the area of this roof tech if this tech is a roof tech."""
        if self._capacity and self._capacity['units'] == 'm2':
            return self._capacity['bounds']['lower']

        return None

    @property
    def is_chp(self) -> bool:
        """Does the converter use and/or output heat and power?"""
        return len(self._converter['outputs']) >= 2
