#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .helper import normjoin, Verbose, Exclusions

# must define 'verbose', 'noop' and 'debug' before importing other submodules

display = Verbose(True)  # always emit
warn = Verbose(True) # always emit (unless --quiet)
verbose = Verbose()
noop = Verbose()
from os import environ
debug = Verbose('DEBUG' in environ and environ['DEBUG'] != '')
del environ

# display timing information, changed in pyerector.main.PyErector
noTimer = False

from .version import *
from .main import PyErector, pymain
from .base import Target, Task
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
    'V',  # alias for Variable
    'Variable',
    'VariableSet',
    'VCS',

    # tasks
    'Chmod',
    'Copy',
    'CopyTree',
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

