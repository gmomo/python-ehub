"""
Provides a class for encapsulating an energy hub model.
"""
from itertools import product
from typing import Iterable
import logging

import excel_to_request_format
from data_formats import response_format
from data_formats.request_format import Storage
from energy_hub.input_data import InputData
from energy_hub.param_var import ConstantOrVar
from energy_hub.utils import constraint, constraint_list
from pylp import RealVariable, IntegerVariable, BinaryVariable
import pylp

DOMAIN_TO_VARIABLE = {
    'Continuous': RealVariable,
    'Integer': IntegerVariable,
    'Binary': BinaryVariable,
}

DEFAULT_SOLVER_SETTINGS = {
    'name': 'glpk',
    'options': {
        'mipgap': 0.05,
    },
}

BIG_M = 5000
TIME_HORIZON = 20
MAX_CARBON = 650000
MAX_SOLAR_AREA = 500


class InfeasibleConstraintError(Exception):
    """A constraint will always be false."""
    def __init__(self, constraint_name: str = None, arguments: tuple = None) -> None:
        if arguments is None:
            message = f'Constraint {constraint_name} is False'
        else:
            message = f'Constraint {constraint_name}{arguments} is False'

        super().__init__(message)


class EHubModel:
    """
    Represents a black-box Energy Hub.
    """

    def __init__(self, *, excel=None, request=None):
        """Create a new Energy Hub using some input data.

        Args:
            excel: The Excel 2003 file for input data
            request: The request format dictionary
        """
        self._data = None

        if excel:
            request = excel_to_request_format.convert(excel)

        if request:
            self._data = InputData(request)

        if self._data:
            self._constraints = []
            self._prepare()
        else:
            raise RuntimeError("Can't create a hub with no data.")

    def _prepare(self):
        self._create_sets()

        self._add_variables()
        self._add_parameters()
        self._add_constraints()

    def _create_sets(self):
        data = self._data

        self.streams = data.stream_names

        self.time = range(data.num_time_steps)

        self.technologies = data.converter_names
        self.techs_without_grid = data.converter_names_without_grid

        self.storages = data.storage_names
        self.output_streams = data.output_stream_names
        self.demands = data.output_stream_names

        self.techs = data.techs
        self.solar_techs = data.solar_techs
        self.disp_techs = data.disp_techs
        self.roof_tech = data.roof_tech

        self.part_load = data.part_load_techs

    @property
    def objective(self):
        """The objective "function" of the model."""
        return self.total_cost

    @constraint()
    def calculate_total_cost(self):
        """A constraint for calculating the total cost."""
        cost = (self.investment_cost
                + self.operating_cost
                + self.maintenance_cost)
        income = self.income_from_exports

        return self.total_cost == cost - income

    @constraint()
    def calculate_total_carbon(self):
        """A constraint for calculating the total carbon produced."""
        total_carbon = 0
        for tech in self.technologies:
            total_energy_imported = sum(self.energy_imported[t][tech]
                                        for t in self.time)
            carbon_factor = self.CARBON_FACTORS[tech]

            total_carbon += carbon_factor * total_energy_imported

        return self.total_carbon == total_carbon

    @constraint()
    def calculate_investment_cost(self):
        """A constraint for calculating the investment cost."""
        storage_cost = sum(self.NET_PRESENT_VALUE_STORAGE[storage]
                           * self.LINEAR_STORAGE_COSTS[storage]
                           * self.storage_capacity[storage]
                           for storage in self.storages)

        tech_cost = sum(self.NET_PRESENT_VALUE_TECH[tech]
                        * self.LINEAR_CAPITAL_COSTS[tech]
                        * self.capacities[tech]
                        + (self.FIXED_CAPITAL_COSTS[tech]
                           * self.is_installed[tech])
                        for tech in self.techs_without_grid)

        cost = tech_cost + storage_cost
        return self.investment_cost == cost

    @constraint()
    def calculate_income_from_exports(self):
        """A constraint for calculating the income from exported streams."""
        income = 0
        for energy in self.output_streams:
            total_energy_exported = sum(self.energy_exported[t][energy]
                                        for t in self.time)

            income += self.FEED_IN_TARIFFS[energy] * total_energy_exported

        return self.income_from_exports == income

    @constraint()
    def calculate_maintenance_cost(self):
        """A constraint for calculating the maintenance cost."""
        cost = 0
        for t in self.time:
            for tech in self.technologies:
                for energy in self.output_streams:
                    cost += (self.energy_imported[t][tech]
                             * self.CONVERSION_EFFICIENCY[tech][energy]
                             * self.OMV_COSTS[tech])

        return self.maintenance_cost == cost

    @constraint()
    def calculate_operating_cost(self):
        """A constraint for calculating the operating cost."""
        cost = 0
        for tech in self.technologies:
            total_energy_imported = sum(self.energy_imported[t][tech]
                                        for t in self.time)

            cost += self.OPERATING_PRICES[tech] * total_energy_imported

        return self.operating_cost == cost

    @constraint('time', 'storages')
    def storage_level_below_capacity(self, t, storage):
        """
        Ensure the storage's level is below the storage's capacity.

        Args:
            t: A time step
            storage: A storage
        """
        storage_level = self.storage_level[t][storage]
        storage_capacity = self.storage_capacity[storage]

        return storage_level <= storage_capacity

    @constraint('time', 'storages')
    def storage_level_above_minimum(self, t, storage):
        """
        Ensure the storage level is above it's minimum level.

        Args:
            t: A time step
            storage: A storage
        """
        storage_capacity = self.storage_capacity[storage]
        min_soc = self.MIN_STATE_OF_CHARGE[storage]
        storage_level = self.storage_level[t][storage]

        min_storage_level = storage_capacity * min_soc

        return min_storage_level <= storage_level

    @constraint('time', 'storages')
    def cap_storage_discharge_rate(self, t, storage):
        """
        Ensure the discharge rate of a storage is below it's maximum rate.

        Args:
            t: A time step
            storage: A storage
        """
        max_discharge_rate = self.MAX_DISCHARGE_RATE[storage]
        storage_capacity = self.storage_capacity[storage]
        discharge_rate = self.energy_from_storage[t][storage]

        max_rate = max_discharge_rate * storage_capacity

        return discharge_rate <= max_rate

    @constraint('time', 'storages')
    def cap_storage_charge_rate(self, t, storage):
        """
        Ensure the charge rate of a storage is below it's maximum rate.

        Args:
            t: A time step
            storage: A storage
        """
        max_charge_rate = self.MAX_CHARGE_RATE[storage]
        storage_capacity = self.storage_capacity[storage]
        charge_rate = self.energy_to_storage[t][storage]

        max_rate = max_charge_rate * storage_capacity

        return charge_rate <= max_rate

    @constraint('time', 'storages')
    def storage_balance(self, t, storage):
        """
        Calculate the current storage level from the previous level.

        Args:
            t: A time step
            storage: A storage
        """
        # See the storage_level declaration for more details
        next_storage_level = self.storage_level[t + 1][storage]
        current_storage_level = self.storage_level[t][storage]

        storage_standing_loss = self.STORAGE_STANDING_LOSSES[storage]

        discharge_rate = self.DISCHARGING_EFFICIENCY[storage]
        charge_rate = self.CHARGING_EFFICIENCY[storage]

        charge_in = self.energy_to_storage[t][storage]
        charge_out = self.energy_from_storage[t][storage]

        calculated_next_storage_level = (
            ((1 - storage_standing_loss) * current_storage_level)
            + (charge_rate * charge_in)
            - ((1 / discharge_rate) * charge_out)
        )
        return next_storage_level == calculated_next_storage_level

    @constraint('technologies')
    def allow_capacity_when_installed(self, tech):
        """
        Ensure the tech's capacity is relevant if the tech is installed.
        Args:
            tech: A converter
        """
        capacity = self.capacities[tech]
        rhs = self.BIG_M * self.is_installed[tech]
        return capacity <= rhs

    @constraint()
    def roof_tech_area_below_max(self):
        """ Ensure the roof techs are taking up less area than there is roof.
        """
        total_roof_area = sum(self.capacities[roof] for roof in self.roof_tech)

        return total_roof_area <= self.MAX_SOLAR_AREA

    @constraint('time', 'solar_techs', 'output_streams')
    def calculate_solar_energy(self, t, solar_tech, out):
        """
        Calculate the energy from the roof techs per time step.

        Args:
            t: A time step
            solar_tech: A solar converter
            out: An output stream
        """
        conversion_rate = self.CONVERSION_EFFICIENCY[solar_tech][out]

        if conversion_rate <= 0:
            return None

        energy_imported = self.energy_imported[t][solar_tech]
        capacity = self.capacities[solar_tech]

        rhs = self.SOLAR_EM[t] * capacity

        return energy_imported == rhs

    @constraint('time', 'part_load', 'output_streams')
    def import_energy_when_on(self, t, disp, out):
        """
        Only import energy from a dispatch tech if it is on.

        Args:
            t: A time step
            disp: A dispatch tech
            out: An output energy stream
        """
        conversion_rate = self.CONVERSION_EFFICIENCY[disp][out]

        if conversion_rate <= 0:
            return None

        energy_imported = self.energy_imported[t][disp]
        is_on = self.is_on[t][disp]

        lhs = energy_imported * conversion_rate
        rhs = self.BIG_M * is_on

        return lhs <= rhs

    @constraint('time', 'part_load', 'output_streams')
    def part_load_l(self, t, disp, out):
        """
        Args:
            t: A time step
            disp: A dispatch tech
            out: An output energy stream
        """
        conversion_rate = self.CONVERSION_EFFICIENCY[disp][out]

        if conversion_rate <= 0:
            return None

        part_load = self.PART_LOAD[disp][out]
        capacity = self.capacities[disp]
        energy_imported = self.energy_imported[t][disp]
        is_on = self.is_on[t][disp]

        lhs = part_load * capacity

        rhs = (energy_imported * conversion_rate
               + self.BIG_M * (1 - is_on))
        return lhs <= rhs

    def _get_storages_from_stream(self, out: str) -> Iterable[Storage]:
        return (storage for storage in self._data.storages
                if storage.stream == out)

    @constraint('time', 'demands')
    def loads_balance(self, t, demand):
        """
        Ensure the loads and exported energy is below the produced energy.

        Args:
            t: A time step
            demand: An output stream
        """
        load = self.LOADS[demand][t]
        energy_exported = self.energy_exported[t][demand]

        lhs = load + energy_exported

        total_q_out = 0
        total_q_in = 0
        for storage in self._get_storages_from_stream(demand):
            total_q_in += self.energy_to_storage[t][storage.name]
            total_q_out += self.energy_from_storage[t][storage.name]

        energy_in = 0
        for tech in self.technologies:
            energy_imported = self.energy_imported[t][tech]
            conversion_rate = self.CONVERSION_EFFICIENCY[tech][demand]

            energy_in += energy_imported * conversion_rate

        rhs = (total_q_out - total_q_in) + energy_in

        return lhs <= rhs

    @constraint('time', 'technologies', 'output_streams')
    def energy_imported_below_capacity(self, t, tech, output_type):
        """
        Ensure the energy imported by a tech is less than its capacity.

        Args:
            t: A time step
            tech: A converter
            output_type: An output stream
        """
        conversion_rate = self.CONVERSION_EFFICIENCY[tech][output_type]

        if conversion_rate <= 0 or tech in self.solar_techs:
            return None

        energy_imported = self.energy_imported[t][tech]
        capacity = self.capacities[tech]

        energy_in = energy_imported * conversion_rate

        return energy_in <= capacity

    def _add_constraint_to_constraints(self, constraint_):
        # Comparing to True and False is bad, but expression can
        # be many types
        if constraint_ is True:
            return
        elif constraint_ is False:
            raise InfeasibleConstraintError()
        elif constraint_ is not None:
            self.constraints.append(constraint_)

    def _add_indexed_constraints(self):
        """Add all the constraint decorated functions to the model."""
        methods = [getattr(self, method)
                   for method in dir(self)
                   if callable(getattr(self, method))]
        rules = (rule for rule in methods if hasattr(rule, 'is_constraint'))

        for rule in rules:
            logging.info(f'Found indexed constraint: {rule.__name__}')
            if not rule.enabled:
                logging.info(f'{rule.__name__} is not enabled')
                continue

            logging.info(f'{rule.__name__} is enabled')

            if not rule.args:
                # Constraint is not indexed by anything
                expression = rule()

                try:
                    self._add_constraint_to_constraints(expression)
                except InfeasibleConstraintError:
                    raise InfeasibleConstraintError(rule.__name__)
            else:
                sets = [getattr(self, arg) for arg in rule.args]

                for indices in product(*sets):
                    expression = rule(*indices)

                    try:
                        self._add_constraint_to_constraints(expression)
                    except InfeasibleConstraintError:
                        raise InfeasibleConstraintError(rule.__name__, indices)

    def _add_constraint_lists(self):
        methods = [getattr(self, method)
                   for method in dir(self)
                   if callable(getattr(self, method))]
        rules = (rule for rule in methods
                 if hasattr(rule, 'is_constraint_list'))

        for rule in rules:
            logging.info(f'Found constraint list: {rule.__name__}')
            if not rule.enabled:
                logging.info(f'{rule.__name__} is NOT enabled')
                continue
            logging.info(f'{rule.__name__} is enabled')

            for expression in rule():
                self.constraints.append(expression)

    @constraint_list()
    def capacity_constraints(self):
        """Ensure the capacities are within their given bounds."""
        for capacity in self._data.capacities:
            variable = getattr(self, capacity.name)

            lower_bound = capacity.lower_bound
            upper_bound = capacity.upper_bound

            if lower_bound is not None and upper_bound is not None:
                yield lower_bound <= variable <= upper_bound
            elif lower_bound is not None and upper_bound is None:
                yield lower_bound <= variable
            elif lower_bound is None and upper_bound is not None:
                yield variable <= upper_bound
            else:
                raise RuntimeError

    def _add_constraints(self):
        self._add_indexed_constraints()
        self._add_constraint_lists()

    @constraint_list()
    def storage_looping(self):
        """Ensure that the storage level at the beginning is equal to it's end
        level."""
        for storage in self._data.storages:
            # See the storage_level declaration
            last_entry = list(self.time)[-1] + 1
            first_entry = list(self.time)[0]

            start_level = self.storage_level[first_entry][storage.name]
            end_level = self.storage_level[last_entry][storage.name]

            yield start_level == end_level

    def _add_capacity_variables(self):
        for capacity in self._data.capacities:
            domain = capacity.domain
            name = capacity.name

            try:
                variable = DOMAIN_TO_VARIABLE[domain]()
            except KeyError:
                raise ValueError(
                    f'Cannot create variable of type: {domain}. Can only be: '
                    f'{list(DOMAIN_TO_VARIABLE.keys())}'
                )

            setattr(self, name, variable)

    @constraint()
    def operating_cost_above_zero(self):
        """The operating cost should be positive."""
        return self.operating_cost >= 0

    @constraint()
    def maintenance_cost_above_zero(self):
        """The maintenance cost should be positive."""
        return self.maintenance_cost >= 0

    @constraint()
    def income_from_exports_above_zero(self):
        """The income from exports should be positive."""
        return self.income_from_exports >= 0

    @constraint()
    def investment_cost_above_zero(self):
        """The investment cost should be positive."""
        return self.investment_cost >= 0

    @constraint('time', 'technologies')
    def energy_imported_is_above_zero(self, t, tech):
        """Energy imported should be positive."""
        return self.energy_imported[t][tech] >= 0

    @constraint('time', 'output_streams')
    def energy_exported_is_above_zero(self, t, output_stream):
        """Energy exported should be positive."""
        return self.energy_exported[t][output_stream] >= 0

    @constraint('time', 'storages')
    def energy_to_storage_above_zero(self, t, storage):
        """Energy to storage should be positive."""
        return self.energy_to_storage[t][storage] >= 0

    @constraint('time', 'storages')
    def energy_from_storage_above_zero(self, t, storage):
        """Energy from the storages should be positive."""
        return self.energy_from_storage[t][storage] >= 0

    @constraint('time', 'storages')
    def storage_level_above_zero(self, t, storage):
        """Storages' levels should be above zero."""
        return self.storage_level[t][storage] >= 0

    @property
    def constraints(self):
        """The list of constraints on the model."""
        return self._constraints

    @constraints.setter
    def constraints(self, constraints):
        """Set the constraints of the model."""
        self._constraints = constraints

    def _add_variables(self):
        self._add_capacity_variables()

        # Global variables
        self.energy_imported = {
            t: {tech: RealVariable() for tech in self.technologies}
            for t in self.time
        }
        self.energy_exported = {
            t: {out: RealVariable() for out in self.output_streams}
            for t in self.time
        }

        self.capacities = ConstantOrVar(self.technologies,
                                        model=self,
                                        values=self._data.converters_capacity)

        self.is_installed = {tech: BinaryVariable()
                             for tech in self.technologies}

        self.is_on = {
            t: {tech: BinaryVariable() for tech in self.technologies}
            for t in self.time
        }

        self.total_cost = RealVariable()
        self.operating_cost = RealVariable()
        self.maintenance_cost = RealVariable()
        self.income_from_exports = RealVariable()
        self.investment_cost = RealVariable()

        self.total_carbon = RealVariable()

        self.energy_to_storage = {
            t: {storage: RealVariable() for storage in self.storages}
            for t in self.time
        }
        self.energy_from_storage = {
            t: {storage: RealVariable() for storage in self.storages}
            for t in self.time
        }

        # Time steps are not points in time, but time intervals. Time step 0 is
        # from time 0 up to, but not including, time 1. Time step 1 is from
        # time 1 up to time 2, and so on.
        # But for storages, we measure the level at each point in time. So for
        # time step 0, we are measuring it at that point in time. The level
        # for time step 1 is at time point 1, and so on.
        # So we need an additional time "step" to measure the level after
        # everything has happened in the last time step.
        #
        #      time step 0   time step 1   time step 2
        #           |             |             |
        #    |-------------|-------------|-------------|---...
        #  time 0        time 1        time 2        time 3
        #
        self.storage_level = {
            t: {storage: RealVariable() for storage in self.storages}
            for t in range(len(self.time) + 1)
        }

        self.storage_capacity = ConstantOrVar(
            self.storages, model=self, values=self._data.storage_capacity
        )

    def _add_parameters(self):
        data = self._data

        # coupling matrix & Technical parameters
        # coupling matrix technology efficiencies
        self.CONVERSION_EFFICIENCY = data.c_matrix

        self.MAX_CHARGE_RATE = data.storage_charge
        self.MAX_DISCHARGE_RATE = data.storage_discharge
        self.STORAGE_STANDING_LOSSES = data.storage_loss
        self.CHARGING_EFFICIENCY = data.storage_ef_ch
        self.DISCHARGING_EFFICIENCY = data.storage_ef_disch
        self.MIN_STATE_OF_CHARGE = data.storage_min_soc
        # PartloadInput
        self.PART_LOAD = data.part_load

        # carbon factors
        self.CARBON_FACTORS = data.carbon_factors
        self.MAX_CARBON = MAX_CARBON

        # Cost parameters
        # Technologies capital costs
        self.LINEAR_CAPITAL_COSTS = data.linear_cost
        self.FIXED_CAPITAL_COSTS = data.fixed_capital_costs
        self.LINEAR_STORAGE_COSTS = data.storage_lin_cost
        # Operating prices technologies
        self.OPERATING_PRICES = data.fuel_price
        self.FEED_IN_TARIFFS = data.feed_in
        # Maintenance costs
        self.OMV_COSTS = data.variable_maintenance_cost

        # Declaring Global Parameters
        self.TIME_HORIZON = TIME_HORIZON

        self.BIG_M = BIG_M

        self.INTEREST_RATE = data.interest_rate

        self.MAX_SOLAR_AREA = MAX_SOLAR_AREA

        # loads
        self.LOADS = data.loads
        self.SOLAR_EM = data.solar_data

        self.NET_PRESENT_VALUE_TECH = data.tech_npv
        self.NET_PRESENT_VALUE_STORAGE = data.storage_npv

    def _public_attributes(self):
        return {name: value
                for name, value in self.__dict__.items()
                if not name.startswith('_')}

    def solve(self, solver_settings: dict = None, is_verbose: bool = False):
        """
        Solve the model.

        Args:
            solver_settings: The config options for the solver
            is_verbose: Makes it so the solver prints everything

        Returns:
            The results
        """
        if solver_settings is None:
            solver_settings = DEFAULT_SOLVER_SETTINGS

        solver = solver_settings["name"]
        options = solver_settings["options"]
        if options is None:
            options = {}

        status = pylp.solve(objective=self.objective,
                            constraints=self.constraints,
                            minimize=True,
                            solver=solver,
                            verbose=is_verbose)

        attributes = self._public_attributes()
        return response_format.create_response(status, attributes)
