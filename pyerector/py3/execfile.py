#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

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
    with open(filename, 'rt') as fh:
        exec(fh.read()+"\n", globals, locals)
