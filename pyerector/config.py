#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from warnings import warn

from .variables import V

__all__ = [
    'Config',
    'noop',
    'noTimer',
]


class Config(object):
    """Deprecated, but still provide the same interface, but to variables."""
    def __getattr__(self, variable):
        warn('Config has been deprecated', DeprecationWarning)
        return V[variable]

    def __setattr__(self, variable, value):
        warn('Config has been deprecated', DeprecationWarning)
        V[variable] = value


class State(object):
    def __init__(self, initial=False):
        self.state = initial

    def __bool__(self):
        return self.state
    __nonzero__ = __bool__

    def on(self):
        self.state = True

    def off(self):
        self.state = False

noop = State()

# display timing information, changed in pyerector.main.PyErector
noTimer = State()

