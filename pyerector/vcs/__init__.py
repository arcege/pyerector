#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Determine the version control system being used."""

import os

from ..execute import Initialization
from ..path import Path
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
    names = [
        os.path.splitext(f)[0] for f in os.listdir(curdir)
        if f.endswith('.py') and
        f not in ('__init__.py', 'base.py')
    ]
    try:
        from importlib import import_module
        for name in names:
            modname = '%s.%s' % (__name__, name)
            import_module(modname)
    except ImportError:
        __import__(__name__, fromlist=names)

# pylint: disable=invalid-name
def VCS(*args, **kwargs):
    """Determine the type of version control and return information
about it.
"""
    load_plugins()
    try:
        basedir = V['basedir']
    except KeyError:
        basedir = Path(os.curdir)
    vcs = Base.vcs_check(srcdir=basedir)
    if vcs.name is None:
        raise RuntimeError('no version control found')
    return vcs(*args, **kwargs)

class InitVCS(Initialization):
    """Initialize the version control system, assigning to the
pyerector.vcs variable.
"""
    def run(self):
        from logging import getLogger
        logger = getLogger('pyerector')
        try:
            vcs = VCS()
        except RuntimeError:
            logger.info('No VCS found')
        else:
            vcs.current_info()
            V['pyerector.vcs'] = vcs
            logger.info('Found %s', vcs)

InitVCS()
