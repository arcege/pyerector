#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from . import hasformat, display, verbose
from .register import registry
from .base import Target
from .tasks import Mkdir, Remove, Unittest
from .iterators import StaticIterator
from .variables import V

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
    'Packaging',
    'Test',

]
# standard targets

class Help(Target):
    """This information"""
    def run(self):
        for name, obj in sorted(registry.get('Target').items()):
            if name[1:].lower() != name[1:]:
                continue  # ignore non-callable targets
            # use display.write to get around --quiet option
            if hasformat:
                display.write('{0:20}  {1}'.format(
                        obj.__name__.lower(),
                        obj.__doc__ or ""
                    )
                )
            else:
                display.write(
                    '%-20s  %s' % (obj.__name__.lower(), obj.__doc__ or "")
                )
        for var in V:
            if hasformat:
                verbose('var {} = "{}"'.format(var.name, var.value))
            else:
                verbose('var %s = "%s"' % (var.name, var.value))
class Clean(Target):
    """Clean directories and files used by the build"""
    files = ()
    def run(self):
        Remove()(*self.files)
class InitDirs(Target):
    """Create initial directories"""
    files = ()
    def run(self):
        Mkdir()(StaticIterator(self.files))
class Init(Target):
    """Initialize the build."""
    dependencies = (InitDirs,)
class Compile(Target):
    """Compile source files."""
    # meant to be overriden
class Build(Target):
    """The primary build."""
    dependencies = (Init, Compile)
class Packaging(Target):
    """Package for distribution."""
    # meant to be overriden
class Dist(Target):
    """The primary packaging."""
    dependencies = (Build, Packaging)
    # may be overriden
class Test(Target):
    """Run (unit)tests."""
    dependencies = (Build,)
    tasks = (Unittest,)
# default target
class All(Target):
    """Do it all"""
    dependencies = (Clean, Dist, Test)
class Default(Target):
    """When no target is specified."""
    dependencies = (Dist,)


