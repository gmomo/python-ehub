import pandas as pd
import numpy as np
from itertools import compress


class InputData:

    def __init__(self, excel_path, demands='Demand data', solar='Solar data',
                 tech='Technology', gen='General'):
        self.path = excel_path
        self.DemandSheet = demands
        self.SolarSheet = solar
        self.TechSheet = tech
        self.GeneralSheet = gen

        self.TechOutputs = None
        self.Technologies = None
        self.DemandData = None
        self.StorageData = None

        self.Initialize()

    def Initialize(self):
        self.TechParameters()
        self.TechOutput()
        self.Demanddata()
        self.Storage()

    def TechParameters(self):
        Technologies = pd.read_excel(self.path, sheetname=self.TechSheet,
                                     skiprows=1, index_col=0, skip_footer=38)  # technology characteristics
        Technologies = Technologies.dropna(
            axis=1, how='all')  # technology characteristics
        Technologies = Technologies.fillna(0)  # technology characteristics
        self.Technologies = Technologies

    def TechOutput(self):
        TechOutputs = pd.read_excel(self.path, sheetname=self.TechSheet,
                                    skiprows=15, index_col=0, skip_footer=26)  # Output matrix
        TechOutputs = TechOutputs.dropna(axis=0, how='all')  # Output matrix
        TechOutputs = TechOutputs.dropna(axis=1, how='all')  # Output matrix
        self.TechOutputs = TechOutputs

    def Demanddata(self):
        DemandDatas = pd.read_excel(self.path, sheetname=self.DemandSheet)
        self.DemandData = DemandDatas

    def Storage(self):
        Storage = pd.read_excel(
            self.path, sheetname=self.TechSheet, skiprows=40, index_col=0, skip_footer=0)
        Storage = Storage.dropna(axis=1, how='all')
        Storage = Storage.fillna(0)
        self.StorageData = Storage

    #----------------------------------------------------------------------

    def Dict1D(self, dictVar, dataframe):
        for i, vali in enumerate(dataframe.index):
            dictVar[i + 1] = round(dataframe.iloc[i][1], 4)
        return dictVar

    def Dict1D_val_index(self, dictVar, dataframe):
        for i, vali in enumerate(dataframe.index):
            dictVar[vali] = round(dataframe.iloc[i][1], 4)
        return dictVar

    def DictND(self, dictVar, dataframe):
        for i, vali in enumerate(dataframe.index):
            for j, valj in enumerate(dataframe.columns):
                dictVar[vali, valj] = round(dataframe.iloc[i][j + 1], 4)
        return dictVar

    #----------------------------------------------------------------------

    def Demands(self):
        Loads_init = self.DemandData
        Loads_init.index = list(range(1, len(Loads_init.index) + 1))
        Loads_init.columns = list(range(1, len(Loads_init.columns) + 1))
        loads_init = {}
        loads_init = self.DictND(loads_init, Loads_init)
        return loads_init

    #----------------------------------------------------------------------

    def SolarData(self):
        SolarData = pd.read_excel(self.path, sheetname=self.SolarSheet)
        SolarData.columns = [1]
        solar_init = {}
        solar_init = self.Dict1D(solar_init, SolarData)
        return solar_init

    #----------------------------------------------------------------------

    def CHP_list(self):
        # find dispatch tech (CHP)
        Dispatch_tech = pd.DataFrame(self.TechOutputs.sum(0))
        CHP_setlist = []
        for n, val in enumerate(Dispatch_tech[0]):
            if val > 1:
                # first is electricity +1 since it starts at 0
                CHP_setlist.append(n + 2)
        return CHP_setlist

    #----------------------------------------------------------------------

    def Roof_tech(self):
        Roof_techset = []
        for n, val in enumerate(self.Technologies.loc["Area (m2)"]):
            if val > 0:
                # first is electricity +1 since it starts at 0
                Roof_techset.append(n + 2)

        return Roof_techset

    #----------------------------------------------------------------------

    def cMatrix(self):

        # Based on the + - values, prepare data for generating coupling matrix
        TechOutputs2 = self.TechOutputs.multiply(
            np.array(self.Technologies.loc['Efficiency (%)']))
        TechOutputs2.loc[TechOutputs2.index != 'Electricity'] = TechOutputs2.loc[TechOutputs2.index != 'Electricity'].multiply(
            np.array(self.Technologies.loc['Output ratio'].fillna(value=1).replace(0, 1)))
        TechOutputs2[TechOutputs2 < 0] = -1

        addGrid = np.zeros(len(self.DemandData.columns),)
        addGrid[0] = 1  # add electricity to coupling matrix
        Grid = pd.DataFrame(
            addGrid, columns=["Grid"], index=self.DemandData.columns).transpose()

        Cmatrix = TechOutputs2.transpose()
        Cmatrix = pd.concat([Grid, Cmatrix])
        Cmatrix.index = list(range(1, len(TechOutputs2.columns) + 2))
        Cmatrix.columns = list(range(1, len(TechOutputs2.index) + 1))
        cMatrixDict = {}
        cMatrixDict = self.DictND(cMatrixDict, Cmatrix)

        return cMatrixDict

    #----------------------------------------------------------------------

    def PartLoad(self):
        PartLoad = self.Technologies.loc["MinLoad (%)", ] / 100

        partload = self.TechOutputs.iloc[0:1].mul(list(PartLoad), axis=1)
        partload = pd.concat(
            [partload, self.TechOutputs.iloc[1:].mul(list(PartLoad), axis=1)], axis=0)
        partload = partload.abs()
        partload = partload.transpose()
        partload.index = list(range(1 + 1, len(self.TechOutputs.columns) + 2))
        partload.columns = list(range(1, len(self.TechOutputs.index) + 1))
        SolartechsSets = list(compress(list(range(
            1 + 1, len(self.Technologies.columns) + 2)), list(self.Technologies.loc["Area (m2)"] > 0)))

        for i in SolartechsSets:
            partload.drop(i, inplace=True)

        PartloadInput = {}
        PartloadInput = self.DictND(PartloadInput, partload)

        return PartloadInput

    #----------------------------------------------------------------------

    def MaxCapacity(self):
        MaxCap = self.Technologies.loc["Maximum Capacity", ]
        MaxCap.index = list(
            range(2, len(self.Technologies.loc["MinLoad (%)", ].index) + 2))
        MaxCap.round(decimals=3)
        maxCap = MaxCap.to_dict()

        SolartechsSets = list(compress(list(range(
            1 + 1, len(self.Technologies.columns) + 2)), list(self.Technologies.loc["Area (m2)"] > 0)))
        for i in SolartechsSets:
            maxCap.pop(i, None)

        return maxCap

    #----------------------------------------------------------------------

    def SolarSet(self):
        return list(compress(list(range(1 + 1, len(self.Technologies.columns) + 2)), list(self.Technologies.loc["Area (m2)"] > 0)))

    def DispTechsSet(self):
        return list(compress(list(range(1 + 1, len(self.Technologies.columns) + 2)), list(self.Technologies.loc["Area (m2)"] == 0)))

    def partloadtechs(self):
        PartLoad = self.Technologies.loc["MinLoad (%)", ] / 100

        partload = self.TechOutputs.iloc[0:1].mul(list(PartLoad), axis=1)
        partload = pd.concat(
            [partload, self.TechOutputs.iloc[1:].mul(list(PartLoad), axis=1)], axis=0)
        partload = partload.abs()
        partload = partload.transpose()
        partload.index = list(range(1 + 1, len(self.TechOutputs.columns) + 2))
        partload.columns = list(range(1, len(self.TechOutputs.index) + 1))
        SolartechsSets = list(compress(list(range(
            1 + 1, len(self.Technologies.columns) + 2)), list(self.Technologies.loc["Area (m2)"] > 0)))

        for i in SolartechsSets:
            partload.drop(i, inplace=True)

        return list(partload.loc[partload.sum(axis=1) > 0].index)

    #----------------------------------------------------------------------

    def LinearCost(self):
        LinearCost = self.Technologies.loc["CapCost (chf/kW)", ]

        linCost = self.TechOutputs.iloc[0:1].mul(list(LinearCost), axis=1)
        linCost = pd.concat(
            [linCost, self.TechOutputs.iloc[1:].mul(list(LinearCost), axis=1)], axis=0)

        linCost = linCost.transpose()
        for name in linCost.columns[1:]:
            linCost.loc[linCost["Electricity"] > 1, name] = 0

        linCost.loc[linCost["Electricity"] < 0, "Electricity"] = 0
        linCost = linCost.abs()

        addGrid = np.zeros(len(self.DemandData.columns),)
        addGrid[0] = 1  # add electricity to coupling matrix
        Grid = pd.DataFrame(
            addGrid, columns=["Grid"], index=self.DemandData.columns).transpose()

        linCost = pd.concat([Grid, linCost])

        linCost.index = list(range(1, len(self.TechOutputs.columns) + 2))
        linCost.columns = list(range(1, len(self.TechOutputs.index) + 1))
        linCost.loc[1] = 0

        linCapCosts = {}
        linCapCosts = self.DictND(linCapCosts, linCost)

        return linCapCosts

    #----------------------------------------------------------------------
    ### Find which is the primary input for capacity #####
    def DisDemands(self):

        CHPlist = self.CHP_list()
        dispatch_demands = np.zeros((len(CHPlist), 2), dtype=int)

        for n, val in enumerate(CHPlist):
            counter = 0
            #import pdb; pdb.set_trace()
            for i, value in enumerate(np.array(self.TechOutputs.iloc[:, val - 2], dtype=int)):
                if value > 0 and counter == 0:
                    dispatch_demands[n, 0] = i + 1
                    counter = 1
                if value > 0 and counter == 1:
                    dispatch_demands[n, 1] = i + 1

        return dispatch_demands

    #----------------------------------------------------------------------

    def InterestRate(self):
        Interest_rate = pd.read_excel(
            self.path, sheetname=self.GeneralSheet, skiprows=8, index_col=0, skip_footer=7)
        Interest_rate = Interest_rate.dropna(axis=1, how='all')
        Interest_rate_R = Interest_rate.loc["Interest Rate r"][0]
        return Interest_rate_R

    #----------------------------------------------------------------------

    def LifeTime(self):
        Life = pd.DataFrame(list(self.Technologies.loc["Lifetime (yr)"]))
        Life.columns = [1]
        Life.index = list(range(2, len(self.TechOutputs.columns) + 2))
        lifeTimeTechs = {}
        lifeTimeTechs = self.Dict1D_val_index(lifeTimeTechs, Life)
        return lifeTimeTechs

    #----------------------------------------------------------------------

    def NPV(self):
        Interest_rate_R = self.InterestRate()
        Life = pd.DataFrame(list(self.Technologies.loc["Lifetime (yr)"]))
        Life.columns = [1]
        Life.index = list(range(2, len(self.TechOutputs.columns) + 2))

        NetPresentValue = 1 / (((1 + Interest_rate_R) ** Life - 1) /
                               (Interest_rate_R * ((1 + Interest_rate_R) ** Life)))
        NetPresentValueTech = {}
        NetPresentValueTech = self.Dict1D_val_index(
            NetPresentValueTech, NetPresentValue)
        return NetPresentValueTech

    #----------------------------------------------------------------------

    def VarMaintCost(self):
        VarOMF = pd.DataFrame(list(self.Technologies.loc["OMVCost (chf/kWh)"]))
        VarOMF.columns = [1]
        VarOMF.index = list(range(1 + 1, len(self.TechOutputs.columns) + 2))
        VarOMF.loc[1] = 0
        omvCosts = {}
        omvCosts = self.Dict1D_val_index(omvCosts, VarOMF)
        return omvCosts

    #----------------------------------------------------------------------

    def CarbFactors(self):
        Carbon = pd.read_excel(
            self.path, sheetname=self.TechSheet, skiprows=24, index_col=0, skip_footer=16)
        Carbon = Carbon.dropna(axis=0, how='all')
        Carbon = Carbon.dropna(axis=1, how='all')
        Carbon.index = [1]

        ElectricityCF = pd.read_excel(
            self.path, sheetname=self.GeneralSheet, skiprows=1, index_col=0, skip_footer=14)
        ElectricityCF = ElectricityCF.dropna(axis=0, how='all')
        ElectricityCF = ElectricityCF.dropna(axis=1, how='all')
        del ElectricityCF["Price (chf/kWh)"]
        ElectricityCF.index = [1]

        CarbonFactors = pd.concat([ElectricityCF, Carbon], axis=1)
        CarbonFactors.columns = list(range(1, len(CarbonFactors.columns) + 1))
        CarbonFactors = CarbonFactors.transpose()

        carbonFactors = {}
        carbonFactors = self.Dict1D(carbonFactors, CarbonFactors)

        return carbonFactors

    #----------------------------------------------------------------------

    def FuelPrice(self):
        Fuel = pd.read_excel(self.path, sheetname=self.GeneralSheet,
                             skiprows=1, index_col=0, skip_footer=10)
        Fuel = Fuel.dropna(axis=0, how='all')

        Carbon = pd.read_excel(
            self.path, sheetname=self.TechSheet, skiprows=24, index_col=0, skip_footer=16)
        Carbon = Carbon.dropna(axis=0, how='all')
        Carbon = Carbon.dropna(axis=1, how='all')
        Carbon.index = [1]

        ElectricityCF = pd.read_excel(
            self.path, sheetname=self.GeneralSheet, skiprows=1, index_col=0, skip_footer=14)
        ElectricityCF = ElectricityCF.dropna(axis=0, how='all')
        ElectricityCF = ElectricityCF.dropna(axis=1, how='all')
        del ElectricityCF["Price (chf/kWh)"]
        ElectricityCF.index = [1]

        CarbonFactors = pd.concat([ElectricityCF, Carbon], axis=1)
        CarbonFactors.columns = list(range(1, len(CarbonFactors.columns) + 1))
        CarbonFactors = CarbonFactors.transpose()

        for n, val in enumerate(Fuel["CO2 (kg/kWh)"]):
            for index, value in CarbonFactors.iterrows():
                if float(val) == float(value):
                    CarbonFactors.loc[index] = float(
                        Fuel["Price (chf/kWh)"][n])

        opPrices = {}
        opPrices = self.Dict1D(opPrices, CarbonFactors)

        return opPrices

    #----------------------------------------------------------------------

    def FeedIn(self):
        Tariff = pd.read_excel(
            self.path, sheetname=self.GeneralSheet, skiprows=11, index_col=0, skip_footer=0)
        Tariff = Tariff.dropna(axis=0, how='all')
        Tariff = Tariff.dropna(axis=1, how='all')
        Tariff.columns = [1]
        Tariff.index = list(range(1, len(self.DemandData.columns) + 1))

        feedInTariffs = {}
        feedInTariffs = self.Dict1D_val_index(feedInTariffs, Tariff)
        return feedInTariffs

    #### Storage ####
    #----------------------------------------------------------------------

    def StorageCh(self):
        maxStorCh = {}
        MaxCharge = pd.DataFrame(list(self.StorageData.loc["max_charge"]))
        MaxCharge.columns = [1]
        maxStorCh = self.Dict1D(maxStorCh, MaxCharge)
        return maxStorCh

    def StorageDisch(self):
        maxStorDisch = {}
        MaxDischarge = pd.DataFrame(
            list(self.StorageData.loc["max_discharge"]))
        MaxDischarge.columns = [1]
        maxStorDisch = self.Dict1D(maxStorDisch, MaxDischarge)
        return maxStorDisch

    def StorageLoss(self):
        lossesStorStanding = {}
        losses = pd.DataFrame(list(self.StorageData.loc["decay"]))
        losses.columns = [1]
        lossesStorStanding = self.Dict1D(lossesStorStanding, losses)
        return lossesStorStanding

    def StorageEfCh(self):
        chargingEff = {}
        Ch_eff = pd.DataFrame(list(self.StorageData.loc["ch_eff"]))
        Ch_eff.columns = [1]
        chargingEff = self.Dict1D(chargingEff, Ch_eff)
        return chargingEff

    def StorageEfDisch(self):
        dischLosses = {}
        Disch_eff = pd.DataFrame(list(self.StorageData.loc["disch_eff"]))
        Disch_eff.columns = [1]
        dischLosses = self.Dict1D(dischLosses, Disch_eff)
        return dischLosses

    def StorageMinSoC(self):
        minSoC = {}
        min_state = pd.DataFrame(list(self.StorageData.loc["min_state"]))
        min_state.columns = [1]
        minSoC = self.Dict1D(minSoC, min_state)
        return minSoC

    def StorageLife(self):
        lifeTimeStorages = {}
        LifeBattery = pd.DataFrame(
            list(self.StorageData.loc["LifeBat (year)"]))
        LifeBattery.columns = [1]
        lifeTimeStorages = self.Dict1D(lifeTimeStorages, LifeBattery)
        return lifeTimeStorages

    def StorageLinCost(self):
        linStorageCosts = {}
        LinearCostStorage = pd.DataFrame(
            list(self.StorageData.loc["CostBat (chf/kWh)"]))
        LinearCostStorage.columns = [1]
        linStorageCosts = self.Dict1D(linStorageCosts, LinearCostStorage)
        return linStorageCosts

    def StorageNPV(self):
        Interest_rate_R = self.InterestRate()
        LifeBattery = pd.DataFrame(
            list(self.StorageData.loc["LifeBat (year)"]))
        LifeBattery.columns = [1]
        NetPresentValueStor = {}
        NetPresentValueStorage = 1 / (((1 + Interest_rate_R) ** LifeBattery - 1) / (
            Interest_rate_R * ((1 + Interest_rate_R) ** LifeBattery)))
        NetPresentValueStor = self.Dict1D(
            NetPresentValueStor, NetPresentValueStorage)
        return NetPresentValueStor
