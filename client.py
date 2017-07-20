"""
An example of remotely solving a EHub Model.
"""
import json
import xmlrpc.client

import excel_to_request_format


# pylint: disable=all
def main():
    # We are reading from a excel file as an example
    file = 'excel_files/General_input_new_simple.xlsx'

    # Now we convert the excel file into the request format
    request = excel_to_request_format.convert(file)

    # And then convert the Python dictionary into a JSON object, which is stored
    # as a Python str
    request = json.dumps(request)


    url = 'http://localhost:8080'  # The URL of the server

    # Connect to the server
    with xmlrpc.client.ServerProxy(url) as server:
        # The `server` variable is used to make calls to the XMLRPC server.
        # Here, we call the `solve` method on the server. This method solves our
        # model, which is stored in the `contents` variable.
        results = server.solve(request)

    # Now we can manipulate the results ourselves
    print(json.loads(results))


if __name__ == '__main__':
    main()
