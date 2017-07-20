"""
Contains logging functionality for the server.
"""
import logging


def create_logger(filename: str) -> None:
    """
    Add logging to the application.

    Args:
        filename: The name of the log file
    """
    # logging accepts all logs, which are then handled later
    logging.getLogger().setLevel(logging.DEBUG)

    add_console_handler()
    add_file_handler(filename)


def add_console_handler() -> None:
    """Add a logging handler for stderr."""
    # For use with Docker logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(get_server_formatter())

    logging.getLogger().addHandler(console_handler)


def add_file_handler(filename: str) -> None:
    """
    Add a logging handler for a log file.

    Args:
        filename: The name of the log file
    """
    file_handler = logging.FileHandler(filename, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(get_server_formatter())

    logging.getLogger().addHandler(file_handler)


def get_server_formatter() -> logging.Formatter:
    """
    Return a formatter for logging on a server.

    Returns:
        A logging.Formatter for the default format
    """
    # The thread ID is more useful than process ID since we create a subprocess
    # in the thread
    return logging.Formatter(
        '%(asctime)s.%(msecs)03d - '  # Hours:Minutes:Seconds.Milliseconds
        'Thread ID: %(thread)d - '
        '%(filename)s:%(lineno)d - '  # File:LineNumber
        '[%(levelname)s]: %(message)s',  # [INFO/DEBUG/...]: Message
        datefmt='%H:%M:%S'
    )
