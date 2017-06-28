"""
Provides a class for encapsulating an energy hub model.
"""
import functools

from pyomo.core.base import (
    ConcreteModel, RangeSet, Set, Param, NonNegativeReals, Binary, Var, Reals,
    Constraint, ConstraintList, Objective, minimize
)
from pyomo.opt import SolverFactory, SolverManagerFactory

# This import is used to find solvers.
# noinspection PyUnresolvedReferences
# pylint: disable=unused-import
import pyomo.environ

import excel_to_request_format
from data_formats import response_format
from energy_hub.input_data import InputData
from config import settings

BIG_M = 5000
TIME_HORIZON = 20
MAX_CARBON = 650000
MAX_SOLAR_AREA = 500


def constraint(*args):
    """
    Mark a function as a constraint of the model.

    The function that adds these constraints to the model is
    `_add_constraints_new`.

    Args:
        *args: The arguments that are passed to Pyomo's Constraint constructor

    Returns:
        The decorated function
    """
    def _wrapper(func):
        functools.wraps(func)

        func.is_constraint = True
        func.args = args

        return func

    return _wrapper


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
        self._model = None
        self._data = None

        if excel:
            request = excel_to_request_format.convert(excel)
            self._data = InputData(request)

        if request:
            self._data = InputData(request)

        if self._data:
            self._prepare()
        else:
            raise RuntimeError("Can't create a hub with no data.")

    def _prepare(self):
        self._model = ConcreteModel()

        self._create_sets()

        self._add_parameters()
        self._add_variables()
        self._add_constraints()
        self._add_objective()

    def _create_sets(self):
        data = self._data
        model = self._model

        num_time_steps, num_demands = data.demand_data.shape
        model.time = RangeSet(1, num_time_steps)
        model.sub_time = RangeSet(2, num_time_steps,
                                  within=model.time)

        model.technologies = RangeSet(1, len(data.converters))

        model.techs_without_grid = RangeSet(2, len(data.converters),
                                            within=model.technologies)

        model.energy_carrier = RangeSet(1, num_demands)

        model.techs = Set(initialize=data.max_capacity.keys(),
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

    @constraint()
    def calculate_total_cost(self, model):
        cost = (model.investment_cost
                + model.operating_cost
                + model.maintenance_cost)
        income = model.income_from_exports

        return model.total_cost == cost - income

    @constraint()
    def calculate_total_carbon(self, model):
        total_carbon = 0
        for tech in model.technologies:
            total_energy_imported = sum(model.energy_imported[t, tech]
                                        for t in model.time)

            total_carbon += (model.CARBON_FACTORS[tech]
                             * total_energy_imported)

        return model.total_carbon == total_carbon

    @constraint()
    def calculate_investment_cost(self, model):
        storage_cost = sum(model.NET_PRESENT_VALUE_STORAGE[out]
                           * model.LINEAR_STORAGE_COSTS[out]
                           * model.storage_capacity[out]
                           for out in model.energy_carrier)

        tech_cost = sum(model.NET_PRESENT_VALUE_TECH[tech]
                        * model.LINEAR_CAPITAL_COSTS[tech, out]
                        * model.capacities[tech, out]
                        # + (model.fixCapCosts[tech,out]
                        # * model.Ytechnologies[tech,out])
                        for tech in model.techs_without_grid
                        for out in model.energy_carrier)

        cost = tech_cost + storage_cost
        return model.investment_cost == cost

    @constraint()
    def calculate_income_from_exports(self, model):
        income = 0
        for energy in model.energy_carrier:
            total_energy_exported = sum(model.energy_exported[t, energy]
                                        for t in model.time)

            income += model.FEED_IN_TARIFFS[energy] * total_energy_exported

        return model.income_from_exports == income

    @constraint()
    def calculate_maintenance_cost(self, model):
        cost = 0
        for t in model.time:
            for tech in model.technologies:
                for energy in model.energy_carrier:
                    cost += (model.energy_imported[t, tech]
                             * model.CONVERSION_EFFICIENCY[tech, energy]
                             * model.OMV_COSTS[tech])

        return model.maintenance_cost == cost

    @constraint()
    def calculate_operating_cost(self, model):
        cost = 0
        for tech in model.technologies:
            total_energy_imported = sum(model.energy_imported[t, tech]
                                        for t in model.time)

            cost += model.OPERATING_PRICES[tech] * total_energy_imported

        return model.operating_cost == cost

    @constraint('time', 'energy_carrier')
    def storage_capacity(self, model, t, out):
        return model.storage_level[t, out] <= model.storage_capacity[out]

    @constraint('time', 'energy_carrier')
    def storage_min_state(self, model, t, out):
        rhs = model.storage_capacity[out] * model.MIN_STATE_OF_CHARGE[out]
        return model.storage_level[t, out] >= rhs

    @constraint('time', 'energy_carrier')
    def storage_discharge_rate(self, model, t, out):
        rhs = model.MAX_DISCHARGE_RATE[out] * model.storage_capacity[out]
        return model.energy_from_storage[t, out] <= rhs

    @constraint('time', 'energy_carrier')
    def storage_charge_rate(self, model, t, out):
        rhs = model.MAX_CHARGE_RATE[out] * model.storage_capacity[out]
        return model.energy_to_storage[t, out] <= rhs

    @constraint('sub_time', 'energy_carrier')
    def storage_balance(self, model, t, out):
        lhs = model.storage_level[t, out]

        storage_standing_loss = model.STORAGE_STANDING_LOSSES[out]
        discharge_rate = model.DISCHARGING_EFFICIENCY[out]
        charge_rate = model.CHARGING_EFFICIENCY[out]
        q_in = model.energy_to_storage[t, out]
        q_out = model.energy_from_storage[t, out]

        rhs = ((storage_standing_loss * model.storage_level[(t - 1), out])
               + (charge_rate * q_in)
               - ((1 / discharge_rate) * q_out))
        return lhs == rhs

    @constraint('technologies', 'energy_carrier')
    def fix_cost_constant(self, model, tech, out):
        capacity = model.capacities[tech, out]
        rhs = model.BIG_M * model.Ytechnologies[tech, out]
        return capacity <= rhs

    @constraint('roof_tech')
    def roof_area(self, model, roof):
        demands = range(1, self._data.demand_data.shape[1] + 1)

        # DemandData.shape[1]
        lhs = sum(model.capacities[roof, d] for d in demands)
        rhs = model.MAX_SOLAR_AREA
        return lhs <= rhs

    @constraint('time', 'solar_techs', 'energy_carrier')
    def solar_input(self, model, t, solar_tech, out):
        conversion_rate = model.CONVERSION_EFFICIENCY[solar_tech, out]

        if conversion_rate <= 0:
            return Constraint.Skip

        energy_imported = model.energy_imported[t, solar_tech]
        capacity = model.capacities[solar_tech, out]

        rhs = model.SOLAR_EM[t] * capacity

        return energy_imported == rhs

    @constraint('time', 'part_load', 'energy_carrier')
    def part_load_u(self, model, t, disp, out):
        conversion_rate = model.CONVERSION_EFFICIENCY[disp, out]

        if conversion_rate <= 0:
            return Constraint.Skip

        energy_imported = model.energy_imported[t, disp]

        lhs = energy_imported * conversion_rate
        rhs = model.BIG_M * model.Yon[t, disp]

        return lhs <= rhs

    @constraint('time', 'part_load', 'energy_carrier')
    def part_load_l(self, model, t, disp, out):
        conversion_rate = model.CONVERSION_EFFICIENCY[disp, out]

        if conversion_rate <= 0:
            return Constraint.Skip

        part_load = model.PART_LOAD[disp, out]
        capacity = model.capacities[disp, out]
        energy_imported = model.energy_imported[disp, out]

        lhs = part_load * capacity

        rhs = (energy_imported * conversion_rate
               + model.BIG_M * (1 - model.Yon[t, disp]))
        return lhs <= rhs

    @constraint('technologies', 'energy_carrier')
    def capacity(self, model, tech, out):
        if model.CONVERSION_EFFICIENCY[tech, out] <= 0:
            return model.capacities[tech, out] == 0

        return Constraint.Skip

    @constraint('disp_techs', 'energy_carrier')
    def max_capacity(self, model, tech, out):
        return model.capacities[tech, out] <= model.MAX_CAP_TECHS[tech]

    @constraint('time', 'energy_carrier')
    def loads_balance(self, model, t, out):
        q_out = model.energy_from_storage[t, out]
        q_in = model.energy_to_storage[t, out]
        load = model.LOADS[t, out]
        energy_exported = model.energy_exported[t, out]

        lhs = load + energy_exported

        energy_in = 0
        for tech in model.technologies:
            energy_imported = model.energy_imported[t, tech]
            conversion_rate = model.CONVERSION_EFFICIENCY[tech, out]

            energy_in += energy_imported * conversion_rate

        rhs = (q_out - q_in) + energy_in

        return lhs <= rhs

    @constraint('time', 'technologies', 'energy_carrier')
    def capacity_const(self, model, t, tech, output_type):
        conversion_rate = model.CONVERSION_EFFICIENCY[tech, output_type]

        if conversion_rate <= 0:
            return Constraint.Skip

        energy_imported = model.energy_imported[t, tech]
        capacity = model.capacities[tech, output_type]

        energy_in = energy_imported * conversion_rate

        return energy_in <= capacity

    def _add_constraints_new(self):
        methods = [getattr(self, method)
                   for method in dir(self)
                   if callable(getattr(self, method))]
        rules = (rule for rule in methods if hasattr(rule, 'is_constraint'))

        for rule in rules:
            name = rule.__name__ + '_constraint'
            args = [getattr(self._model, arg) for arg in rule.args]

            setattr(self._model, name, Constraint(*args, rule=rule))

    def _add_capacity_constraints(self):
        constraints = ConstraintList()
        for capacity in self._data.capacities:
            variable = getattr(self._model, capacity.name)

            lower_bound = capacity.lower_bound
            upper_bound = capacity.upper_bound

            constraints.add(lower_bound <= variable <= upper_bound)

        self._model.capacity_constraints = constraints

    def _add_constraints(self):
        self._add_constraints_new()
        self._add_capacity_constraints()

        self._add_various_constraints()

        self._add_unknown_storage_constraint()

    def _add_unknown_storage_constraint(self):
        data = self._data
        model = self._model

        model.StorCon = ConstraintList()
        for i in range(1, data.demand_data.shape[1] + 1):
            # 8760 I believe is the last entry in the table - 1
            last_entry = model.time.last()
            model.StorCon.add(model.storage_level[1, i]
                              == model.storage_level[last_entry, i])

    def _add_various_constraints(self):
        data = self._data
        model = self._model

        dispatch_demands = data.dispatch_demands
        model.con = ConstraintList()
        for i, chp in enumerate(data.chp_list):
            dd_1 = dispatch_demands[i, 1]
            dd_0 = dispatch_demands[i, 0]

            rhs = (model.CONVERSION_EFFICIENCY[chp, dd_1]
                   / model.CONVERSION_EFFICIENCY[chp, dd_0]
                   * model.capacities[chp, dd_0])
            constraint = model.capacities[chp, dd_1] == rhs
            model.con.add(constraint)

            constraint = (model.Ytechnologies[chp, dd_0]
                          == model.Ytechnologies[chp, dd_1])
            model.con.add(constraint)

            constraint = (model.capacities[chp, dd_0]
                          <= model.MAX_CAP_TECHS[chp]
                          * model.Ytechnologies[chp, dd_0])
            model.con.add(constraint)

    def _add_capacity_variables(self):
        for capacity in self._data.capacities:
            domain = capacity.domain
            name = capacity.name

            setattr(self._model, name, Var(domain=domain))

    def _add_variables(self):
        model = self._model

        self._add_capacity_variables()

        # Global variables
        model.energy_imported = Var(model.time, model.technologies,
                                    domain=NonNegativeReals)
        model.energy_exported = Var(model.time, model.energy_carrier,
                                    domain=NonNegativeReals)

        model.capacities = Var(model.technologies, model.energy_carrier,
                               domain=NonNegativeReals)

        model.Ytechnologies = Var(model.technologies, model.energy_carrier,
                                  domain=Binary)

        model.Yon = Var(model.time, model.technologies, domain=Binary)

        model.total_cost = Var(domain=Reals)
        model.operating_cost = Var(domain=NonNegativeReals)
        model.maintenance_cost = Var(domain=NonNegativeReals)
        model.income_from_exports = Var(domain=NonNegativeReals)
        model.investment_cost = Var(domain=NonNegativeReals)

        model.total_carbon = Var(domain=Reals)

        # Storage variables
        model.energy_to_storage = Var(model.time, model.energy_carrier,
                                      domain=NonNegativeReals)
        model.energy_from_storage = Var(model.time, model.energy_carrier,
                                        domain=NonNegativeReals)

        model.storage_level = Var(model.time, model.energy_carrier,
                                  domain=NonNegativeReals)

        model.storage_capacity = Var(model.energy_carrier,
                                     domain=NonNegativeReals)

    def _add_parameters(self):
        data = self._data
        model = self._model

        # coupling matrix & Technical parameters
        # coupling matrix technology efficiencies
        model.CONVERSION_EFFICIENCY = Param(model.technologies,
                                            model.energy_carrier,
                                            initialize=data.c_matrix)
        model.MAX_CAP_TECHS = Param(model.disp_techs,
                                    initialize=data.max_capacity)

        model.MAX_CHARGE_RATE = Param(model.energy_carrier,
                                      initialize=data.storage_charge)
        model.MAX_DISCHARGE_RATE = Param(model.energy_carrier,
                                         initialize=data.storage_discharge)
        model.STORAGE_STANDING_LOSSES = Param(model.energy_carrier,
                                              initialize=data.storage_loss)
        model.CHARGING_EFFICIENCY = Param(model.energy_carrier,
                                          initialize=data.storage_ef_ch)
        model.DISCHARGING_EFFICIENCY = Param(model.energy_carrier,
                                             initialize=data.storage_ef_disch)
        model.MIN_STATE_OF_CHARGE = Param(model.energy_carrier,
                                          initialize=data.storage_min_soc)
        # PartloadInput
        model.PART_LOAD = Param(model.technologies, model.energy_carrier,
                                initialize=data.part_load)

        # carbon factors
        model.CARBON_FACTORS = Param(model.technologies,
                                     initialize=data.carb_factors)
        model.MAX_CARBON = Param(initialize=MAX_CARBON)

        # Cost parameters
        # Technologies capital costs
        model.LINEAR_CAPITAL_COSTS = Param(model.technologies,
                                           model.energy_carrier,
                                           initialize=data.linear_cost)
        model.LINEAR_STORAGE_COSTS = Param(model.energy_carrier,
                                           initialize=data.storage_lin_cost)
        # Operating prices technologies
        model.OPERATING_PRICES = Param(model.technologies,
                                       initialize=data.fuel_price)
        model.FEED_IN_TARIFFS = Param(model.energy_carrier,
                                      initialize=data.feed_in)
        # Maintenance costs
        model.OMV_COSTS = Param(model.technologies,
                                initialize=data.var_maintenance_cost)

        # Declaring Global Parameters
        model.TIME_HORIZON = Param(within=NonNegativeReals,
                                   initialize=TIME_HORIZON)

        model.BIG_M = Param(within=NonNegativeReals, initialize=BIG_M)

        model.INTEREST_RATE = Param(within=NonNegativeReals,
                                    initialize=data.interest_rate)

        model.MAX_SOLAR_AREA = Param(initialize=MAX_SOLAR_AREA)

        # loads
        model.LOADS = Param(model.time, model.energy_carrier,
                            initialize=data.demands)
        model.SOLAR_EM = Param(model.time, initialize=data.solar_data)

        model.NET_PRESENT_VALUE_TECH = Param(model.technologies,
                                             domain=NonNegativeReals,
                                             initialize=data.tech_npv)
        model.NET_PRESENT_VALUE_STORAGE = Param(model.energy_carrier,
                                                domain=NonNegativeReals,
                                                initialize=data.storage_npv)

    def solve(self):
        """Solve the model.

        Returns:
            The results
        """
        if not self._model:
            raise RuntimeError("Can't solve a model with no data.")

        solver = settings["solver"]["name"]
        options = settings["solver"]["options"]
        if options is None:
            options = {}

        opt = SolverFactory(solver)
        opt.options = options
        solver_manager = SolverManagerFactory("serial")

        results = solver_manager.solve(self._model, opt=opt, tee=True,
                                       timelimit=None)

        # in order to get the solutions found by the solver
        self._model.solutions.store_to(results)

        return response_format.create_response(results, self._model)
