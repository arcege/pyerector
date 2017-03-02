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
    def __init__(self, name, initial=False):
        self.name = name
        self.state = initial

    @property
    def state(self):
        warn("use '%s' variable instead." % self.name, DeprecationWarning)
        return V[self.name]
    @state.setter
    def state(self, value):
        warn("use '%s' variable instead." % self.name, DeprecationWarning)
        V[self.name] = value

    def __bool__(self):
        return self.state
    __nonzero__ = __bool__

    # pylint: disable=invalid-name
    def on(self):
        """Change state to True."""
        warn("use '%s' variable instead." % self.name, DeprecationWarning)
        self.state = True

    def off(self):
        """Change state to False."""
        warn("use '%s' variable instead." % self.name, DeprecationWarning)
        self.state = False

# pylint: disable=invalid-name
noop = State('pyerector.noop')

# display timing information, changed in pyerector.main.PyErector
# pylint: disable=invalid-name
noTimer = State('pyerector.notimer')

