#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Subpackage of the packaged tasks."""

import sys

from ..execute import Initialization
from ..path import Path
from ..variables import V
from ._base import Task, IteratorTask, MapperTask

__all__ = [
]

def load_plugins():
    """Find modules in pyerector.tasks and load them."""
    curdir = Path(__file__).dirname
    names = [
        fname.basename.delext().value for fname in curdir
        if fname.basename.value.endswith('.py') and
        not fname.basename.value.startswith('_')]
    try:
        from importlib import import_module
        for name in names:
            modname = '%s.%s' % (__name__, name)
            import_module(modname)
    except ImportError:
        __import__(__name__, fromlist=names)
    return names


class InitTasks(Initialization):
    """Initialize builtin tasks as plugins."""
    def run(self):
        from logging import getLogger
        logger = getLogger('pyerector.tasks')
        try:
            names = load_plugins()
        except RuntimeError:
            logger.exception('Cannot load task plugins.')
        else:
            this = sys.modules[__name__]
            names = []
            for cls in Task.registered():
                name = cls.__name__
                setattr(this, name, cls)
                if name not in __all__:
                    __all__.append(name)
                names.append(name)
            logger.info('Tasks loaded: %s', names)

InitTasks()
