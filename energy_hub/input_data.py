"""
Provides functionality for handling the request format for using in the
EHubModel.
"""

from collections import defaultdict
from typing import List, Optional, Dict, TypeVar, Tuple

import pandas as pd
import numpy as np

from energy_hub.capacity import Capacity
from energy_hub.utils import cached_property
from energy_hub import Converter, Stream, Storage, TimeSeries

T = TypeVar('T')

AXIS_ROWS = 0
AXIS_COLUMNS = 1


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

    @cached_property
    def converters(self) -> List[Converter]:
        """The list of converters."""
        def _make(converter):
            capacity = self._get_capacity(converter['capacity'])

            return Converter(converter, capacity)

        return [_make(converter) for converter in self._request['converters']]

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

    @cached_property
    def output_stream_names(self):
        """The sorted list of output streams names."""
        names = (output for tech in self.converters for output in tech.outputs)

        return sorted(set(names))

    @cached_property
    def demand_data(self) -> pd.DataFrame:
        """The data for all demand streams as a matrix."""
        demands = [demand for demand in self.time_series_list
                   if demand.is_demand]

        test = pd.DataFrame()
        for demand in demands:
            name = demand.name
            data = demand.data

            data = pd.DataFrame(data, index=range(len(data)), columns=[name])
            test = pd.concat([test, data], axis=1)

        return test

    @property
    def demands(self) -> Dict[Tuple[int, int], float]:
        """The data for all demands as a dictionary that is indexed by (time,
        demand time series ID)."""
        demands = [time_series for time_series in self.time_series_list
                   if time_series.is_demand]

        return {(row, column): value
                for column, demand in enumerate(demands, start=1)
                for row, value in demand.pyomo_data.items()}

    @cached_property
    def solar_data(self) -> Dict[int, float]:
        """The data for the solar time series as a dictionary that is indexed
        by time."""
        solar = [time_series for time_series in self.time_series_list
                 if time_series.is_solar][0]  # Assume there is only one

        return solar.pyomo_data

    @cached_property
    def chp_list(self) -> List[int]:
        """The IDs of Combined Heat and Power converters."""
        return [i for i, tech in enumerate(self.converters, start=1)
                if tech.is_chp]

    @cached_property
    def roof_tech(self) -> List[int]:
        """The IDs of the converters that can be put on a roof."""
        return [i for i, tech in enumerate(self.converters, start=1)
                if tech.is_roof_tech]

    @property
    def c_matrix(self) -> Dict[Tuple[int, int], float]:
        """Return a dictionary-format for the C matrix.

        The keys are of the form (conveter ID, output stream ID).
        """
        tech_outputs = self.output_stream_names

        c_matrix = pd.DataFrame(0, index=range(1, len(self.converters) + 1),
                                columns=tech_outputs, dtype=float)
        for i, tech in enumerate(self.converters, start=1):
            efficiency = tech.efficiency
            output_ratio = tech.output_ratio

            for input_ in tech.inputs:
                # This is just to make it work
                if input_ == 'Grid':
                    c_matrix['Elec'][i] = -1
            for output in tech.outputs:
                if output == 'Elec':
                    value = efficiency
                else:
                    value = efficiency * output_ratio
                c_matrix[output][i] = value

        c_matrix.columns = range(1, len(c_matrix.columns) + 1)

        return {(row, col): value
                for col, column in c_matrix.to_dict().items()
                for row, value in column.items()}

    @cached_property
    def solar_techs(self) -> List[int]:
        """The IDs of the solar converters."""
        return [i for i, tech in enumerate(self.converters, start=1)
                if tech.is_solar]

    @cached_property
    def part_load(self) -> Dict[Tuple[int, int], float]:
        """Return the part load for each tech and each of its outputs."""
        part_load_techs = [(i, tech)
                           for i, tech in enumerate(self.converters, start=1)
                           if not (tech.is_grid or tech.is_solar)]
        output_streams = self.output_stream_names

        part_load = defaultdict(float)  # type: Dict[Tuple[int, int], float]
        for tech_index, tech in part_load_techs:
            for output_index, output_stream in enumerate(output_streams, start=1):
                if output_stream in tech.outputs:
                    min_load = tech.min_load
                    if min_load is not None:
                        part_load[tech_index, output_index] = min_load

        return part_load

    @cached_property
    def max_capacity(self) -> Dict[int, float]:
        """The max capacity of non-solar converter."""
        return {i: tech.max_capacity
                for i, tech in enumerate(self.converters, start=1)
                if not (tech.is_grid or tech.is_solar)}

    @property
    def disp_techs(self) -> List[int]:
        """The IDs of the dispatch converters."""
        return [i for i, tech in enumerate(self.converters, start=1)
                if tech.is_dispatch]

    @property
    def part_load_techs(self) -> List[int]:
        """The IDs of the converters that have a part load."""
        return [i for i, tech in enumerate(self.converters, start=1)
                if tech.has_part_load]

    @cached_property
    def linear_cost(self) -> Dict[Tuple[int, int], float]:
        """Return the linear cost for each tech and each of its outputs."""
        output_streams = self.output_stream_names

        linear_cost = {}
        for row, tech in enumerate(self.converters, start=1):
            for column, output_stream in enumerate(output_streams, start=1):
                linear_cost[row, column] = 0.0

                # If the tech outputs electricity, remove the other costs.  No
                # idea why this happens.
                #
                # Eg: If a tech outputs Elec and Heat, the linear cost is only
                # set for Elec and not Heat.
                if 'Elec' in tech.outputs and len(tech.outputs) > 1 and output_stream != 'Elec':
                    continue

                capital_cost = tech.get_capital_cost(output_stream)
                if capital_cost is not None:
                    linear_cost[row, column] = capital_cost

        return linear_cost

    @cached_property
    def dispatch_demands(self) -> np.ndarray:
        """I have no idea what this is for."""
        # Find which is the primary input for capacity
        chp_techs = [tech for tech in self.converters if tech.is_chp]

        num_rows = len(chp_techs)
        num_columns = len(self.output_stream_names)
        dispatch_demands = np.zeros((num_rows, num_columns), dtype=int)

        for row, chp_tech in enumerate(chp_techs):
            for index, output in enumerate(self.output_stream_names, start=1):
                if output in chp_tech.outputs:
                    for col in range(index - 1, num_columns):
                        dispatch_demands[row, col - 1] = index

        return dispatch_demands

    @cached_property
    def interest_rate(self) -> float:
        """The interest rate."""
        return self._request['general']['interest_rate']

    @cached_property
    def life_time(self) -> Dict[int, float]:
        """The life time of each converter."""
        return {i: tech.lifetime
                for i, tech in enumerate(self.converters, start=1)
                if not tech.is_grid}

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
    def tech_npv(self) -> Dict[int, float]:
        """The net present value of each converter."""
        return {i: round(self._calculate_npv(tech.lifetime), 4)
                for i, tech in enumerate(self.converters, start=1)
                if not tech.is_grid}

    @cached_property
    def var_maintenance_cost(self) -> Dict[int, float]:
        """The variable maintenance cost of each converter."""
        return {i: tech.usage_maintenance_cost
                for i, tech in enumerate(self.converters, start=1)}

    @cached_property
    def carb_factors(self) -> Dict[int, float]:
        """The carbon factor of each converter."""
        carbon_factors = {}
        for i, tech in enumerate(self.converters, start=1):
            input_ = tech.inputs[0]  # Assume only one input per tech

            for stream in self.streams:
                if stream.name == input_:
                    carbon_factors[i] = stream.co2

        return carbon_factors

    @cached_property
    def fuel_price(self) -> Dict[int, float]:
        """ Returns the carbon price of each fuel. """
        fuel_prices = {}
        for i, tech in enumerate(self.converters, start=1):
            input_ = tech.inputs[0]  # Assume only one input per tech

            for stream in self.streams:
                if stream.name == input_:
                    fuel_prices[i] = stream.price

        return fuel_prices

    @cached_property
    def feed_in(self) -> Dict[int, float]:
        """The export price of each output stream."""
        return {i: stream.export_price
                for i, stream in enumerate(self.streams, start=1)
                if stream.is_output}

    @cached_property
    def storage_charge(self) -> Dict[int, float]:
        """The maximum charge of each storage."""
        return self._get_from_storages('max_charge')

    @cached_property
    def storage_discharge(self) -> Dict[int, float]:
        """The maximum discharge of each storage."""
        return self._get_from_storages('max_discharge')

    @cached_property
    def storage_loss(self) -> Dict[int, float]:
        """The decay of each storage."""
        return self._get_from_storages('decay')

    @cached_property
    def storage_ef_ch(self) -> Dict[int, float]:
        """The charging efficiency of each storage."""
        return self._get_from_storages('charge_efficiency')

    @cached_property
    def storage_ef_disch(self) -> Dict[int, float]:
        """The discharging efficiency of each storage."""
        return self._get_from_storages('discharge_efficiency')

    @cached_property
    def storage_min_soc(self) -> Dict[int, float]:
        """The minimum state of charge of each storage."""
        return self._get_from_storages('min_state')

    @cached_property
    def storage_life(self) -> Dict[int, float]:
        """The life time in years of each storage."""
        return self._get_from_storages('lifetime')

    @cached_property
    def storage_lin_cost(self) -> Dict[int, float]:
        """The linear cost of each storage."""
        return self._get_from_storages('cost')

    def _get_from_storages(self, attribute: str) -> Dict[int, T]:
        """Return the attribute of each storage as a dictionary."""
        return {i: getattr(storage, attribute)
                for i, storage in enumerate(self.storages, start=1)}

    @cached_property
    def storage_npv(self) -> Dict[int, float]:
        """The net present value of each storage."""
        return {i: self._calculate_npv(storage.lifetime)
                for i, storage in enumerate(self.storages, start=1)}
