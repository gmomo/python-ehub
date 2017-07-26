import excel_to_request_format
from energy_hub import EHubModel
from energy_hub.utils import constraint
from pylp import RealVariable
from run import pretty_print


class OESModel(EHubModel):
    def __init__(self, *, excel=None, request=None):
        self.oes_charge_cost = RealVariable()

        super().__init__(excel=excel, request=request)

    @constraint('time')
    def constraint_oes_charge_in(self, t):
        return self.energy_to_storage[t]['OES'] <= self.ChargeMax

    @constraint('time')
    def constraint_oes_charge_out(self, t):
        return self.energy_from_storage[t]['OES'] <= self.DischargeMax

    @constraint()
    def add_oes_charge_cost(self):
        return self.oes_charge_cost == 20 * self.ChargeMax

    @constraint()
    def calculate_total_cost(self):
        lhs, _, rhs = super().calculate_total_cost()._constraint

        return lhs == rhs + self.oes_charge_cost + self.total_carbon * 0.1

    @constraint('time')
    def calculate_wind_energy(self, t):
        wind_speed = [series for series in self._data.time_series_list
                      if series.name == 'Wind'][0]
        wind_converter = 'Wind'

        energy_imported = self.energy_imported[t][wind_converter]

        conversion_rate = self.CONVERSION_EFFICIENCY[wind_converter]['Elec']

        return energy_imported == wind_speed.data[t]


def main():
    request = excel_to_request_format.convert('excel_files/General_input_new_OES.xlsx')

    print('building')
    model = OESModel(request=request)

    print('sovling')
    results = model.solve({'name': 'cplex', 'options': None}, is_verbose=True)
    pretty_print(results)

if __name__ == '__main__':
    main()
