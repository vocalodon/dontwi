# -*- coding: utf-8 -*-
""" Exception classes
"""


class DontwiNotImplementedError(NotImplementedError):
    pass


class DontwiConfigError(AttributeError):
    pass


class DontwiMediaError(IOError):
    pass
