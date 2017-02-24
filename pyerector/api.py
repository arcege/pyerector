#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Package: pyerector.api
While this module is mostly empty, it gives access to the routines that
a PyErector developer would need most: Abort, Error, Iterator, Mapper,
PyThread, Subcommand.

Other routines are imported from the pyerector.__init__ module by default.

XXX Future development may see more things moved here from pyerector.
"""

# This is almost no overhead, just the size of a module; everything would
# have already been imported by 'pyerector'.

from .exception import Abort, Error
from .args import Arguments
from .execute import get_current_stack, PyThread
# pylint: disable=unused-import
from .variables import V, Variable, VariableSet
# pylint: disable=unused-import
from .helper import Exclusions, normjoin, Subcommand, Timer
# pylint: disable=unused-import
from .base import Initer
# pylint: disable=unused-import
from .iterators import Iterator, Mapper
# pylint: disable=unused-import
from .targets import Target
# pylint: disable=unused-import
from .tasks import Task, IteratorTask, MapperTask
# pylint: disable=unused-import
from .vcs.base import DVCSBase, VCSBase

# deprecated names
# pylint: disable=invalid-name
DVCS_Base = DVCSBase
# pylint: disable=invalid-name
VCS_Base = VCSBase

__all__ = [
    'Abort', 'Arguments', 'Error', 'DVCSBase', 'get_current_stack',
    'Iterator', 'IteratorTask', 'Mapper', 'MapperTask', 'PyThread',
    'Subcommand', 'Target', 'Task', 'VCSBase',
]

