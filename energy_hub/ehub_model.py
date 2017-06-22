"""
Provides a class for encapsulating an energy hub model.
"""

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

GAS_TECH = [3, 4, 7, 8]
BIG_M = 5000
TIME_HORIZON = 20
MAX_CARBON = 650000
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

        techs_without_grid = range(1 + 1, len(data.converters) + 1)
        model.techs_without_grid = Set(initialize=techs_without_grid,
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
        #model.gas_tech = Set(initialize=GAS_TECH, within=model.technologies)

        model.part_load = Set(initialize=data.part_load_techs,
                              within=model.technologies)

        # set dispatch tech set
        model.CHP = Set(initialize=data.chp_list, within=model.technologies)

    def _add_objective(self):
        def _rule(model):
            return model.total_cost

        self._model.total_cost_objective = Objective(rule=_rule, sense=minimize)

    def _add_constraints(self):
        # Global constraints
        self._add_loads_balance_constraint()
        self._add_capacity_const_constraint()
        self._add_max_capacity_constraint()
        self._add_capacity_constraint()

        # Specific constraints
        self._add_part_load_l_constraint()
        self._add_part_load_u_constraint()
        self._add_solar_input_constraint()
        self._add_roof_area_constraint()
        self._add_fix_cost_const_constraint()

        self._add_various_constraints()

        self._add_storage_balance_constraint()
        self._add_unknown_storage_constraint()
        self._add_storage_charge_rate_constraint()
        self._add_storage_discharge_rate_constraint()
        self._add_storage_min_state_constraint()
        self._add_storage_cap_constraint()

        self._add_operating_cost_constraint()
        self._add_maintenance_cost_constraint()
        self._add_income_from_exports_constraint()
        self._add_investment_cost_constraint()
        self._add_total_cost_constraint()
        self._add_total_carbon_constraint()

    def _add_unknown_storage_constraint(self):
        data = self._data
        model = self._model

        model.StorCon = ConstraintList()
        for i in range(1, data.demand_data.shape[1] + 1):
            # 8760 I believe is the last entry in the table - 1
            last_entry = model.time.last()
            model.StorCon.add(model.E[1, i] == model.E[last_entry, i])

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

    def _add_total_carbon_constraint(self):
        def _rule(model):
            total_carbon = 0
            for tech in model.technologies:
                total_energy_imported = sum(model.energy_imported[t, tech]
                                            for t in model.time)

                total_carbon += (model.CARBON_FACTORS[tech]
                                 * total_energy_imported)

            return model.total_carbon == total_carbon

        self._model.total_carbon_constraint = Constraint(rule=_rule)

    def _add_total_cost_constraint(self):
        def _rule(model):
            cost = (model.investment_cost
                    + model.operating_cost
                    + model.maintenance_cost)
            income = model.income_from_exports

            return model.total_cost == cost - income

        self._model.total_cost_constraint = Constraint(rule=_rule)

    def _add_investment_cost_constraint(self):
        def _rule(model):
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

        self._model.investment_cost_constraint = Constraint(rule=_rule)

    def _add_income_from_exports_constraint(self):
        def _rule(model):
            income = 0
            for energy in model.energy_carrier:
                total_energy_exported = sum(model.energy_exported[t, energy]
                                            for t in model.time)

                income += model.FEED_IN_TARIFFS[energy] * total_energy_exported

            return model.income_from_exports == income

        self._model.income_from_exports_constraint = Constraint(rule=_rule)

    def _add_maintenance_cost_constraint(self):
        def _rule(model):
            cost = 0
            for t in model.time:
                for tech in model.technologies:
                    for energy in model.energy_carrier:
                        cost += (model.energy_imported[t, tech]
                                 * model.CONVERSION_EFFICIENCY[tech, energy]
                                 * model.OMV_COSTS[tech])

            return model.maintenance_cost == cost

        self._model.maintenance_cost_constraint = Constraint(rule=_rule)

    def _add_operating_cost_constraint(self):
        def _rule(model):
            cost = 0
            for tech in model.technologies:
                total_energy_imported = sum(model.energy_imported[t, tech]
                                            for t in model.time)

                cost += model.OPERATING_PRICES[tech] * total_energy_imported

            return model.operating_cost == cost

        self._model.operating_cost_constraint = Constraint(rule=_rule)

    def _add_storage_cap_constraint(self):
        def _rule(model, t, out):
            return model.E[t, out] <= model.storage_capacity[out]

        self._model.storage_capacity_constraint = Constraint(
            self._model.time, self._model.energy_carrier, rule=_rule)

    def _add_storage_min_state_constraint(self):
        def _rule(model, t, out):
            rhs = model.storage_capacity[out] * model.MIN_STATE_OF_CHARGE[out]
            return model.E[t, out] >= rhs

        self._model.storage_min_state_constraint = Constraint(
            self._model.time, self._model.energy_carrier, rule=_rule)

    def _add_storage_discharge_rate_constraint(self):
        def _rule(model, t, out):
            rhs = model.MAX_DISCHARGE_RATE[out] * model.storage_capacity[out]
            return model.energy_from_storage[t, out] <= rhs

        self._model.storage_discharge_rate_constraint = Constraint(
            self._model.time, self._model.energy_carrier, rule=_rule)

    def _add_storage_charge_rate_constraint(self):
        def _rule(model, t, out):
            rhs = model.MAX_CHARGE_RATE[out] * model.storage_capacity[out]
            return model.energy_to_storage[t, out] <= rhs

        self._model.storage_charge_rate_constraint = Constraint(
            self._model.time, self._model.energy_carrier, rule=_rule)

    def _add_storage_balance_constraint(self):
        def _rule(model, t, out):
            lhs = model.E[t, out]

            storage_standing_loss = model.STORAGE_STANDING_LOSSES[out]
            discharge_rate = model.DISCHARGING_EFFICIENCY[out]
            charge_rate = model.CHARGING_EFFICIENCY[out]
            q_in = model.energy_to_storage[t, out]
            q_out = model.energy_from_storage[t, out]

            rhs = ((storage_standing_loss * model.E[(t - 1), out])
                   + (charge_rate * q_in)
                   - ((1 / discharge_rate) * q_out))
            return lhs == rhs

        self._model.storage_balance_constraint = Constraint(
            self._model.sub_time, self._model.energy_carrier, rule=_rule)

    def _add_fix_cost_const_constraint(self):
        def _rule(model, tech, out):
            capacity = model.capacities[tech, out]
            rhs = model.BIG_M * model.Ytechnologies[tech, out]
            return capacity <= rhs

        self._model.fix_cost_const_constraint = Constraint(
            self._model.technologies, self._model.energy_carrier, rule=_rule)

    def _add_roof_area_constraint(self):
        demands = range(1, self._data.demand_data.shape[1] + 1)

        def _rule(model, roof):
            # DemandData.shape[1]
            lhs = sum(model.capacities[roof, d] for d in demands)
            rhs = model.MAX_SOLAR_AREA
            return lhs <= rhs

        self._model.roof_area_constraint = Constraint(self._model.roof_tech,
                                                      rule=_rule)

    def _add_solar_input_constraint(self):
        def _rule(model, t, solar_tech, out):
            conversion_rate = model.CONVERSION_EFFICIENCY[solar_tech, out]

            if conversion_rate <= 0:
                return Constraint.Skip

            energy_imported = model.energy_imported[t, solar_tech]
            capacity = model.capacities[solar_tech, out]

            rhs = model.SOLAR_EM[t] * capacity

            return energy_imported == rhs

        self._model.solar_input_constraint = Constraint(
            self._model.time, self._model.solar_techs,
            self._model.energy_carrier, rule=_rule)

    def _add_part_load_u_constraint(self):
        def _rule(model, t, disp, out):
            conversion_rate = model.CONVERSION_EFFICIENCY[disp, out]

            if conversion_rate <= 0:
                return Constraint.Skip

            energy_imported = model.energy_imported[t, disp]

            lhs = energy_imported * conversion_rate
            rhs = model.BIG_M * model.Yon[t, disp]

            return lhs <= rhs

        self._model.part_load_u_constraint = Constraint(
            self._model.time, self._model.part_load,
            self._model.energy_carrier, rule=_rule)

    def _add_part_load_l_constraint(self):
        def _rule(model, t, disp, out):
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

        self._model.part_load_l_constraint = Constraint(
            self._model.time, self._model.part_load,
            self._model.energy_carrier, rule=_rule)

    def _add_capacity_constraint(self):
        def _rule(model, tech, out):
            if model.CONVERSION_EFFICIENCY[tech, out] <= 0:
                return model.capacities[tech, out] == 0

            return Constraint.Skip

        self._model.capacity_feasibility = Constraint(
            self._model.technologies, self._model.energy_carrier, rule=_rule)

    def _add_max_capacity_constraint(self):
        def _rule(model, tech, out):
            return model.capacities[tech, out] <= model.MAX_CAP_TECHS[tech]

        self._model.max_capacity_constraint = Constraint(
            self._model.disp_techs, self._model.energy_carrier, rule=_rule)

    def _add_loads_balance_constraint(self):
        def _rule(model, t, out):
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

        self._model.loads_balance_constraint = Constraint(
            self._model.time, self._model.energy_carrier, rule=_rule)

    def _add_capacity_const_constraint(self):
        def _rule(model, t, tech, output_type):
            conversion_rate = model.CONVERSION_EFFICIENCY[tech, output_type]


            if conversion_rate <= 0:
                return Constraint.Skip

            energy_imported = model.energy_imported[t, tech]
            capacity = model.capacities[tech, output_type]

            energy_in = energy_imported * conversion_rate

            return energy_in <= capacity

        self._model.capacity_const_constraint = Constraint(
            self._model.time, self._model.technologies,
            self._model.energy_carrier, rule=_rule)

    def _add_variables(self):
        model = self._model

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

        model.E = Var(model.time, model.energy_carrier,
                      domain=NonNegativeReals)

        model.storage_capacity = Var(model.energy_carrier,
                                     domain=NonNegativeReals)

        model.Ystorage = Var(model.energy_carrier, domain=Binary)

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
        model.MAX_CAP_TECHS_ALL = Param(model.techs,
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

        model.TECH_LIFETIMES = Param(model.technologies,
                                     initialize=data.life_time)
        model.STORAGE_LIFETIMES = Param(model.energy_carrier,
                                        initialize=data.storage_life)

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
