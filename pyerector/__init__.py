#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .helper import normjoin, Verbose, Exclusions
from .version import get_version

# Future Py3000 work prevents the use of string formatting using '%'
# trying to use both string formatting and ''.format is UGLY!!!!
# A LOT of the code may be using the less efficient string
# concatentation which is supported across both sets of releases.
try:
    ''.format
except AttributeError:
    hasformat = False
else:
    hasformat = True

# must define 'verbose', 'noop' and 'debug' before importing other submodules

warn = Verbose(True) # always emit
verbose = Verbose()
noop = Verbose()
from os import environ
debug = Verbose('DEBUG' in environ and environ['DEBUG'] != '')
del environ

# display timing information, changed in pyerector.main.PyErector
noTimer = False

from .main import PyErector, pymain
from .base import Target, Task
from .tasks import  *
from .targets import *
from .iterators import *
from .variables import *
from .vcs import *
V = Variable  # an alias for exporting to clients, internally use 'Variable'

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
    'HashGen',
    'Java',
    'Mkdir',
    'PyCompile',
    'Remove',
    'Shebang',
    'Spawn',
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

