# -*- coding: utf-8 -*-
""" Exception classes
"""

class DontwiNotImplementedError(NotImplementedError):
    """Raised when not implemented method was called.
    """
    pass


class DontwiConfigError(AttributeError):
    """Raised when reading or parsing error occurred.

    Attributes:
        message -- explanation of why the specific transition is not allowed
    """
    def __init__(self, message):
        self.message = message


class DontwiMediaError(IOError):
    """Raised when reading or processing error occurred.
    """
    pass
