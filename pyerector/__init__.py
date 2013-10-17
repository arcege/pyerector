#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Package: pyerector
A framework to build products based on tasks and targets.  The thought
is, distutils/setuptools is to Maven as PyErector is to Ant.  The former
requires that you shoehorn project to fit into their model.  PyErector is
a toolkit/framework, like Make and Ant, giving you routines to set up
what you want/need to do.  It is geared more toward Python usage, but
most tasks are generic enough for any system.

The developer would create a driver file, commonly named 'pyerect',
that would include the 'pyerector' module generally using.  The smallest
driver file would be:
    from pyerector import *
    PyErector()

The PyErector main routine will scan the command-line arguments for
target names, if none are found, then it will call the default target.
Target references on the command-line are the same as the class, but
with the first character lowercase.  The command-line argument 'default'
would refer to the 'Default' Target class.

Command-line arguments must reference targets, not other objects (except
variable assignments).  Instead of referencing a Target, a command-line
argument may also assign a string value to a variable, for example:
"developer.name=Michael".

After command-line arguments are processed, PyErector() will verify the
classes are properly constructed and then call the target references in
turn.

The package is broken into three primary types of objects: standard
targets, standard tasks and the API.  All standard targets could be
subclassed, but would not be, in general.  Instead the class members
would be modified in the driver file:
    InitDirs.files = ('build',)
    Compile.tasks = (Copy('foobar.txt', dest='build'),)

As you can see with the Copy task above, the most common usage is to
create instances within a target's class members, like 'tasks'.
"""

from .helper import normjoin, Exclusions
from .helper import display, warn, verbose, debug  # being deprecated
from .execute import Initialization

from .version import *
from .main import PyErector, pymain
from .base import *
from .tasks import  *
from .targets import *
from .iterators import *
from .variables import *
from .vcs import *

__all__ = [
    # base routines
    'Exclusions',
    'normjoin',
    'PyErector',
    'pymain',
    'Target',
    'Task',
    'Sequential',
    'Parallel',
    'V',  # alias for Variable
    'Variable',
    'VariableSet',
    'VCS',

    # tasks
    'Chmod',
    'Copy',
    'CopyTree',
    'Echo',
    'Egg',
    'HashGen',
    'Java',
    'Mkdir',
    'PyCompile',
    'Remove',
    'Shebang',
    'Spawn',
    'SubPyErector',
    'Tar',
    'Tokenize',
    'Unittest',
    'Untar',
    'Unzip',
    'Zip',

    # targets
    'All',
    'Build',
    'Clean',
    'Compile',
    'Default',
    'Dist',
    'Help',
    'Init',
    'InitDirs',
    'InitVCS',
    'Packaging',
    'Test',

    # iterators
    'FileSet',
    'StaticIterator',
    'FileIterator',
    'FileList',
    'DirList',
    # mappers
    'FileMapper',
    'BasenameMapper',
    'MergeMapper',
    'Uptodate',
]

Initialization.start()

