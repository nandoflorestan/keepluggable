"""Special exceptions raised by keepluggable."""


class FileNotAllowed(Exception):
    """Thrown when a file shouldn't be stored. The message must explain why."""
