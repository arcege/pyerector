#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from . import hasformat, display
from .register import registry
from .base import Target
from .tasks import Mkdir, Remove, Unittest
from .iterators import StaticIterator

__all__ =  [
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
Dependencies: None
Members: None
Methods: None
"""
    def run(self):
        def firstline(s):
            try:
                p = s.index('\n')
            except ValueError:
                return s
            else:
                return s[:p]
        for name, obj in sorted(registry.get('Target').items()):
            # use display.write to get around --quiet option
            if name[1:].lower() != name[1:]:
                continue
            if hasformat:
                display.write('{0:20}  {1}'.format(
                        obj.__name__.lower(),
                        firstline(obj.__doc__ or "")
                    )
                )
            else:
                display.write(
                    '%-20s  %s' % (obj.__name__.lower(), obj.__doc__ or "")
                )
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
        Remove()(*self.files)
class InitVCS(Target):
    """Initialize information about the version control system, VCS.
The VCS instance is stored as a global Variable.
Tasks: None
Dependencies: None
Members: None
Methods: None
"""
    def run(self):
        from . import verbose, VCS, Variable
        from .helper import Verbose
        lclverbose = Verbose(verbose, prefix='InitVCS')
        try:
            v = VCS()
        except RuntimeError:
            lclverbose('No VCS found')
        else:
            v.current_info()
            Variable('pyerector.vcs', v)
            lclverbose('Found', v)
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


