"""
Provides a class for encapsulating an energy hub model.
"""
from typing import Iterable

from pyomo.core.base import (
    ConcreteModel, Set, Param, NonNegativeReals, Binary, Var, Reals,
    Constraint, ConstraintList, Objective, minimize,
)
from pyomo.opt import SolverFactory, SolverManagerFactory

# This import is used to find solvers.
# noinspection PyUnresolvedReferences
# pylint: disable=unused-import
import pyomo.environ

import excel_to_request_format
from data_formats import response_format
from data_formats.request_format import Storage
from energy_hub.input_data import InputData
from energy_hub.param_var import ConstantOrVar
from energy_hub.range_set import RangeSet
from energy_hub.utils import constraint, constraint_list

DEFAULT_SOLVER_SETTINGS = {
    'name': 'glpk',
    'options': {
        'mipgap': 0.05,
    },
}

BIG_M = 5000
MAX_SOLAR_AREA = 500


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
        self._model = ConcreteModel()
        self._data = None

        if excel:
            request = excel_to_request_format.convert(excel)

        if request:
            self._data = InputData(request, self._model)

        if self._data:
            self._prepare()
        else:
            raise RuntimeError("Can't create a hub with no data.")

    def _prepare(self):
        self._create_sets()

        self._add_variables()
        self._add_parameters()
        self._add_constraints()
        self._add_objective()

    def _create_sets(self):
        data = self._data
        model = self._model

        num_time_steps = data.num_time_steps

        model.streams = Set(initialize=data.stream_names)

        model.time = RangeSet(stop=num_time_steps)
        model.sub_time = RangeSet(start=1, stop=num_time_steps,
                                  within=model.time)

        model.technologies = Set(initialize=data.converter_names)
        model.techs_without_grid = Set(
            initialize=data.converter_names_without_grid,
            within=model.technologies
        )

        model.storages = Set(initialize=data.storage_names)
        model.energy_carrier = Set(initialize=data.output_stream_names)
        model.demands = Set(initialize=data.output_stream_names)

        model.techs = Set(initialize=data.max_capacity_names,
                          within=model.technologies)
        model.solar_techs = Set(initialize=data.solar_techs,
                                within=model.technologies)
        model.disp_techs = Set(initialize=data.disp_techs,
                               within=model.technologies)
        model.roof_tech = Set(initialize=data.roof_tech,
                              within=model.technologies)

        model.part_load = Set(initialize=data.part_load_techs,
                              within=model.technologies)

    def _add_objective(self):
        def _rule(model):
            return model.total_cost

        self._model.total_cost_objective = Objective(rule=_rule, sense=minimize)

    @staticmethod
    @constraint()
    def calculate_total_cost(model: ConcreteModel) -> bool:
        """
        A constraint for calculating the total cost.

        Args:
            model: The Pyomo model
        """
        cost = (model.investment_cost
                + model.operating_cost
                + model.maintenance_cost)
        income = model.income_from_exports

        return model.total_cost == cost - income

    @staticmethod
    @constraint()
    def calculate_total_carbon(model):
        """
        A constraint for calculating the total carbon produced.

        Args:
            model: The Pyomo model
        """
        total_carbon = 0
        for tech in model.technologies:
            total_energy_imported = sum(model.energy_imported[t, tech]
                                        for t in model.time)
            carbon_factor = model.CARBON_FACTORS[tech]

            total_carbon += carbon_factor * total_energy_imported

        return model.total_carbon == total_carbon

    @staticmethod
    @constraint()
    def calculate_investment_cost(model):
        """
        A constraint for calculating the investment cost.

        Args:
            model: The Pyomo model
        """
        storage_cost = sum(model.NET_PRESENT_VALUE_STORAGE[storage]
                           * model.LINEAR_STORAGE_COSTS[storage]
                           * model.storage_capacity[storage]
                           for storage in model.storages)

        tech_cost = sum(model.NET_PRESENT_VALUE_TECH[tech]
                        * model.LINEAR_CAPITAL_COSTS[tech]
                        * model.capacities[tech]
                        + (model.FIXED_CAPITAL_COSTS[tech]
                           * model.Ytechnologies[tech])
                        for tech in model.techs_without_grid)

        cost = tech_cost + storage_cost
        return model.investment_cost == cost

    @staticmethod
    @constraint()
    def calculate_income_from_exports(model):
        """
        A constraint for calculating the income from exported streams.

        Args:
            model: The Pyomo model
        """
        income = 0
        for energy in model.energy_carrier:
            total_energy_exported = sum(model.energy_exported[t, energy]
                                        for t in model.time)

            income += model.FEED_IN_TARIFFS[energy] * total_energy_exported

        return model.income_from_exports == income

    @staticmethod
    @constraint()
    def calculate_maintenance_cost(model):
        """
        A constraint for calculating the maintenance cost.

        Args:
            model: The Pyomo model
        """
        cost = 0
        for t in model.time:
            for tech in model.technologies:
                for energy in model.energy_carrier:
                    cost += (model.energy_imported[t, tech]
                             * model.CONVERSION_EFFICIENCY[tech, energy]
                             * model.OMV_COSTS[tech])

        return model.maintenance_cost == cost

    @staticmethod
    @constraint()
    def calculate_operating_cost(model):
        """
        A constraint for calculating the operating cost.

        Args:
            model: The Pyomo model
        """
        cost = 0
        for tech in model.technologies:
            total_energy_imported = sum(model.energy_imported[t, tech]
                                        for t in model.time)

            cost += model.OPERATING_PRICES[tech] * total_energy_imported

        return model.operating_cost == cost

    @staticmethod
    @constraint('time', 'storages')
    def storage_capacity(model, t, storage):
        """
        Ensure the storage level is below the storage's capacity.

        Args:
            model: The Pyomo model
            t: A time step
            storage: A storage
        """
        storage_level = model.storage_level[t, storage]
        storage_capacity = model.storage_capacity[storage]

        return storage_level <= storage_capacity

    @staticmethod
    @constraint('time', 'storages')
    def storage_min_state(model, t, storage):
        """
        Ensure the storage level is above it's minimum level.\

        Args:
            model: The Pyomo model
            t: A time step
            storage: A storage
        """
        storage_capacity = model.storage_capacity[storage]
        min_soc = model.MIN_STATE_OF_CHARGE[storage]
        storage_level = model.storage_level[t, storage]

        min_storage_level = storage_capacity * min_soc

        return min_storage_level <= storage_level

    @staticmethod
    @constraint('time', 'storages')
    def storage_discharge_rate(model, t, storage):
        """
        Ensure the discharge rate of a storage is below it's maximum rate.

        Args:
            model: The Pyomo model
            t: A time step
            storage: A storage
        """
        max_discharge_rate = model.MAX_DISCHARGE_RATE[storage]
        storage_capacity = model.storage_capacity[storage]
        discharge_rate = model.energy_from_storage[t, storage]

        max_rate = max_discharge_rate * storage_capacity

        return discharge_rate <= max_rate

    @staticmethod
    @constraint('time', 'storages')
    def storage_charge_rate(model, t, storage):
        """
        Ensure the charge rate of a storage is below it's maximum rate.

        Args:
            model: The Pyomo model
            t: A time step
            storage: A storage
        """
        max_charge_rate = model.MAX_CHARGE_RATE[storage]
        storage_capacity = model.storage_capacity[storage]
        charge_rate = model.energy_to_storage[t, storage]

        max_rate = max_charge_rate * storage_capacity

        return charge_rate <= max_rate

    @staticmethod
    @constraint('sub_time', 'storages')
    def storage_balance(model, t, storage):
        """
        Calculate the current storage level from the previous level.

        Args:
            model: The Pyomo model
            t: A time step
            storage: A storage
        """
        current_storage_level = model.storage_level[t, storage]
        previous_storage_level = model.storage_level[t - 1, storage]

        storage_standing_loss = model.STORAGE_STANDING_LOSSES[storage]

        discharge_rate = model.DISCHARGING_EFFICIENCY[storage]
        charge_rate = model.CHARGING_EFFICIENCY[storage]

        q_in = model.energy_to_storage[t, storage]
        q_out = model.energy_from_storage[t, storage]

        calculated_level = (
            ((1 - storage_standing_loss) * previous_storage_level)
            + (charge_rate * q_in)
            - ((1 / discharge_rate) * q_out)
        )
        return current_storage_level == calculated_level

    @staticmethod
    @constraint('technologies')
    def fix_cost_constant(model, tech):
        """
        Args:
            model: The Pyomo model
            tech: A converter
        """
        capacity = model.capacities[tech]
        rhs = model.BIG_M * model.Ytechnologies[tech]
        return capacity <= rhs

    @staticmethod
    @constraint('roof_tech')
    def roof_area(model, roof):
        """
        Ensure the roof techs are taking up less area than there is roof.

        Args:
            model: The Pyomo model
            roof: A roof converter
        """
        roof_area = model.capacities[roof]

        return roof_area <= model.MAX_SOLAR_AREA

    @staticmethod
    @constraint('time', 'solar_techs', 'energy_carrier')
    def solar_input(model, t, solar_tech, out):
        """
        Calculate the energy from the roof techs per time step.

        Args:
            model: The Pyomo model
            t: A time step
            solar_tech: A solar converter
            out:
        """
        conversion_rate = model.CONVERSION_EFFICIENCY[solar_tech, out]

        if conversion_rate <= 0:
            return Constraint.Skip

        energy_imported = model.energy_imported[t, solar_tech]
        capacity = model.capacities[solar_tech]

        rhs = model.SOLAR_EM[t] * capacity

        return energy_imported == rhs

    @staticmethod
    @constraint('time', 'part_load', 'energy_carrier')
    def part_load_u(model, t, disp, out):
        """
        Args:
            model: The Pyomo model
            t: A time step
            disp: A dispatch tech
            out:
        """
        conversion_rate = model.CONVERSION_EFFICIENCY[disp, out]

        if conversion_rate <= 0:
            return Constraint.Skip

        energy_imported = model.energy_imported[t, disp]

        lhs = energy_imported * conversion_rate
        rhs = model.BIG_M * model.Yon[t, disp]

        return lhs <= rhs

    @staticmethod
    @constraint('time', 'part_load', 'energy_carrier')
    def part_load_l(model, t, disp, out):
        """
        Args:
            model: The Pyomo model
            t: A time step
            disp: A dispatch tech
            out:
        """
        conversion_rate = model.CONVERSION_EFFICIENCY[disp, out]

        if conversion_rate <= 0:
            return Constraint.Skip

        part_load = model.PART_LOAD[disp, out]
        capacity = model.capacities[disp]
        energy_imported = model.energy_imported[t, disp]

        lhs = part_load * capacity

        rhs = (energy_imported * conversion_rate
               + model.BIG_M * (1 - model.Yon[t, disp]))
        return lhs <= rhs

    @staticmethod
    @constraint('disp_techs')
    def max_capacity(model, tech):
        """
        Args:
            model: The Pyomo model
            tech: A converter
        """
        return model.capacities[tech] <= model.MAX_CAP_TECHS[tech]

    def _get_storages_from_stream(self, out: str) -> Iterable[Storage]:
        return (storage for storage in self._data.storages
                if storage.stream == out)

    @constraint('time', 'demands')
    def loads_balance(self, model, t, demand):
        """
        Args:
            model: The Pyomo model
            t: A time step
            demand: An output stream
        """
        load = model.LOADS[t, demand]
        energy_exported = model.energy_exported[t, demand]

        lhs = load + energy_exported

        total_q_out = 0
        total_q_in = 0
        for storage in self._get_storages_from_stream(demand):
            total_q_in += model.energy_to_storage[t, storage.name]
            total_q_out += model.energy_from_storage[t, storage.name]

        energy_in = 0
        for tech in model.technologies:
            energy_imported = model.energy_imported[t, tech]
            conversion_rate = model.CONVERSION_EFFICIENCY[tech, demand]

            energy_in += energy_imported * conversion_rate

        rhs = (total_q_out - total_q_in) + energy_in

        return lhs <= rhs

    @staticmethod
    @constraint('time', 'technologies', 'energy_carrier')
    def capacity_const(model, t, tech, output_type):
        """
        Args:
            model: The Pyomo model
            t: A time step
            tech: A converter
            output_type: An output stream
        """
        conversion_rate = model.CONVERSION_EFFICIENCY[tech, output_type]

        if conversion_rate <= 0 or tech in model.solar_techs:
            return Constraint.Skip

        energy_imported = model.energy_imported[t, tech]
        capacity = model.capacities[tech]

        energy_in = energy_imported * conversion_rate

        return energy_in <= capacity

    def _add_constraints_new(self):
        """Add all the constraint decorated functions to the model."""
        methods = [getattr(self, method)
                   for method in dir(self)
                   if callable(getattr(self, method))]
        rules = (rule for rule in methods if hasattr(rule, 'is_constraint'))

        for rule in rules:
            if not rule.enabled:
                continue

            name = rule.__name__ + '_constraint'
            args = [getattr(self._model, arg) for arg in rule.args]

            setattr(self._model, name, Constraint(*args, rule=rule))

    def _add_constraint_lists(self):
        methods = [getattr(self, method)
                   for method in dir(self)
                   if callable(getattr(self, method))]
        rules = (rule for rule in methods
                 if hasattr(rule, 'is_constraint_list'))

        for rule in rules:
            if not rule.enabled:
                continue

            name = rule.__name__ + '_constraint_list'

            constraints = ConstraintList()
            for expression in rule():
                constraints.add(expression)

            setattr(self._model, name, constraints)

    @constraint_list()
    def capacity_constraints(self):
        """Ensure the capacities are within their given bounds."""
        for capacity in self._data.capacities:
            variable = getattr(self._model, capacity.name)

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
        self._add_constraints_new()
        self._add_constraint_lists()

    @constraint_list()
    def _add_unknown_storage_constraint(self):
        """Ensure that the storage level at the beginning is equal to it's end
        level."""
        model = self._model

        for storage in self._data.storages:
            last_entry = model.time.last()
            first_entry = model.time.first()

            start_level = model.storage_level[first_entry, storage.name]
            end_level = model.storage_level[last_entry, storage.name]

            yield start_level == end_level

    def _add_capacity_variables(self):
        for capacity in self._data.capacities:
            domain = capacity.domain
            name = capacity.name

            setattr(self._model, name, Var(domain=domain))

    def _add_variables(self):
        data = self._data
        model = self._model

        self._add_capacity_variables()

        # Global variables
        model.energy_imported = Var(model.time, model.technologies,
                                    domain=NonNegativeReals)
        model.energy_exported = Var(model.time, model.energy_carrier,
                                    domain=NonNegativeReals)

        model.capacities = ConstantOrVar(model.technologies,
                                         model=model,
                                         values=data.converters_capacity)

        model.Ytechnologies = Var(model.technologies, domain=Binary)

        model.Yon = Var(model.time, model.technologies, domain=Binary)

        model.total_cost = Var(domain=Reals)
        model.operating_cost = Var(domain=NonNegativeReals)
        model.maintenance_cost = Var(domain=NonNegativeReals)
        model.income_from_exports = Var(domain=NonNegativeReals)
        model.investment_cost = Var(domain=NonNegativeReals)

        model.total_carbon = Var(domain=Reals)

        # Storage variables
        model.energy_to_storage = Var(model.time, model.storages,
                                      domain=NonNegativeReals)
        model.energy_from_storage = Var(model.time, model.storages,
                                        domain=NonNegativeReals)

        model.storage_level = Var(model.time, model.storages,
                                  domain=NonNegativeReals)

        model.storage_capacity = ConstantOrVar(
            model.storages, model=model, values=self._data.storage_capacity
        )

    def _add_parameters(self):
        data = self._data
        model = self._model

        # coupling matrix & Technical parameters
        # coupling matrix technology efficiencies
        model.CONVERSION_EFFICIENCY = Param(model.technologies,
                                            model.streams,
                                            initialize=data.c_matrix)
        model.MAX_CAP_TECHS = ConstantOrVar(model.disp_techs, model=model,
                                            values=data.max_capacity)

        model.MAX_CHARGE_RATE = Param(model.storages,
                                      initialize=data.storage_charge)
        model.MAX_DISCHARGE_RATE = Param(model.storages,
                                         initialize=data.storage_discharge)
        model.STORAGE_STANDING_LOSSES = Param(model.storages,
                                              initialize=data.storage_loss)
        model.CHARGING_EFFICIENCY = Param(model.storages,
                                          initialize=data.storage_ef_ch)
        model.DISCHARGING_EFFICIENCY = Param(model.storages,
                                             initialize=data.storage_ef_disch)
        model.MIN_STATE_OF_CHARGE = Param(model.storages,
                                          initialize=data.storage_min_soc)
        # PartloadInput
        model.PART_LOAD = Param(model.technologies, model.energy_carrier,
                                initialize=data.part_load)

        # carbon factors
        model.CARBON_FACTORS = Param(model.technologies,
                                     initialize=data.carbon_factors)

        # Cost parameters
        # Technologies capital costs
        model.LINEAR_CAPITAL_COSTS = Param(model.technologies,
                                           initialize=data.linear_cost)
        model.FIXED_CAPITAL_COSTS = Param(model.technologies,
                                          initialize=data.fixed_capital_costs)
        model.LINEAR_STORAGE_COSTS = Param(model.storages,
                                           initialize=data.storage_lin_cost)
        # Operating prices technologies
        model.OPERATING_PRICES = Param(model.technologies,
                                       initialize=data.fuel_price)
        model.FEED_IN_TARIFFS = Param(model.energy_carrier,
                                      initialize=data.feed_in)
        # Maintenance costs
        model.OMV_COSTS = Param(model.technologies,
                                initialize=data.variable_maintenance_cost)

        # Declaring Global Parameters

        model.BIG_M = Param(within=NonNegativeReals, initialize=BIG_M)

        model.INTEREST_RATE = Param(within=NonNegativeReals,
                                    initialize=data.interest_rate)

        model.MAX_SOLAR_AREA = Param(initialize=MAX_SOLAR_AREA)

        # loads
        model.LOADS = Param(model.time, model.demands,
                            initialize=data.loads)
        model.SOLAR_EM = Param(model.time, initialize=data.solar_data)

        model.NET_PRESENT_VALUE_TECH = Param(model.technologies,
                                             domain=NonNegativeReals,
                                             initialize=data.tech_npv)
        model.NET_PRESENT_VALUE_STORAGE = Param(model.storages,
                                                domain=NonNegativeReals,
                                                initialize=data.storage_npv)

    def solve(self, solver_settings: dict = None, is_verbose: bool = False):
        """
        Solve the model.

        Args:
            solver_settings: The config options for the solver
            is_verbose: Makes it so the solver prints everything

        Returns:
            The results
        """
        if not self._model:
            raise RuntimeError("Can't solve a model with no data.")

        if solver_settings is None:
            solver_settings = DEFAULT_SOLVER_SETTINGS

        solver = solver_settings["name"]
        options = solver_settings["options"]
        if options is None:
            options = {}

        opt = SolverFactory(solver)
        opt.options = options
        solver_manager = SolverManagerFactory("serial")

        results = solver_manager.solve(self._model, opt=opt, tee=is_verbose,
                                       timelimit=None)

        # in order to get the solutions found by the solver
        self._model.solutions.store_to(results)

        return response_format.create_response(results, self._model)
