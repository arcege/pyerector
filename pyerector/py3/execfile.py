#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Redefine the execfile in Python 3.x, which was removed."""

import sys

__all__ = [
    'execfile'
]


def execfile(filename, globals=None, locals=None):
    """Reproduce the Python2 execfile() function."""
    if globals is None:
        globals = sys._getframe(1).f_globals
    if locals is None:
        locals = sys._getframe(1).f_locals
    with open(filename, 'rt') as filehandle:
        exec(filehandle.read()+"\n", globals, locals)

