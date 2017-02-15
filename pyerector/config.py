#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Handle configuration values.

The Config class managed "variables" before global variables were
introduced.  This class has now been deprecated and exists only for
backward compatibility.

The State class is to give the same functionality as the now deprecated
Verbose class.  The "noop" and "noTimer" instances are initialized here
and turned on in PyErector.arguments().
"""

from warnings import warn

from .variables import V

__all__ = [
    'Config',
    'noop',
    'noTimer',
]


# pylint: disable=too-few-public-methods
class Config(object):
    """Deprecated, but still provide the same interface, but to variables."""
    def __getattr__(self, variable):
        warn('Config has been deprecated', DeprecationWarning)
        return V[variable]

    def __setattr__(self, variable, value):
        warn('Config has been deprecated', DeprecationWarning)
        V[variable] = value


class State(object):
    """Create a mutable boolean object."""
    def __init__(self, initial=False):
        self.state = initial

    def __bool__(self):
        return self.state
    __nonzero__ = __bool__

    # pylint: disable=invalid-name
    def on(self):
        """Change state to True."""
        self.state = True

    def off(self):
        """Change state to False."""
        self.state = False

noop = State()

# display timing information, changed in pyerector.main.PyErector
noTimer = State()

