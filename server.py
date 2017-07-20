"""
A server for remotely solving an energy hub model.
"""
import json
from multiprocessing.pool import Pool
from socketserver import ThreadingMixIn
from xmlrpc.server import SimpleXMLRPCServer
import logging

import server_logging
from energy_hub import EHubModel
from data_formats import request_format

# This URL is for inside the Docker container
SERVER_URL = '0.0.0.0:8080'


class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    """A multi-threaded version of a XMLRPC server."""


# This is not a constant but pylint doesn't see that
# pylint: disable=invalid-name
web_service_functions = []


def web_service(func):
    """Mark a function as a XMLRPC callable function.

    Args:
        func: The function to be marked as a XMLRPC callable function.

    Returns:
        The marked function
    """
    web_service_functions.append(func)

    return func


def worker_process(request: dict):
    """The function for a worker subprocess.

    A subprocess is created because glpk and Pyomo are not thread-safe.

    Args:
        request: An instance of the request format to be solved

    Returns:
        The results of solving the model
    """
    model = EHubModel(request=request)

    return model.solve(is_verbose=True)


@web_service
def solve(request):
    """Solve the EHubModel for an instance of the request format.

    Args:
        request: The JSON representation of the the request format to be solved

    Returns:
        A JSON representation of the solution
    """
    request = json.loads(request)

    logging.info('Start validation of request')
    request_format.validate(request)
    logging.info('Request validated')

    with Pool(processes=1) as subprocess:
        response = subprocess.apply(worker_process, (request,))

    logging.info('Sending response back')
    return json.dumps(response)


def main():
    """The main function of the server."""
    server_logging.create_logger('server_logs.log')

    ip, port = SERVER_URL.split(':')
    with ThreadedXMLRPCServer((ip, int(port))) as server:
        for func in web_service_functions:
            server.register_function(func)

        server.serve_forever()


if __name__ == "__main__":
    main()
