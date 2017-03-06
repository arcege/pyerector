#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.
"""Define the standard targets."""

import logging
import threading

from .exception import Error, Abort
from .helper import Timer
from .register import registry
from .execute import get_current_stack
from .base import Initer, Sequential, Parallel
from .iterators import Iterator, StaticIterator
from .variables import V, Variable

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


class Target(Initer):
    """A representation of an element of "organization".  There are
three primary members and a method to be overridden:
    uptodates - a Mapper instance to check if the target should be started.
    dependencies - sequence of Targets (or Variable instances) to be called
before tasks or the run() method.
    tasks - sequence of Tasks (or Variable instances) to be called before
the run() method.
    run() - perform Python code.
A timer tracks how long the tasks and run() method take.
Exceptions raised:
There are two primary exceptions, Abort and code-base (KeyError, etc.).  The
abort is captured by PyErector.run(), but other exceptions are handled as
normal (using getLogger('pyerector').exception()).
"""
    dependencies = ()
    uptodates = ()
    tasks = ()
    # if True, then 'been_called' always returns False, allowing for
    # reexecution
    allow_reexec = False
    # if True, then 'been_called' returns True, preventing
    # reexecution
    _been_called = False
    _been_called_lock = threading.RLock()

    @property
    def been_called(self):
        """Return if the Target has been called already."""
        with self._been_called_lock:  # class member
            # pylint: disable=protected-access
            return not self.allow_reexec and self.__class__._been_called

    @been_called.setter
    def been_called(self, value):
        """Set if the Target has been called."""
        with self._been_called_lock:  # class member
            # pylint: disable=protected-access
            self.__class__._been_called = value

    def __str__(self):
        return self.__class__.__name__

    @classmethod
    def validate_tree(cls):
        """Recursively validate the contents of 'dependencies' (Target),
'uptodates' (Mapper) and 'tasks' (Task). Also allowable are Variable
instances."""
        def validate_class(kobj, kset, ktype, ktname):
            """Validate that the object is the correct type."""
            klassobj = registry[ktype]
            klasses = registry.get(ktype)
            for name in kset:
                if isinstance(name, Variable):
                    # variables are valid, but we don't do anything with them
                    continue
                if ktype == 'Mapper' and isinstance(name, klassobj):
                    # special case, allow direct instance of Uptodate
                    obj = name
                elif isinstance(name, Sequential):
                    validate_class(klassobj.__name__, name, ktype, ktname)
                    continue
                elif isinstance(name, str) and name in klasses:
                    obj = klasses[name]
                elif isinstance(name, type) and issubclass(name, klassobj):
                    obj = klasses[name.__name__]
                elif isinstance(name, klassobj):
                    obj = klasses[name.__class__.__name__]
                else:
                    raise ValueError(
                        '%s: invalid %s: %s' % (kobj, ktname, name)
                    )
                if hasattr(obj, 'validate_tree'):
                    obj.validate_tree()
        validate_class(cls.__name__, cls.dependencies, 'Target', 'dependency')
        validate_class(cls.__name__, cls.uptodates, 'Mapper', 'uptodate')
        validate_class(cls.__name__, cls.tasks, 'Task', 'task')

    def member_cast(self):
        """Cast each member as Sequential."""

        if not isinstance(self.dependencies, Sequential):
            self.dependencies = Sequential(*self.dependencies)
        if not isinstance(self.uptodates, Sequential):
            self.uptodates = Sequential(*self.uptodates)
        elif isinstance(self.uptodates, Parallel):
            raise ValueError('uptodates cannot be Parallel')
        if not isinstance(self.tasks, Sequential):
            self.tasks = Sequential(*self.tasks)
        assert isinstance(self.uptodates, Sequential) and \
            not isinstance(self.uptodates, Parallel)
        assert isinstance(self.dependencies, Sequential)
        assert isinstance(self.tasks, Sequential)

    def __call__(self, *args):
        """Call the chain: uptodates, dependencies, tasks, run()."""
        myname = self.__class__.__name__
        self.logger.debug('%s.__call__(*%s)', myname, args)
        timer = Timer()
        if self.been_called:
            return
        self.member_cast()
        stack = get_current_stack()
        stack.push(self)  # push me onto the execution stack
        try:
            if self.call_uptodates():
                self.verbose('uptodate.')
                return

            self.call_dependencies()

            # call tasks, and run()
            with timer:
                if self.tasks:
                    self.logger.debug('calling %s.tasks()', self)
                    self.tasks()

                try:
                    self.logger.debug('starting %s.run', myname)
                    self.run()
                except (KeyError, ValueError, TypeError,
                        RuntimeError, AttributeError):
                    raise  # reraise
                except Abort:
                    raise  # reraise
                except Error:
                    self.logger.exception('Exception in %s.run', myname)
                    raise Abort
                except Exception:
                    logging.getLogger('pyerector').exception('Exception')
                    raise Abort
            if V['pyerector.notimer']:
                self.verbose('done.')
            else:
                self.verbose('done. (%0.3f)' % timer)
            self.been_called = True
        finally:
            stack.pop()

    def call_uptodates(self):
        """Run through the uptodates entries."""
        if self.uptodates:
            self.logger.debug('calling %s.uptodates()', self)
            return self.uptodates()
        return False

    def call_dependencies(self):
        """Run through the dependencies."""
        if self.dependencies:
            self.logger.debug('calling %s.dependencies()', self)
            self.dependencies()

    def run(self):
        """To be overridden."""

    def verbose(self, *args):
        """Display the class name with the message."""
        msg = '%s: %s' % (str(self), ' '.join(str(s) for s in args))
        self.logger.warning(msg)


# standard targets


class Help(Target):
    """This information.
Tasks: internal
Dependencies: None
Members: None
Methods: None
"""

    def run(self):
        """Display callable targets with the first line of their
docstrings.  If --verbose, then also show the contents of the
VariableCache."""
        def firstline(string):
            """Return only up to the first newline."""
            try:
                pos = string.index('\n')
            except (AttributeError, ValueError, IndexError):
                return string or ''
            else:
                return string[:pos]
        for name, obj in sorted(registry.get('Target').items()):
            if name[1:].lower() != name[1:]:
                continue  # ignore non-callable targets
            self.display(
                '%-20s  %s' % (obj.__name__.lower(),
                               firstline(obj.__doc__))
            )
        for var in sorted(V):
            self.logger.info('var %s = "%s"', var.name, var.value)


# pylint: disable=too-few-public-methods
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
        from .tasks import Remove
        from .iterators import DirList
        files = self.get_args('files')
        if isinstance(files, Iterator):
            pass
        elif isinstance(files, (list, tuple)) and \
                len(files) == 1 and isinstance(files[0], Iterator):
            files = files[0]
        elif isinstance(files, (list, tuple)):
            files = DirList(*tuple(files))
        assert isinstance(files, Iterator)
        Remove()(files)


class InitVCS(Target):
    """Initialize information about the version control system, VCS.
The VCS instance is stored as a global Variable.
Tasks: None
Dependencies: None
Members: None
Methods: None
This functionality should now be handled by pyerector.vcs.__init__.InitVCS
before pyerector finishes being imported.
"""
    def run(self):
        self.logger.warning('Target %s has been deprecated.', self)


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
        from .tasks import Mkdir
        Mkdir()(StaticIterator(self.files))


class Init(Target):
    """Initialize the build.
Tasks: None
Dependencies: InitDirs
Members: None
Methods: None
"""
    dependencies = (InitDirs,)


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


class Testonly(Target):
    """Run unittest, without dependencies.
Tasks: None
Dependencies: None
Members: None
Methods: None
"""

class Test(Target):
    """Run (unit)tests.
Tasks: None
Dependencies: Build, Testonly
Members: None
Methods: None
"""
    dependencies = (Build, Testonly)


class All(Target):
    """Do it all.
Tasks. None
Dependencies: (Clean, Dist, Test)
Members: None
Methods: None
"""
    dependencies = (Clean, Dist, Test)


# default target

class Default(Target):
    """When no target is specified.
Tasks: None
Dependencies: Dist
Members: None
Methods: None
"""
    dependencies = (Dist,)
