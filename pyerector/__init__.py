#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Package: pyerector
A framework to build products based on tasks and targets.  The thought
is, distutils/setuptools is to Maven as PyErector is to Ant.  The former
requires that you shoehorn project to fit into their model.  PyErector is
a toolkit/framework, like Make and Ant, giving you routines to set up
what you want/need to do.  It is geared more toward Python usage, but
most tasks are generic enough for any system.

The developer would create a driver file, commonly named 'pyerect',
that would import the 'pyerector' module and call the PyErector routine.
The smallest driver file would be:
    from pyerector import *
    PyErector()

The PyErector main routine will scan the command-line arguments for
target names, if none are found, then it will call the default target.
Target references on the command-line are the same as the class, but
with the first character lowercase.  The command-line argument 'default'
would refer to the 'Default' Target class.

Command-line arguments must reference targets, not other objects, or
variable assignments.  Instead of referencing a Target, a command-line
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

As can be seen with the standard Copy task above, the most common usage
is to create instances within a target's class members, like 'tasks'.

The API allows the developer to extend or change what is being performed
during the build.  For example, in the product's "pyerect" program,
there is a Registration task, which changes the SubPyErector task:
    class Regression(SubPyErector):
        wdir = 'regression'
        proddir = os.path.realpath(os.path.join('build', distfile))
        if 'PYTHONPATH' in os.environ:
            paths = os.environ['PYTHONPATH'].split(os.pathsep)
            paths.append(proddir)
            env = {'PYTHONPATH': os.pathsep.join(paths)}
            del paths
        else:
            env = {'PYTHONPATH': proddir }

This does not change the task's flow, but it does set up certain defaults
which does change the behavior.
"""

from .path import Path
from .helper import normjoin, Exclusions
from .helper import display, warn, verbose, debug  # being deprecated
from .execute import Initialization

from .version import Version
from .main import PyErector, pymain
from .vcs import VCS
from .base import Sequential, Parallel
from .targets import Target, All, Build, Clean, Compile, Default, Dist, Help, \
                     Init, InitDirs, InitVCS, Packaging, Test, Testonly
from .iterators import FileSet, StaticIterator, FileIterator, FileList, \
                       DirList, FileMapper, BasenameMapper, MergeMapper, \
                       IdentityMapper, Uptodate
from .variables import FileVariable, V, Variable, VariableSet

import pyerector.tasks
del pyerector

# With the addition of pyerector.api, some of the lower-level objects, like
# Target, Sequential, etc. should be removed in the future
__all__ = [
    # base routines
    'Exclusions',
    'normjoin',
    'PyErector',
    'pymain',
    'Version',
    # remove 'Target' and 'Task' to move to pyerector.api
    'Target',
    'Task',
    'Sequential',
    'Parallel',
    'V',  # alias for VariableCache
    'FileVariable',
    'Variable',
    'VariableSet',
    'VCS',
    'Path',

    # tasks
    'Chmod',
    'Copy',
    'CopyTree',
    'Echo',
    'Egg',
    'EncodeVar',
    'HashGen',
    'Java',
    'Mkdir',
    'PyCompile',
    'Remove',
    'Scp',
    'Shebang',
    'Spawn',
    'Ssh',
    'SubPyErector',
    'Symlink',
    'Tar',
    'Tokenize',
    'Touch',
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
    'Testonly',

    # iterators
    'FileSet',
    'StaticIterator',
    'FileIterator',
    'FileList',
    'DirList',
    # mappers
    'FileMapper',
    'BasenameMapper',
    'IdentityMapper',
    'MergeMapper',
    'Uptodate',
]

Initialization.start()

# pylint: disable=wrong-import-position
from .tasks import Task
# pylint: disable=wrong-import-position
from .tasks import Chmod, Copy, CopyTree, Echo, Egg, EncodeVar, HashGen, \
                   Java, Mkdir, PyCompile, Remove, Scp, Shebang, Spawn, \
                   SubPyErector, Ssh, Symlink, Tar, Tokenize, Touch, \
                   Unittest, Untar, Unzip, Zip

