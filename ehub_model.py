from pyomo.core.base import (
    ConcreteModel, RangeSet, Set, Param, NonNegativeReals, Binary, Var, Reals,
    Constraint, ConstraintList, Objective, minimize
)
from pyomo.opt import SolverFactory, SolverManagerFactory
# noinspection PyUnresolvedReferences
import pyomo.environ  # used to find solvers

from InputData import InputData
from config import settings


class EHubModel:
    """
    Represents a black-box Energy Hub.
    """
    def __init__(self, excel=None):
        """
        Creates a new Energy Hub using some input data.

        Args:
            excel: The Excel 2003 file for input data.
        """
        self._model = None
        self._data = None

        if excel:
            self._data = InputData(excel)

        if self._data:
            self._prepare()
        else:
            raise RuntimeError("Can't create a hub with no data.")

    def _prepare(self):
        model = ConcreteModel()
        data = self._data

        # sets definition
        model.Time = RangeSet(1, data.DemandData.shape[0])
        model.SubTime = RangeSet(2, data.DemandData.shape[0],
                                 within=model.Time)
        model.In = RangeSet(1, data.Technologies.shape[1] + 1)
        model.W_Ogrid = Set(initialize=list(range(
                1 + 1, len(data.Technologies.columns) + 2)),
                within=model.In)  # techs w/o grid

        model.Out = RangeSet(1, data.DemandData.shape[1])
        number_of_demands = list(range(1, data.DemandData.shape[1] + 1))

        model.SolarTechs = Set(initialize=data.SolarSet(), within=model.In)

        model.DispTechs = Set(initialize=data.DispTechsSet(), within=model.In)
        model.Techs = Set(initialize=list(data.MaxCapacity().keys()),
                          within=model.In)
        model.PartLoad = Set(initialize=data.partloadtechs(), within=model.In)

        model.CHP = Set(initialize=data.CHP_list(),
                        within=model.In)  # set dispatch tech set
        # set tech with roof area set
        model.roof_tech = Set(initialize=data.Roof_tech(), within=model.In)
        model.gas_tech = Set(initialize=[3, 4, 7, 8], within=model.In)

        # coupling matrix & Technical parameters
        # coupling matrix technology efficiencies
        model.cMatrix = Param(model.In, model.Out, initialize=data.cMatrix())
        model.maxCapTechs = Param(model.DispTechs,
                                  initialize=data.MaxCapacity())
        model.maxCapTechsAll = Param(model.Techs,
                                     initialize=data.MaxCapacity())
        model.maxStorCh = Param(model.Out, initialize=data.StorageCh())
        model.maxStorDisch = Param(model.Out, initialize=data.StorageDisch())

        model.lossesStorStanding = Param(model.Out,
                                         initialize=data.StorageLoss())
        model.chargingEff = Param(model.Out, initialize=data.StorageEfCh())
        model.dischLosses = Param(model.Out, initialize=data.StorageEfDisch())
        model.minSoC = Param(model.Out, initialize=data.StorageMinSoC())
        model.partLoad = Param(model.In, model.Out,
                               initialize=data.PartLoad())  # PartloadInput
        model.maxSolarArea = Param(initialize=500)

        # carbon factors
        model.carbonFactors = Param(model.In, initialize=data.CarbFactors())
        model.maxCarbon = Param(initialize=650000)

        # Cost parameters
        # Technologies capital costs
        model.linCapCosts = Param(model.In, model.Out,
                                  initialize=data.LinearCost())
        model.linStorageCosts = Param(model.Out,
                                      initialize=data.StorageLinCost())
        # Operating prices technologies
        model.opPrices = Param(model.In, initialize=data.FuelPrice())
        model.feedInTariffs = Param(
                model.Out, initialize=data.FeedIn())  # feed-in tariffs
        # Maintenance costs
        model.omvCosts = Param(model.In, initialize=data.VarMaintCost())
        model.interestRate = Param(within=NonNegativeReals,
                                   initialize=data.InterestRate())
        # lifetime
        model.lifeTimeTechs = Param(model.In, initialize=data.LifeTime())
        model.lifeTimeStorages = Param(model.Out,
                                       initialize=data.StorageLife())

        # Declaring Global Parameters
        model.timeHorizon = Param(within=NonNegativeReals, initialize=20)
        model.bigM = Param(within=NonNegativeReals, initialize=5000)

        # loads

        model.loads = Param(model.Time, model.Out, initialize=data.Demands())
        model.solarEm = Param(model.Time, initialize=data.SolarData())

        # Global variables
        model.P = Var(model.Time, model.In, domain=NonNegativeReals)
        model.Pexport = Var(model.Time, model.Out, domain=NonNegativeReals)
        model.Capacities = Var(model.In, model.Out, domain=NonNegativeReals)
        model.Ytechnologies = Var(model.In, model.Out, domain=Binary)
        model.Yon = Var(model.Time, model.In, domain=Binary)
        model.TotalCost = Var(domain=Reals)
        model.OpCost = Var(domain=NonNegativeReals)
        model.MaintCost = Var(domain=NonNegativeReals)
        model.IncomeExp = Var(domain=NonNegativeReals)
        model.InvCost = Var(domain=NonNegativeReals)
        model.TotalCarbon = Var(domain=Reals)
        model.TotalCarbon2 = Var(domain=Reals)
        model.NetPresentValueTech = Param(
                model.In, domain=NonNegativeReals, initialize=data.NPV())
        model.NetPresentValueStor = Param(
                model.Out, domain=NonNegativeReals,
                initialize=data.StorageNPV())

        # Storage variables
        model.Qin = Var(model.Time, model.Out, domain=NonNegativeReals)
        model.Qout = Var(model.Time, model.Out, domain=NonNegativeReals)
        model.E = Var(model.Time, model.Out, domain=NonNegativeReals)
        model.StorageCap = Var(model.Out, domain=NonNegativeReals)
        model.Ystorage = Var(model.Out, domain=Binary)

        # --------------------------------------------------------------------------- #
        # Global constraints
        # --------------------------------------------------------------------------- #


        def loadsBalance_rule(model, t, out):
            return (model.loads[t, out] + model.Pexport[t, out] <= (
            model.Qout[t, out] - model.Qin[t, out] +
            sum(model.P[t, inp] * model.cMatrix[inp, out] for inp in
                model.In)))

        model.loadsBalance = Constraint(model.Time, model.Out,
                                        rule=loadsBalance_rule)

        def capacityConst_rule(model, t, inp, out):
            if model.cMatrix[inp, out] <= 0:
                return (Constraint.Skip)
            else:
                return (
                model.P[t, inp] * model.cMatrix[inp, out] <= model.Capacities[
                    inp, out])

        model.capacityConst = Constraint(
                model.Time, model.In, model.Out, rule=capacityConst_rule)

        def maxCapacity_rule2(model, tech, out):
            return (model.Capacities[tech, out] <= model.maxCapTechs[tech])

        model.maxCapacity2 = Constraint(
                model.DispTechs, model.Out, rule=maxCapacity_rule2)

        def capacity_rule(model, inp, out):
            if model.cMatrix[inp, out] <= 0:
                return (model.Capacities[inp, out] == 0)
            else:
                return (Constraint.Skip)

        model.capacity_feasibility = Constraint(
                model.In, model.Out, rule=capacity_rule)

        # --------------------------------------------------------------------------- #
        # Specific constraints
        # --------------------------------------------------------------------------- #


        def partLoadL_rule(model, t, disp, out):
            if model.cMatrix[disp, out] <= 0:
                return (Constraint.Skip)
            else:
                return (
                model.partLoad[disp, out] * model.Capacities[disp, out] <=
                (model.P[disp, out] * model.cMatrix[disp, out]
                 + model.bigM * (1 - model.Yon[t, disp])))

        model.partLoadL = Constraint(
                model.Time, model.PartLoad, model.Out, rule=partLoadL_rule)

        def partLoadU_rule(model, t, disp, out):
            if model.cMatrix[disp, out] <= 0:
                return (Constraint.Skip)
            else:
                return (
                model.P[t, disp] * model.cMatrix[disp, out] <= model.bigM *
                model.Yon[t, disp])

        model.partLoadU = Constraint(
                model.Time, model.PartLoad, model.Out, rule=partLoadU_rule)

        def solarInput_rule(model, t, sol, out):
            if model.cMatrix[sol, out] <= 0:
                return (Constraint.Skip)
            else:
                return (model.P[t, sol] == model.solarEm[t] * model.Capacities[
                    sol, out])

        model.solarInput = Constraint(
                model.Time, model.SolarTechs, model.Out, rule=solarInput_rule)

        def roofArea_rule(model, roof, demand):
            # DemandData.shape[1]
            return (sum(model.Capacities[roof, d] for d in
                        number_of_demands) <= model.maxSolarArea)

        model.roofArea = Constraint(
                model.roof_tech, model.Out,
                rule=roofArea_rule)  # model.roof_tech

        def fixCostConst_rule(model, inp, out):
            return (
            model.Capacities[inp, out] <= model.bigM * model.Ytechnologies[
                inp, out])

        model.fixCostConst = Constraint(model.In, model.Out,
                                        rule=fixCostConst_rule)

        dispatch_demands = data.DisDemands()
        CHP_list = data.CHP_list()
        model.con = ConstraintList()
        for x in range(1, len(dispatch_demands) + 1):
            model.con.add(model.Capacities[
                              CHP_list[x - 1], dispatch_demands[x - 1, 1]] ==
                          model.cMatrix[
                              CHP_list[x - 1], dispatch_demands[x - 1, 1]
                          ] / model.cMatrix[
                              CHP_list[x - 1], dispatch_demands[x - 1, 0]] *
                          model.Capacities[
                              CHP_list[x - 1], dispatch_demands[x - 1, 0]])
            model.con.add(model.Ytechnologies[
                              CHP_list[x - 1], dispatch_demands[x - 1, 0]]
                          == model.Ytechnologies[
                              CHP_list[x - 1], dispatch_demands[x - 1, 1]])
            model.con.add(model.Capacities[
                              CHP_list[x - 1], dispatch_demands[x - 1, 0]] <=
                          model.maxCapTechs[CHP_list[x - 1]] *
                          model.Ytechnologies[
                              CHP_list[x - 1], dispatch_demands[x - 1, 0]])

        # --------------------------------------------------------------------------- #
        # Storage constraints
        # --------------------------------------------------------------------------- #

        def storageBalance_rule(model, t, out):
            return (model.E[t, out] == (
            model.lossesStorStanding[out] * model.E[(t - 1), out]
            + model.chargingEff[out] * model.Qin[t, out]
            - (1 / model.dischLosses[out]) * model.Qout[t, out]))

        model.storageBalance = Constraint(
                model.SubTime, model.Out, rule=storageBalance_rule)

        model.StorCon = ConstraintList()
        for x in range(1, data.DemandData.shape[1] + 1):
            # 8760 I believe is the last entry in the table - 1
            model.StorCon.add(model.E[1, x] == model.E[24, x])

        def storageChargeRate_rule(model, t, out):
            return (
            model.Qin[t, out] <= model.maxStorCh[out] * model.StorageCap[out])

        model.storageChargeRate = Constraint(
                model.Time, model.Out, rule=storageChargeRate_rule)

        def storageDischRate_rule(model, t, out):
            return (
            model.Qout[t, out] <= model.maxStorDisch[out] * model.StorageCap[
                out])

        model.storageDischRate = Constraint(
                model.Time, model.Out, rule=storageDischRate_rule)

        def storageMinState_rule(model, t, out):
            return (
            model.E[t, out] >= model.StorageCap[out] * model.minSoC[out])

        model.storageMinState = Constraint(
                model.Time, model.Out, rule=storageMinState_rule)

        def storageCap_rule(model, t, out):
            return (model.E[t, out] <= model.StorageCap[out])

        model.storageCap = Constraint(model.Time, model.Out,
                                      rule=storageCap_rule)

        # --------------------------------------------------------------------------- #
        # Objective functions
        # --------------------------------------------------------------------------- #
        def objective_rule(model):
            return (model.TotalCost)

        model.Total_Cost = Objective(rule=objective_rule, sense=minimize)

        def opCost_rule(model):
            return (model.OpCost == ((sum(model.opPrices[inp]
                                          * sum(
                    model.P[t, inp] for t in model.Time)
                                          for inp in model.In)))
                    )

        model.opCost = Constraint(rule=opCost_rule)

        def maintenanceCost_rule(model):
            return (model.MaintCost == (sum(model.P[t, inp] *
                                            model.cMatrix[inp, out] *
                                            model.omvCosts[inp]
                                            for t in model.Time for inp in
                                            model.In for out in model.Out)
                                        ))

        model.maintCost = Constraint(rule=maintenanceCost_rule)

        def incomeExp_rule(model):
            return (model.IncomeExp == (sum(model.feedInTariffs[out] *
                                            sum(model.Pexport[t, out]
                                                for t in model.Time)
                                            for out in model.Out))
                    )

        model.incomeExp = Constraint(rule=incomeExp_rule)

        def invCost_rule(model):
            return (model.InvCost == (sum(model.NetPresentValueTech[inp] * (
            model.linCapCosts[inp, out] * model.Capacities[inp, out]) for inp
                                          in model.W_Ogrid for out in
                                          model.Out)  # + model.fixCapCosts[inp,out] * model.Ytechnologies[inp,out]
                                      + sum(
                    model.NetPresentValueStor[out] * model.linStorageCosts[
                        out] * model.StorageCap[out] for out in model.Out))
                    )

        model.invCost = Constraint(rule=invCost_rule)

        def totalCost_rule(model):
            return (
            model.TotalCost == model.InvCost + model.OpCost + model.MaintCost - model.IncomeExp)

        model.totalCost = Constraint(rule=totalCost_rule)

        def totalCarbon2_rule(model):
            return (model.TotalCarbon2 == model.TotalCarbon)

        model.totalCarbon2 = Constraint(rule=totalCarbon2_rule)

        def totalCarbon_rule(model):
            return (model.TotalCarbon == sum(model.carbonFactors[inp] * sum(
                    model.P[t, inp] for t in model.Time) for inp in model.In))

        model.totalCarbon = Constraint(rule=totalCarbon_rule)

        self._model = model

    def solve(self):
        """
        Solves the model.

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

        return results
