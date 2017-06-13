"""Converts Excel files into the request format."""

import argparse
import json
from contextlib import suppress

import jsonschema
import xlrd

from data_formats import request_format


class FormatUnsupportedError(Exception):
    """The Excel format is not supported."""


def convert(excel_file):
    """Convert the excel file into the request format.

    Args:
        excel_file: The path to the excel file

    Returns:
        The request format as a Python dict
    """
    for subclass in Converter.__subclasses__():
        converter = subclass(excel_file)

        # Assume that any errors are due to the format and nothing else
        with suppress(Exception):
            return converter.convert()

    # Found no converter for the excel file
    raise FormatUnsupportedError


class Converter:
    """The SuperClass for all Excel-to-request-format converters.
    
    All a subclass needs to do is implement all the abstract methods and the 
    superclass does the rest of the work.
    """

    def __init__(self, excel_file):
        """Create a new converter for the Excel file.

        Args:
            excel_file: The path to the excel file
        """
        self._excel_file = excel_file
        self._file = xlrd.open_workbook(excel_file)

    def _get_columns(self, sheet_name, start=0):
        sheet = self._file.sheet_by_name(sheet_name)

        for colx in range(start, sheet.ncols):
            yield sheet.col_values(colx)

    def _get_general(self):
        raise NotImplementedError

    def _get_capacities(self):
        raise NotImplementedError

    def _get_streams(self):
        raise NotImplementedError

    def _get_converters(self):
        raise NotImplementedError

    def _get_storages(self):
        raise NotImplementedError

    def _get_system_types(self):
        raise NotImplementedError

    def _get_time_series(self):
        raise NotImplementedError

    def _get_network_nodes(self):
        raise NotImplementedError

    def _get_network_links(self):
        raise NotImplementedError

    def convert(self):
        """Convert the file into the request format.

        Returns:
            The request format
        """
        request = {
            'version': '0.1.0',
            'general': self._get_general(),
            'capacities': self._get_capacities(),
            'streams': self._get_streams(),
            'converters': self._get_converters(),
            'storages': self._get_storages(),
            'system_types': self._get_system_types(),
            'time_series': self._get_time_series(),
            # 'network': {
            #     'nodes': self._get_network_nodes(),
            #     'links': self._get_network_links(),
            # }
        }

        return request


class _NewFormatConverter(Converter):
    def _get_columns(self, sheet_name, start=0):
        # The first column holds all the names for the rows
        return super()._get_columns(sheet_name, start=1)

    def _get_general(self):
        sheet = self._file.sheet_by_name('General')

        return {
            'interest_rate': sheet.cell(1, 1).value,
        }

    def _get_capacities(self):
        capacities = []
        for column in self._get_columns('Capacities'):
            (name, units, item_type, options, lower_bound,
             upper_bound) = column

            capacity = {
                'name': name,
                'units': units,
                'type': item_type,
            }

            if options:
                if item_type == 'List':
                    options = [int(x) for x in options.split(',')]

                capacity['options'] = options

            if lower_bound or upper_bound:
                capacity['bounds'] = {}

                if lower_bound:
                    capacity['bounds']['lower'] = lower_bound

                if upper_bound:
                    capacity['bounds']['upper'] = upper_bound

            capacities.append(capacity)

        return capacities

    def _get_streams(self):
        streams = []
        for column in self._get_columns('Streams'):
            (name, availability, price, export_price, co2) = column

            stream = {
                'name': name,
                'price': price,
                'export_price': export_price,
                'co2': co2,
            }

            if availability:
                stream['availability'] = availability

            streams.append(stream)

        return streams

    def _get_converters(self):
        converters = []
        for column in self._get_columns('Converters'):
            (name, capacity, capital_cost, annual_maintenance_cost,
             usage_maintenance_cost, efficiency, lifetime, output_ratio,
             min_load, inputs, outputs) = column

            converter = {
                'name': name,
                'efficiency': float(efficiency),
            }

            if capacity:
                try:
                    capacity = int(capacity)
                except ValueError:
                    # References a capacity in the capacities
                    capacity = str(capacity)

                converter['capacity'] = capacity

            if capital_cost:
                converter['capital_cost'] = float(capital_cost)

            if annual_maintenance_cost:
                annual_maintenance_cost = float(annual_maintenance_cost)
                converter['annual_maintenance_cost'] = annual_maintenance_cost

            if usage_maintenance_cost:
                usage_maintenance_cost = float(usage_maintenance_cost)
                converter['usage_maintenance_cost'] = usage_maintenance_cost

            if lifetime:
                converter['lifetime'] = float(lifetime)

            if output_ratio:
                converter['output_ratio'] = float(output_ratio)

            if min_load:
                converter['min_load'] = float(min_load)

            if inputs:
                converter['inputs'] = inputs.split(',')

            if outputs:
                converter['outputs'] = outputs.split(',')

            converters.append(converter)

        return converters

    def _get_storages(self):
        storages = []
        for column in self._get_columns('Storages'):
            (name, stream, __, cost, lifetime, charge_efficiency,
             discharge_efficiency, decay, max_charge, max_discharge,
             min_state) = column

            storage = {
                'name': name,
                'stream': stream,
                'cost': float(cost),
                'lifetime': float(lifetime),
                'charge_efficiency': float(charge_efficiency),
                'discharge_efficiency': float(discharge_efficiency),
                'decay': float(decay),
                'max_charge': float(max_charge),
                'max_discharge': float(max_discharge),
                'min_state': float(min_state),
            }

            storages.append(storage)

        return storages

    def _get_system_types(self):
        system_types = []
        for column in self._get_columns('System types'):
            (name, *technologies) = column

            technologies = [tech for tech in technologies
                            if tech]

            system_type = {
                'name': name,
                'technologies': technologies
            }
            system_types.append(system_type)

        return system_types

    def _get_time_series(self):
        time_series_list = []
        for column in self._get_columns('Time series'):
            (series_id, series_type, stream, node, units, source,
             *rest) = column

            data = rest[3:]  # Remove empty lines

            time_series = {
                'id': series_id,
                'type': series_type,
                'stream': stream,
                'units': units,
                'data': [int(d) for d in data if d],
            }

            if source:
                time_series['source'] = source

            if node:
                time_series['node'] = int(node)

            time_series_list.append(time_series)

        return time_series_list

    def _get_network_nodes(self):
        nodes = []
        for column in self._get_columns('Network nodes'):
            (node_id, geo_coords, grid_coords, building_id, building_type,
             system_id, system_type) = column

            node = {
                'id': int(node_id),
                'coords': {},
                'building': {
                    'id': int(building_id),
                    'type': building_type,
                },
                'system': {
                    'id': int(system_id),
                    'type': system_type,
                },
            }

            if geo_coords:
                (latitude, longitude) = geo_coords.split(',')

                node['coords']['latitude'] = float(latitude)
                node['coords']['longitude'] = float(longitude)

            if grid_coords:
                (x, y) = grid_coords.split(',')

                node['coords']['x'] = float(x)
                node['coords']['y'] = float(y)

            if system_id:
                node['system']['id'] = system_id

            if system_type:
                node['system']['type'] = system_type

            nodes.append(node)

        return nodes

    def _get_network_links(self):
        links = []
        for column in self._get_columns('Network links'):
            (link_id, start_id, end_id, link_type, length, capacity, voltage,
             electrical_resistance, electrical_reactance, total_thermal_loss,
             total_pressure_loss, operating_temperature) = column

            link = {
                'id': int(link_id),
                'start_id': int(start_id),
                'end_id': int(end_id),
                'type': link_type,
                'length': float(length),
                'capacity': float(capacity),
                'voltage': float(voltage),
                'electrical_resistance': float(electrical_resistance),
                'electrical_reactance': float(electrical_reactance),
                'total_thermal_loss': float(total_thermal_loss),
                'total_pressure_loss': float(total_pressure_loss),
                'operating_temperature': float(operating_temperature),
            }

            links.append(link)

        return links


def parse_args():
    """Parses the command-line arguments."""

    parser = argparse.ArgumentParser(
        description='Converts an excel file into a EHub Request format.')
    parser.add_argument('excel_file',
                        help='The excel file to convert',
                        )
    parser.add_argument('output_file',
                        help='The file to output the results to',
                        )
    return parser.parse_args()


def main():
    args = parse_args()

    content = convert(args.excel_file)

    # Ensure the format is correct
    jsonschema.validate(content, request_format.schema)

    with open(args.output_file, 'w') as file:
        file.write(json.dumps(content))

if __name__ == "__main__":
    main()
