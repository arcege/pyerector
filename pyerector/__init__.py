#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .helper import normjoin, Exclusions, init_logging
from .helper import display, warn, verbose, debug # being deprecated
from .execute import init_threading

from .version import *
from .main import PyErector, pymain, init_main
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

# initialize, but remove the references afterward
init_logging()
init_threading()
init_main()
del init_logging, init_threading, init_main
