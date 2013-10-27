#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.
"""Define the primary constructs for use within the package; namely
Initer (base class), Target, Task, Iterator, Mapper, Sequential, Parallel.

Iterator and Mapper have most of their logic defined in iterators.
"""

import logging
import os
from sys import version
import threading
try:
    reduce
except NameError:
    from functools import reduce
if version[0] > '2':  # python 3+
    from .py3.base import Base
else:
    from .py2.base import Base
from .helper import Exclusions, normjoin, Timer
from .execute import get_current_stack, PyThread
from .register import registry
from .exception import Abort, Error
from .config import Config, noop, noTimer
from .variables import V, Variable

__all__ = [
    'Target', 'Task', 'Sequential', 'Parallel',
]

# the base class to set up the others


class Initer(Base):
    """Primary base class for everything.  This is responsible for
establishing the common framework for the API, including argument
handling.
"""
    config = Config()  # for backward compatibility only
    # values to propagate to an iterator
    pattern = None
    noglob = False
    recurse = False
    fileonly = True
    exclude = None

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger('pyerector.execute')
        self.logger.debug('%s.__init__(*%s, **%s)',
                          self.__class__.__name__, args, kwargs)
        try:
            basedir = kwargs['basedir']
        except KeyError:
            basedir = None
        else:
            del kwargs['basedir']
        try:
            curdir = kwargs['curdir']
        except KeyError:
            curdir = os.curdir
        else:
            del kwargs['curdir']
        if args:
            self.args = args
        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])
        if basedir is not None:
            V['basedir'] = basedir or curdir

    def get_files(self, files=None):
        """Return an Iterator of either a given sequence or the "files"
member.  Iterator attributes define in the class will be propagated to
the Iterator instance.
"""
        # propagate 'noglob' keyword to the interator
        noglob = self.get_kwarg('noglob', bool)
        recurse = self.get_kwarg('recurse', bool)
        fileonly = self.get_kwarg('fileonly', bool)
        pattern = self.get_kwarg('pattern', str)
        exclude = self.get_kwarg('exclude', (Exclusions, tuple))
        if files is None:
            try:
                files = getattr(self, 'files')
            except AttributeError:
                files = ()
        if isinstance(files, Iterator):
            return files
        else:
            # import here to avoid recursive references
            from .iterators import FileIterator
            fset = FileIterator(noglob=noglob, recurse=recurse,
                                fileonly=fileonly, pattern=pattern,
                                exclude=exclude)
            for entry in files:
                fset.append(entry)
            return fset

    def join(self, *path):
        """Normjoin the basedir and the path."""
        self.logger.debug('%s.join(%s, *%s)',
                          self.__class__.__name__, V['basedir'], path)
        return normjoin(V['basedir'], *path)

    def asserttype(self, value, typeval, valname):
        """Assert that the value is a value type."""
        if isinstance(typeval, type):
            typename = typeval.__name__
        else:
            typename = ' or '.join(t.__name__ for t in typeval)
        text = "Must supply %s to '%s' in '%s'" % (
            typename, valname, self.__class__.__name__
        )
        if isinstance(typeval, (tuple, list)) and callable in typeval:
            lst = list(typeval)[:]
            lst.remove(callable)
            assert callable(value) or isinstance(value, tuple(lst)), text
        else:
            assert isinstance(value, typeval), text

    def get_kwarg(self, name, typeval, noNone=False):
        """Return a item in saved kwargs or an attribute of the name name.
If noNone, then raise ValueError if the value is None.
"""
        if hasattr(self, 'kwargs') and name in getattr(self, 'kwargs'):
            value = getattr(self, 'kwargs')[name]
        else:
            value = getattr(self, name)
        if noNone or value is not None:
            self.asserttype(value, typeval, name)
        elif noNone and value is None:
            raise ValueError("no '%s' for '%s'" %
                             (name, self.__class__.__name__))
        return value

    def get_args(self, name):
        """Return the saved argument list or an attribute of the name."""
        if hasattr(self, 'args') and getattr(self, 'args'):
            value = getattr(self, 'args')
        elif hasattr(self, name) and getattr(self, name):
            value = getattr(self, name)
        else:
            return ()
        self.asserttype(value, (tuple, list, Iterator), name)
        return value

    @classmethod
    def validate_tree(cls):
        """To be overridden in subclasses."""
        pass  # do nothing, Target will do something with this

    def display(self, msg, *args, **kwargs):
        """Display a message at the DISPLAY log level, which should
be above the level that the --quiet option would set."""
        from logging import getLevelName
        self.logger.log(getLevelName('DISPLAY'), msg, *args, **kwargs)


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
            return not self.allow_reexec and self.__class__._been_called

    @been_called.setter
    def been_called(self, value):
        """Set if the Target has been called."""
        with self._been_called_lock:  # class member
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
            # call uptodates
            if self.uptodates():
                self.verbose('uptodate.')
                return

            # call dependencies
            self.dependencies()

            # call tasks, and run()
            with timer:
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
            if noTimer:
                self.verbose('done.')
            else:
                self.verbose('done. (%0.3f)' % timer)
            self.been_called = True
        finally:
            stack.pop()

    def run(self):
        """To be overridden."""

    def verbose(self, *args):
        """Display the class name with the message."""
        msg = '%s: %s' % (str(self), ' '.join(str(s) for s in args))
        self.logger.warning(msg)


# Tasks
class Task(Initer):
    """A representation of a unit of work.  Generally performs Python code
directly, either as one of the standard tasks or through the API.  The
run() method is meant to be overridden.
"""
    args = []

    def __str__(self):
        return self.__class__.__name__

    def __call__(self, *args, **kwargs):
        myname = self.__class__.__name__
        self.logger.debug('%s.__call__(*%s, **%s)', myname, args, kwargs)
        stack = get_current_stack()
        stack.push(self)  # push me onto the execution stack
        try:
            self.handle_args(args, kwargs)
            if noop:
                self.logger.warning('Calling %s(*%s, **%s)',
                                    myname, args, kwargs)
                return
            try:
                returncode = self.run()
            except (KeyError, ValueError, TypeError,
                    RuntimeError, AttributeError):
                raise
            except Abort:
                raise  # reraise
            except Error:
                self.logger.exception('Exception in %s.run', myname)
                raise Abort
            except Exception:
                logging.getLogger('pyerector').exception('Exception')
                raise Abort
        finally:
            stack.pop()
        if returncode:
            raise Error(str(self), 'return error = %s' % returncode)
        else:
            self.logger.info('%s: done.', myname)

    def run(self):
        """To be overridden."""

    def handle_args(self, args, kwargs):
        """"Put the arguments into their proper places."""
        if (hasattr(self, 'args') and not self.args) or args:
            if len(args) == 1 and isinstance(args[0], Iterator):
                self.args = args[0]
            else:
                self.args = tuple(args)
        if kwargs:
            self.kwargs = dict(kwargs)


class Iterator(Initer):
    """The base class for Iterators and Mappers.  Processes arguments as
sequences of files."""
    def __init__(self, *path, **kwargs):
        super(Iterator, self).__init__(*path, **kwargs)
        exclude = self.get_kwarg('exclude',
                                 (Exclusions, set, str, tuple, list, type(None))
        )
        self.exclusion = Exclusions(exclude)

    def __iter__(self):
        return self

    def next(self):
        """To be overridden."""
        raise StopIteration


class Mapper(Iterator):
    """The base class for Mappers."""
    def __call__(self):
        """To be overridden."""

    def uptodate(self):
        """To be overridden."""
        return False


class Sequential(Initer):
    """Class to sequentially call Target or Task instances."""
    items = ()

    def __repr__(self):
        name = self.__class__.__name__[:1]
        return '%s%s' % (name, self.get_args('items'))

    def __iter__(self):
        return iter(self.get_args('items'))

    def __bool__(self):
        return len(self.get_args('items')) > 0
    __nonzero__ = __bool__

    @staticmethod
    def retrieve(name):
        if isinstance(name, Variable):
            return None
        elif isinstance(name, type) and issubclass(name, Initer):
            obj = name()
        elif isinstance(name, Initer):
            obj = name
        elif hasattr(name, 'lower'):
            try:
                kobj = registry[name]
            except (KeyError, AssertionError):
                logging.getLogger('pyerector').exception(
                        'Cannot find %s', name
                )
                raise Abort
            else:
                obj = kobj()
        else:
            logging.getLogger('pyerector.execute').exception(
                    'could not retrieve %s', name
            )
            raise Abort
        return obj


    @staticmethod
    def get_exception_message(obj, parent):
        if isinstance(obj, Target):
            return 'Exception in %s.dependencies: %s' % (parent, obj)
        elif isinstance(obj, Task):
            return 'Exception in %s.tasks: %s' % (parent, obj)
        elif isinstance(obj, Mapper):
            return 'Exception in %s.uptodates: %s' % (parent, obj)
        else:
            return None

    def __call__(self, *args):
        """Call the items in the list."""
        parent = get_current_stack()[-1]
        abortive = False
        for item in self:
            obj = self.retrieve(item)
            self.logger.debug('Calling %s' % obj)
            if obj is None:  # do not process Variable instances
                continue
            excmsg = self.get_exception_message(obj, parent)
            try:
                result = obj(*args)
            except Error:
                self.logger.exception(excmsg)
                raise Abort
            else:
                if abortive and not result:
                    return False
        else:
            if abortive:
                return True
            else:  # this is just being explicit
                return


class Parallel(Sequential):
    """Class to concurrently call Target or Task instances."""
    def __call__(self, *args):
        """Call the items in the list, in separate threads."""
        parent = get_current_stack()[-1]
        bname = '%s.' % parent
        threads = []
        for item in self:
            obj = self.retrieve(item)
            if obj is None:  # do not process Variable instances
                continue
            exgmsg = self.get_exception_message(obj, parent)
            thread = PyThread(
                name=bname + str(obj),
                target=obj,
            )
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for thread in threads:
            if thread.exception:
                raise Abort
        del threads

