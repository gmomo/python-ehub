import pylp
from energy_hub import EHubModel
from run import pretty_print


def network_constraint(hub1, hub2):
    for t in hub1.time:
        yield (hub1.energy_imported[t]['Network']
               <= hub2.energy_exported[t]['Elec'])
        yield (hub2.energy_imported[t]['Network']
               <= hub1.energy_exported[t]['Elec'])


def main():
    hub1 = EHubModel(excel='hub1.xlsx')
    hub2 = EHubModel(excel='hub2.xlsx')

    constraints = hub1.constraints + hub2.constraints
    obj = hub1.objective + hub2.objective

    for c in network_constraint(hub1, hub2):
        constraints.append(c)

    status = pylp.solve(objective=obj, constraints=constraints, minimize=True)

    print(obj.evaluate())

    result = {
        'version': '0.1',
        'solver': {
            'termination_condition': status.status,
            'time': status.time,
        },
        'solution': {},
    }



    result['solution'] = hub1._public_attributes()
    pretty_print(result)
    result['solution'] = hub2._public_attributes()
    pretty_print(result)


if __name__ == '__main__':
    main()
