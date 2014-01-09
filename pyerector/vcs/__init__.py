#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Determine the version control system being used."""

import os

from ..variables import V
from .base import Base

__all__ = [
    'VCS'
]

def load_plugins():
    """Find modules in pyerector.vcs (that are not __init__ and base) and
load them."""
    from sys import modules
    curdir = os.path.dirname(__file__)
    # only get the *.py files
    names = [os.path.splitext(f)[0] for f in os.listdir(curdir)
                if f.endswith('.py') and 
                   f not in ('__init__.py', 'base.py')
    ]
    try:
        from importlib import import_module
        whereami = modules[__name__]
        for name in names:
            modname = '%s.%s' % (__name__, name)
            import_module(modname)
    except ImportError:
        __import__(__name__, fromlist=names)

def VCS(*args, **kwargs):
    """Determine the type of version control and return information
about it.
"""
    load_plugins()
    try:
        basedir = V['basedir']
    except KeyError:
        basedir = os.curdir
    for vcs in Base.registered():
        if vcs.vcs_check(srcdir=basedir):
            break
    else:
        raise RuntimeError('no version control found')
    return vcs(*args, **kwargs)

