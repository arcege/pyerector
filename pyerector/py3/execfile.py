#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Redefine the execfile in Python 3.x, which was removed."""

import sys

__all__ = [
    'execfile'
]


# pylint: disable=redefined-builtin
def execfile(filename, globals=None, locals=None):
    """Reproduce the Python2 execfile() function."""
    # pylint: disable=redefined-builtin
    if globals is None:
        # pylint: disable=protected-access
        globals = sys._getframe(1).f_globals
    # pylint: disable=redefined-builtin
    if locals is None:
        # pylint: disable=protected-access
        locals = sys._getframe(1).f_locals
    with open(filename, 'rt') as filehandle:
        # pylint: disable=exec-used
        exec(filehandle.read()+"\n", globals, locals)

