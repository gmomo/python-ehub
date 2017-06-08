import numpy as np

from ehub_model import EHubModel
from cli import pretty_print
from plotting import Figure, Figures
from plotting.plots import (
    LineChart, BarChart, StackedBarChart,
    StackedLineChart
)


def to_numpy(variables):
    for name, variable in variables.items():
        if isinstance(variable, list):
            variable = np.matrix(variable)
        variables[name] = variable


def main():
    np.set_printoptions(linewidth=1000, suppress=True)

    model = EHubModel(excel="input_test.xlsx")

    result = model.solve()
    pretty_print(result)

    variables = result['solution']['variables']
    parameters = result['solution']['parameters']

    to_numpy(variables)
    to_numpy(parameters)

    P = variables['P']
    Pexport = variables['Pexport']
    Yon = variables['Yon']
    Qin = variables['Qin']
    Qout = variables['Qout']
    E = variables['E']

    cMatrix = parameters['cMatrix']
    loads = parameters['loads']
    solarEm = parameters['solarEm']
    carbonFactors = parameters['carbonFactors']

    num_hours = len(P)
    time = np.linspace(0, num_hours, num_hours)

    P_plot = get_P_plot(time, P)
    stacked_P_plot = get_stacked_P_plot(time, P)
    Pexport_plot = get_Pexport_plot(time, Pexport)
    Yon_plot = get_Yon_plot(time, Yon)
    loads_and_solar_plot = get_plot_of_loads_and_solar(time, loads, solarEm)
    charge_plot = get_charge_plot(time, Qin, Qout)
    net_charge_plot = get_net_charge_plot(time, Qin, Qout)
    state_of_charge_plot = get_state_of_charge_plot(time, E)
    storage_vs_loads_plot = get_storage_vs_loads(time, E, loads)
    carbon_plot = create_carbon_plot(time, P, carbonFactors)
    tech_carbon_plot = create_carbon_per_tech_plot(time, P, carbonFactors)
    total_tech_carbon_plot = create_total_carbon_per_tech_plot(time, P, carbonFactors)


    figures = Figures()

    figure = Figure('Stacked P')
    figure.add(stacked_P_plot)
    figures.add(figure)

    figure = Figure("Various plots", num_rows=2, num_cols=2)
    figure.add(P_plot, row=1, col=1)
    figure.add(Pexport_plot, row=1, col=2)
    figure.add(loads_and_solar_plot, row=2, col=1)
    figure.add(carbon_plot, row=2, col=2)
    figures.add(figure)

    figure = Figure("Various Charges", num_rows=2, num_cols=2)
    figure.add(charge_plot, row=1, col=1)
    figure.add(net_charge_plot, row=1, col=2)
    figure.add(state_of_charge_plot, row=2, col=1)
    figure.add(storage_vs_loads_plot, row=2, col=2)
    figures.add(figure)

    figure = Figure("cMatrix", num_rows=1, num_cols=1)
    figure.add(create_cMatrix_plot(cMatrix))
    figures.add(figure)

    figure = Figure("Example stacked bar chart", num_rows=1, num_cols=1)
    figure.add(create_stacked_bar_chart(cMatrix))
    figures.add(figure)

    figure = Figure("Carbon plots", num_rows=2, num_cols=2)
    figure.add(carbon_plot, row=1)
    figure.add(tech_carbon_plot, row=2, col=1)
    figure.add(total_tech_carbon_plot, row=2, col=2)
    figures.add(figure)

    figure = Figure('Stacked Line Plot')
    plot = StackedLineChart('eg')
    x = np.arange(1, 3)
    plot.plot(x=x, y=x, label='1')
    plot.plot(x=x, y=x, label='2')
    plot.plot(x=x, y=x, label='3')
    figure.add(plot)
    figures.add(figure)

    figures.show()


def get_stacked_P_plot(time, P):
    plot = StackedLineChart('Plot of P')

    plot.plot(x=time, y=P.T[0].T, label='Grid')
    for i, col in enumerate(P.T[1:], start=1):
        label = "Tech {}".format(i)
        plot.plot(x=time, y=col.T, label=label)

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Amount of energy input'
    plot.legend_location = 'upper left'

    return plot


def create_total_carbon_per_tech_plot(time, P, carbonFactors):
    plot = LineChart('Total Carbon produced per tech')

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Total amount of carbon'

    carbon = np.multiply(P, carbonFactors)
    total_carbon = carbon.cumsum(axis=0)  # Accumulate over time

    plot.plot(x=time, y=total_carbon.T[0].T, label='Grid')
    for i, (carbon, total_carbon) in enumerate(
            zip(carbon.T[1:], total_carbon.T[1:]), start=1):
        label = 'Tech {}'.format(i)

        plot.plot(x=time, y=total_carbon.T, label=label)

    return plot


def create_carbon_per_tech_plot(time, P, carbonFactors):
    plot = LineChart('Carbon produced per tech')

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Amount of carbon'

    carbon = np.multiply(P, carbonFactors)
    print(carbon)
    total_carbon = carbon.cumsum(axis=0)  # Accumulate over time
    print(total_carbon)

    plot.plot(x=time, y=carbon.T[0].T, label='Grid')
    for i, (carbon, total_carbon) in enumerate(zip(carbon.T[1:], total_carbon.T[1:]), start=1):
        label = 'Tech {}'.format(i)

        plot.plot(x=time, y=carbon.T, label=label)

    return plot


def create_carbon_plot(time, P, carbonFactors):
    plot = LineChart('Carbon produced')

    plot.x_axis = 'Time (hours)'
    plot.y_axes = ['Amount of carbon', 'Total amount of carbon']
    plot.legend_locations = ['upper left', 'upper right']

    carbon = P * carbonFactors.T

    plot.plot(x=time, y=carbon, label='Carbon', color='r',
              y_axis='Amount of carbon')
    plot.plot(x=time, y=carbon.cumsum().T, label='Total Carbon', color='b',
              y_axis='Total amount of carbon')

    return plot


def create_stacked_bar_chart(cMatrix):
    bar = StackedBarChart('cMatrix')

    bar.x_axis = 'Energy Streams'
    bar.y_axis = 'Conversion rate'

    bar.x = ['Electricity', 'Heat', 'Heat2']

    bar.plot(y=cMatrix[0].T, label='Grid')
    for i, tech in enumerate(cMatrix[1:], start=1):
        bar.plot(y=tech.T, label='Tech {}'.format(i))

    return bar


def create_cMatrix_plot(cMatrix):
    bar = BarChart('cMatrix')

    bar.x_axis = 'Energy Streams'
    bar.y_axis = 'Conversion rate'

    bar.x = ['Grid'] + ['Tech {}'.format(i) for i in range(1, 9)]

    bar.plot(y=cMatrix.T[0].T, label='Electricity')
    bar.plot(y=cMatrix.T[1].T, label='Heat')
    bar.plot(y=cMatrix.T[2].T, label='Heat2')

    return bar


def create_bar_chart():
    bar = BarChart('title')

    bar.x_axis = 'groups'
    bar.y_axis = 'scores'
    bar.legend_location = 'upper right'

    bar.x = ['a', 'b', 'c']

    bar.plot(y=[1, 2, 3], label='Men')
    bar.plot(y=[3, 2, 1], label='Women')
    bar.plot(y=[3, 3, 3], label='Others')

    return bar


def get_charge_plot(time, Qin, Qout):
    plot = LineChart("Qin and Qout vs time")

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Charge'

    labels = ['Electricity', 'Heat', 'Heat 2']

    for i, label in enumerate(labels):
        qin, qout = Qin.T[i].T, -Qout.T[i].T
        plot.plot(x=time, y=qin, label=label + ' in')
        plot.plot(x=time, y=qout, label=label + ' out')

    return plot


def get_net_charge_plot(time, Qin, Qout):
    plot = LineChart("Net Charge vs time")

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Net charge'

    net_q = Qin - Qout
    plot.plot(x=time, y=net_q.T[0].T, label='Electricity')
    plot.plot(x=time, y=net_q.T[1].T, label='Electricity')
    plot.plot(x=time, y=net_q.T[2].T, label='Electricity')

    return plot


def get_state_of_charge_plot(time, E):
    plot = LineChart('State of Charge vs. time')

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'State of Charge'

    plot.plot(x=time, y=E.T[0].T, label='Electricity')
    plot.plot(x=time, y=E.T[1].T, label='Heat')
    plot.plot(x=time, y=E.T[2].T, label='Heat 2')

    return plot


def get_storage_vs_loads(time, E, loads):
    plot = LineChart('Storage and Demands vs. time')

    plot.x_axis = 'Time (hours)'
    plot.y_axes = ['Storage', 'Demands']
    plot.legend_locations = ['upper left', 'upper right']

    labels = ['Electricity', 'Heat', 'Heat 2']
    demand_colors = ['y', 'r', 'g']

    for i, (label, demand_color) in enumerate(zip(labels, demand_colors)):
        load, storage = loads.T[i].T, E.T[i].T

        plot.plot(x=time, y=load, label=label, color=demand_color,
                  y_axis='Demands')
        plot.plot(x=time, y=storage, label=label, y_axis='Storage')

    return plot


def get_P_plot(time, P):
    plot = LineChart('Plot of P')

    plot.plot(x=time, y=P.T[0].T, label='Grid')
    for i, col in enumerate(P.T[1:], start=1):
        label = "Tech {}".format(i)
        plot.plot(x=time, y=col.T, label=label)

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Amount of energy input'
    plot.legend_location = 'upper left'

    return plot


def get_Pexport_plot(time, Pexport):
    plot = LineChart('Plot of Pexport')

    plot.plot(x=time, y=Pexport.T[0].T, label='Electricity')
    plot.plot(x=time, y=Pexport.T[1].T, label='Heat 1')
    plot.plot(x=time, y=Pexport.T[2].T, label='Heat 2')

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Energy exported'

    return plot


def get_Yon_plot(time, Yon):
    plot = LineChart('Plot of Yon')

    for i, col in enumerate(Yon.T[1:], start=1):
        if col.any() is not None:
            label = "Tech {}".format(i)
            plot.plot(x=time, y=col.T, label=label)

    plot.x_axis = 'Time (hours)'
    plot.y_axis = 'Is on?'

    return plot


def get_plot_of_loads_and_solar(time, loads, solarEm):
    plot = LineChart('Plot of loads and solarEm')

    plot.x_axis = 'Time (hours)'
    plot.y_axes = ['Demands', 'Solar Irradiation']
    plot.legend_locations = ['upper left', 'upper right']

    plot.plot(x=time, y=loads.T[0].T, label='Electricity', y_axis='Demands')
    plot.plot(x=time, y=loads.T[1].T, label='Heat', y_axis='Demands')
    plot.plot(x=time, y=loads.T[2].T, label='Heat2', y_axis='Demands')
    plot.plot(x=time, y=solarEm.T, label='Solar', color='y',
              y_axis='Solar Irradiation')

    return plot


if __name__ == "__main__":
    main()
