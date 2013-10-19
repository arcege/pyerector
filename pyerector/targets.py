#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Define the standard targets."""

from .register import registry
from .base import Target
from .tasks import Mkdir, Remove, Unittest
from .iterators import StaticIterator
from .variables import V
from .vcs import VCS

__all__ = [
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

]
# standard targets


class Help(Target):
    """This information.
Tasks: internal
Dependencies: InitVCS
Members: None
Methods: None
"""
    dependencies = ('InitVCS',)

    def run(self):
        """Display callable targets with the first line of their
docstrings.  If --verbose, then also show the contents of the
VariableCache."""
        def firstline(string):
            """Return only up to the first newline."""
            try:
                pos = string.index('\n')
            except ValueError:
                return string
            else:
                return string[:pos]
        for name, obj in sorted(registry.get('Target').items()):
            if name[1:].lower() != name[1:]:
                continue  # ignore non-callable targets
            self.display(
                '%-20s  %s' % (obj.__name__.lower(),
                               firstline(obj.__doc__) or "")
            )
        for var in sorted(V):
            self.logger.info('var %s = "%s"' % (var.name, var.value))


class Clean(Target):
    """Clean directories and files used by the build.
Tasks: internal [Remove(files)]
Dependencies: None
Members:
  files = ()
Methods: None
"""
    files = ()

    def run(self):
        from .iterators import DirList
        Remove()(DirList(self.get_args('files')))


class InitVCS(Target):
    """Initialize information about the version control system, VCS.
The VCS instance is stored as a global Variable.
Tasks: None
Dependencies: None
Members: None
Methods: None
"""
    def run(self):
        try:
            vcs = VCS()
        except RuntimeError:
            self.logger.info('No VCS found')
        else:
            vcs.current_info()
            V['pyerector.vcs'] = vcs
            self.logger.info('Found %s', vcs)


class InitDirs(Target):
    """Create initial directories.
Tasks: internal [Mkdir(files)]
Dependencies: None
Members:
    files = ()
Methods: None
"""
    files = ()

    def run(self):
        Mkdir()(StaticIterator(self.files))


class Init(Target):
    """Initialize the build.
Tasks: None
Dependencies: InitDirs, InitVCS
Members: None
Methods: None
"""
    dependencies = (InitDirs, InitVCS)


class Compile(Target):
    """Compile source files.
Tasks: None
Dependencies: None
Members: None
Methods: None
"""
    # meant to be overriden


class Build(Target):
    """The primary build.
Tasks: None
Dependencies: (Init, Compile)
Members: None
Methods: None
"""
    dependencies = (Init, Compile)


class Packaging(Target):
    """Package for distribution.
Tasks: None
Dependencies: None
Members: None
Methods: None
"""
    # meant to be overriden


class Dist(Target):
    """The primary packaging.
Tasks: None
Dependencies: (Build, Packaging)
Members: None
Methods: None
"""
    dependencies = (Build, Packaging)
    # may be overriden


class Test(Target):
    """Run (unit)tests.
Tasks: Unittest
Dependencies: Build
Members: None
Methods: None
"""
    dependencies = (Build,)
    tasks = (Unittest,)
# default target


class All(Target):
    """Do it all.
Tasks. None
Dependencies: (Clean, Dist, Test)
Members: None
Methods: None
"""
    dependencies = (Clean, Dist, Test)


class Default(Target):
    """When no target is specified.
Tasks: None
Dependencies: Dist
Members: None
Methods: None
"""
    dependencies = (Dist,)
