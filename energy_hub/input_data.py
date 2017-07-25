"""
Provides functionality for handling the request format for using in the
EHubModel.
"""
from collections import defaultdict
from typing import List, Optional, Dict, TypeVar, Iterable

import pandas as pd

from data_formats.request_format import (
    Capacity, Converter, Stream, Storage, TimeSeries,
)
from energy_hub.utils import cached_property

T = TypeVar('T')


class InputData:
    """Provides convenient access to needed data to implement an energy hub
    model."""

    def __init__(self, request: dict) -> None:
        """Create a new instance.

        Args:
            request: A dictionary in request format
        """
        self._request = request

    @cached_property
    def capacities(self) -> List[Capacity]:
        """The list of capacities."""
        return [Capacity(capacity) for capacity in self._request['capacities']]

    def _get_capacity(self, name: str) -> Optional[dict]:
        """Get the capacity in the request format with this name.

        Args:
            name: The name of the capacity

        Returns:
            Either the capacity in the request format or None
        """
        capacities = self._request['capacities']

        for capacity in capacities:
            if capacity['name'] == name:
                return capacity

        return None

    @cached_property
    def storages(self) -> List[Storage]:
        """The list of storages."""
        def _make(storage):
            capacity = self._get_capacity(storage['capacity'])

            return Storage(storage, capacity)

        return [_make(storage) for storage in self._request['storages']]

    @property
    def storage_names(self) -> List[str]:
        """Return the names of the storages."""
        return [storage.name for storage in self.storages]

    @cached_property
    def converters(self) -> List[Converter]:
        """The list of converters."""
        def _make(converter):
            capacity = self._get_capacity(converter['capacity'])

            return Converter(converter, capacity)

        return [_make(converter) for converter in self._request['converters']]

    @property
    def converter_names(self) -> List[str]:
        """Return the names of the converters."""
        return [converter.name for converter in self.converters]

    @property
    def converter_names_without_grid(self) -> List[str]:
        """Return the names of the converters except for the grid."""
        return [converter.name for converter in self.converters
                if converter.name != 'Grid']

    @cached_property
    def time_series_list(self) -> List[TimeSeries]:
        """The list of time series."""
        return [TimeSeries(time_series)
                for time_series in self._request['time_series']]

    @cached_property
    def streams(self) -> List[Stream]:
        """The list of streams."""
        return [Stream(stream, self._request)
                for stream in self._request['streams']]

    @property
    def stream_names(self) -> List[str]:
        """Return the names of the streams."""
        return [stream.name for stream in self.streams]

    @cached_property
    def output_stream_names(self):
        """The sorted list of output streams names."""
        names = (output for tech in self.converters for output in tech.outputs)

        return sorted(set(names))

    @property
    def demands(self) -> Iterable[TimeSeries]:
        """Return the TimeSeries that are demands."""
        return (demand for demand in self.time_series_list
                if demand.is_demand)

    @cached_property
    def num_time_steps(self) -> int:
        """Return the number of time steps in the model."""
        return len(list(self.demands)[0].data.keys())

    @cached_property
    def num_demands(self) -> int:
        """Return the number of demands."""
        return len(list(self.demands))

    @property
    def loads(self) -> Dict[str, Dict[int, float]]:
        """The data for all demands as a dictionary that is indexed by (time,
        demand time series ID)."""
        return {demand.stream: demand.data for demand in self.demands}

    @cached_property
    def solar_data(self) -> Dict[int, float]:
        """The data for the solar time series as a dictionary that is indexed
        by time."""
        solar = [time_series for time_series in self.time_series_list
                 if time_series.is_solar][0]  # Assume there is only one

        return solar.data

    @cached_property
    def chp_list(self) -> List[Converter]:
        """The Combined Heat and Power converters."""
        return [tech for tech in self.converters if tech.is_chp]

    @cached_property
    def roof_tech(self) -> List[str]:
        """The names of the converters that can be put on a roof."""
        return [tech.name for tech in self.converters if tech.is_roof_tech]

    @property
    def c_matrix(self) -> Dict[str, Dict[str, float]]:
        """Return a dictionary-format for the C matrix.

        The format is like {converter name: {stream name: ...}, ...}
        """
        c_matrix = pd.DataFrame(0, index=self.converter_names,
                                columns=self.stream_names, dtype=float)
        for tech in self.converters:
            efficiency = tech.efficiency

            for input_ in tech.inputs:
                c_matrix[input_][tech.name] = -1

            for output in tech.outputs:
                output_ratio = tech.output_ratios[output]
                c_matrix[output][tech.name] = efficiency * output_ratio

        return c_matrix.T.to_dict()

    @cached_property
    def solar_techs(self) -> List[str]:
        """The name s of the solar converters."""
        return [tech.name for  tech in self.converters
                if tech.is_solar]

    @cached_property
    def part_load(self) -> Dict[str, Dict[str, float]]:
        """Return the part load for each tech and each of its outputs."""
        part_load_techs = [tech for tech in self.converters
                           if not (tech.is_grid or tech.is_solar)]
        part_load = defaultdict(defaultdict)  # type: Dict[str, Dict[str, float]]
        for tech in part_load_techs:
            for output_stream in self.output_stream_names:
                if output_stream in tech.outputs:
                    min_load = tech.min_load
                    if min_load is not None:
                        part_load[tech.name][output_stream] = min_load

        return part_load

    @property
    def converters_capacity(self) -> Dict[str, float]:
        """Return the capacities of the converters."""
        return {tech.name: tech.capacity
                for tech in self.converters}

    @property
    def techs(self) -> List[str]:
        """Return the names of non-solar converters."""
        return [tech.name for tech in self.converters
                if not (tech.is_grid or tech.is_solar)]

    @property
    def disp_techs(self) -> List[str]:
        """The names of the dispatch converters."""
        return [tech.name for tech in self.converters if tech.is_dispatch]

    @property
    def part_load_techs(self) -> List[str]:
        """The names of the converters that have a part load."""
        return [tech.name for tech in self.converters if tech.has_part_load]

    @cached_property
    def linear_cost(self) -> Dict[str, float]:
        """Return the linear cost for each tech."""
        return {converter.name: converter.capital_cost
                for converter in self.converters}

    @cached_property
    def fixed_capital_costs(self) -> Dict[str, float]:
        """Return the fixed capital cost for each converter."""
        return {converter.name: converter.fixed_capital_cost
                for converter in self.converters}

    @cached_property
    def interest_rate(self) -> float:
        """The interest rate."""
        return self._request['general']['interest_rate']

    def _calculate_npv(self, lifetime: float) -> float:
        """Calculate the net present value of an asset giving its lifetime.

        Args:
            lifetime: The lifetime of the asset

        Returns:
            The net present value of the asset
        """
        r = self.interest_rate

        return 1 / (
            ((1 + r)**lifetime - 1) / (r * (1 + r)**lifetime)
        )

    @cached_property
    def tech_npv(self) -> Dict[str, float]:
        """The net present value of each converter."""
        return {tech.name: round(self._calculate_npv(tech.lifetime), 4)
                for tech in self.converters
                if not tech.is_grid}

    @cached_property
    def variable_maintenance_cost(self) -> Dict[str, float]:
        """The variable maintenance cost of each converter."""
        return {tech.name: tech.usage_maintenance_cost
                for tech in self.converters}

    @cached_property
    def carbon_factors(self) -> Dict[str, float]:
        """The carbon factor of each converter."""
        carbon_factors = {}
        for tech in self.converters:
            input_ = tech.inputs[0]  # Assume only one input per tech

            for stream in self.streams:
                if stream.name == input_:
                    carbon_factors[tech.name] = stream.co2

        return carbon_factors

    @cached_property
    def fuel_price(self) -> Dict[str, float]:
        """Return the price of each fuel."""
        fuel_prices = {}
        for tech in self.converters:
            input_ = tech.inputs[0]  # Assume only one input per tech

            for stream in self.streams:
                if stream.name == input_:
                    fuel_prices[tech.name] = stream.price

        return fuel_prices

    @cached_property
    def feed_in(self) -> Dict[str, float]:
        """The export price of each output stream."""
        return {stream.name: stream.export_price
                for stream in self.streams
                if stream.is_output}

    @property
    def storage_capacity(self):
        """The capacity of each storage."""
        return self._get_from_storages('capacity')

    @cached_property
    def storage_charge(self) -> Dict[str, float]:
        """The maximum charge of each storage."""
        return self._get_from_storages('max_charge')

    @cached_property
    def storage_discharge(self) -> Dict[str, float]:
        """The maximum discharge of each storage."""
        return self._get_from_storages('max_discharge')

    @cached_property
    def storage_loss(self) -> Dict[str, float]:
        """The decay of each storage."""
        return self._get_from_storages('decay')

    @cached_property
    def storage_ef_ch(self) -> Dict[str, float]:
        """The charging efficiency of each storage."""
        return self._get_from_storages('charge_efficiency')

    @cached_property
    def storage_ef_disch(self) -> Dict[str, float]:
        """The discharging efficiency of each storage."""
        return self._get_from_storages('discharge_efficiency')

    @cached_property
    def storage_min_soc(self) -> Dict[str, float]:
        """The minimum state of charge of each storage."""
        return self._get_from_storages('min_state')

    @cached_property
    def storage_life(self) -> Dict[str, float]:
        """The life time in years of each storage."""
        return self._get_from_storages('lifetime')

    @cached_property
    def storage_lin_cost(self) -> Dict[str, float]:
        """The linear cost of each storage."""
        return self._get_from_storages('cost')

    def _get_from_storages(self, attribute: str) -> Dict[str, T]:
        """Return the attribute of each storage as a dictionary."""
        return {storage.name: getattr(storage, attribute)
                for storage in self.storages}

    @cached_property
    def storage_npv(self) -> Dict[str, float]:
        """The net present value of each storage."""
        return {storage.name: self._calculate_npv(storage.lifetime)
                for storage in self.storages}
