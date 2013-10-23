#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
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
from .execute import get_current_stack, PyThread
from .variables import V, Variable, VariableSet
from .helper import Exclusions, normjoin, Subcommand, Timer
from .iterators import BaseIterator
from .base import Initer, Iterator, Mapper, Target, Task
from .vcs.base import DVCS_Base, VCS_Base

__all__ = [
    'Abort', 'Error', 'DVCS_Base', 'get_current_stack', 'Iterator',
    'Mapper', 'PyThread', 'Subcommand', 'Target', 'Task', 'VCS_Base',
]

