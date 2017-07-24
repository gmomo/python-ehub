import pylp
from energy_hub import EHubModel
from energy_hub.utils import constraint
from run import pretty_print, print_section


class NetworkModel(EHubModel):
    @constraint('time', 'technologies')
    def energy_imported_is_above_zero(self, t, tech):
        if tech == 'Network':
            return None

        return super().energy_imported_is_above_zero(t, tech)


def network_constraint(hub1, hub2):
    for t in hub1.time:
        yield (hub1.energy_imported[t]['Network']
               == -hub2.energy_imported[t]['Network'])


def main():
    hub1 = NetworkModel(excel='hub1.xlsx')
    hub2 = NetworkModel(excel='hub2.xlsx')

    constraints = hub1.constraints + hub2.constraints
    obj = hub1.objective + hub2.objective

    for c in network_constraint(hub1, hub2):
        constraints.append(c)

    pylp.solve(objective=obj, constraints=constraints, minimize=True)

    print_section('Hub1', hub1.__dict__)
    print_section('Hub2', hub2.__dict__)
    print(obj.evaluate())


if __name__ == '__main__':
    main()
