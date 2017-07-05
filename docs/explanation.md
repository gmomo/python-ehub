# Explanation of variables and parameters

**Note: This document will get out of date quickly. See the code for more 
up-to-date explanation.**

## Sets

* Technology: model.In
* Energy carrier: model.Out
* Node: model.hubs, model.hub_i, model.hub_j
* Timestep: model.Time

## Parameters

### Conversion technology parameters
* Efficiencies: model.cMatrix = Param(model.In, model.Out, initialize=data.cMatrix())                                       
* Max capacities: model.maxCapTechs = Param(model.hubs, model.DispTechs, initialize=data.MaxCapacity())
* model.maxCapTechsAll = Param(model.hubs, model.Techs, initialize=data.MaxCapacityALL())
* Min part load: model.partLoad = Param(model.In, model.Out, initialize=data.PartLoad()) 

### Storage tehnology parameters
* Standing losses: model.lossesStorStanding = Param(model.hubs, model.Out, initialize = data.StorageLoss())
* Max storage charge rate: model.maxStorCh = Param(model.hubs, model.Out, initialize=data.StorageCh())
* Max storage discharge rate: model.maxStorDisch = Param(model.hubs, model.Out, initialize= data.StorageDisch())
* Charging efficiency: model.chargingEff = Param(model.hubs, model.Out, initialize = data.StorageEfCh())
* Discharging efficiency: model.dischLosses = Param(model.hubs, model.Out, initialize = data.StorageEfDisch())
* Min state of charge: model.minSoC = Param(model.hubs, model.Out, initialize = data.StorageMinSoC())

### Cost parameters
* Linear capital costs: model.linCapCosts = Param(model.hubs, model.In, model.Out, initialize= data.LinearCost())        
* Linear capital costs for storage: model.linStorageCosts = Param(model.hubs, model.Out, initialize = data.StorageLinCost())
* Fuel prices: model.opPrices = Param( model.In, initialize=data.FuelPrice())  
* Electricity feed-in-tariff: model.feedInTariffs = Param(model.Out, initialize=data.FeedIn())              
* Variable/maintenance costs: model.omvCosts = Param(model.hubs, model.In, initialize=data.VarMaintCost())               
* Interest rate: model.interestRate = Param(within=NonNegativeReals, initialize=data.InterestRate())
* Technology lifetime: model.lifeTimeTechs = Param(model.hubs, model.In, initialize = data.LifeTime())
* Storage technology lifetime: model.lifeTimeStorages = Param(model.hubs, model.Out, initialize = data.StorageLife())

### District heating parameters
* Heat losses: model.HeatLosses=Param(model.hub_i, model.hub_j, initialize=0.001)
* Investment cost pipe: model.PipeCost=Param(initialize=200)
* Energy losses: model.Losses=Param(model.hub_i, model.hub_j, initialize=0.001 )

### Energy load parameters
* Energy demands: model.loads = Param(model.hub_i, model.Time, model.Out, initialize=data.Demands())

## Variables

### System variables
* Input energy: model.P = Var(model.hubs, model.Time, model.In, domain=NonNegativeReals)
* Energy exported: model.Pexport = Var(model.hubs, model.Time, model.Out, domain=NonNegativeReals)
* Technology capacity: model.Capacities = Var(model.hubs, model.In, model.Out, domain=NonNegativeReals)
* Technology installation: model.Ytechnologies = Var(model.hubs, model.In, model.Out, domain=Binary)
* Technology operation: model.Yon = Var(model.hubs, model.Time, model.In, domain=Binary)

### Cost and carbon variables
* Total cost: model.TotalCost = Var(domain=Reals)
* Operational cost: model.OpCost = Var(domain=NonNegativeReals)
* Maintenance cost: model.MaintCost = Var(domain=NonNegativeReals)
* Income from energy exports: model.IncomeExp = Var(domain=NonNegativeReals)
* Investment cost: model.InvCost = Var(domain=NonNegativeReals)
* Total carbon emissions: model.TotalCarbon = Var(domain=Reals)
* Total carbon emissions (necessary for Pyomo): model.TotalCarbon2 = Var(domain=Reals)
* Technology NPV: model.NetPresentValueTech = Param(model.In, domain=NonNegativeReals, initialize=data.NPV())
* Storage NPV: model.NetPresentValueStor = Param(model.Out, domain=NonNegativeReals, initialize=data.StorageNPV())

### District heating variables
* Energy transfer between nodes: model.DH_Q = Var(model.hub_i, model.hub_j,model.Time, model.Out, domain=NonNegativeReals)
* Pipe operation: model.Ypipeline = Var(model.hub_i, model.hub_j, domain=Binary)

### Storage variables
* Energy input to storage: model.Qin = Var(model.hubs, model.Time, model.Out, domain=NonNegativeReals)
* Energy output from storage: model.Qout = Var(model.hubs, model.Time, model.Out, domain=NonNegativeReals)
* Storage SOC: model.E = Var(model.hubs, model.Time, model.Out, domain=NonNegativeReals)
* Storage capacity: model.StorageCap = Var(model.hubs, model.Out, domain=NonNegativeReals)
* Storage installation: model.Ystorage = Param(model.hubs, model.Out, domain=Binary, initialize=data.StorageBinary())
