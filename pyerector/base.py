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
    exclude = ()

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
            #assert callable(value) or isinstance(value, tuple(lst)), text
            if not callable(value) and not isinstance(value, tuple(lst)):
                raise TypeError(value, text)
        else:
            #assert isinstance(value, typeval), text
            if not isinstance(value, typeval):
                raise TypeError(value, text)

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
            if self.uptodates:
                self.logger.debug('calling %s.uptodates()', self)
                if self.uptodates():
                    self.verbose('uptodate.')
                    return

            # call dependencies
            if self.dependencies:
                self.logger.debug('calling %s.dependencies()', self)
                self.dependencies()

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
sequences of files.
Examples:
 i = Iterator('src', 'test', pattern='*.py')
 j = Iterator('build', pattern='*.py', recurse=True)
 k = Iterator('conf', ['etc/build.properties', 'tmp/dummy'], i, j)
 tuple(k) == ('conf/foo.cfg', 'etc/build.properties', 'tmp/dummy', 'src/foo.py', 'test/testfoo.py',
              'build/foo.py', 'build/test/testfoo.py')

 i = Iterator('src', pattern='*.py', recurse=True)
 j = Iterator(i, pattern='test*')
 tuple(j) == ('src/test/testfoo.py',)
"""
    exclusion = Exclusions()

    def __init__(self, *path, **kwargs):
        super(Iterator, self).__init__(*path, **kwargs)
        self.pool = None
        self.curset = None
        exclude = self.get_kwarg('exclude',
                                 (Exclusions, set, str, tuple, list, type(None))
        )
        if isinstance(exclude, Exclusions):
            self.exclusion = exclude
        elif isinstance(exclude, (set, tuple, list)):
            self.exclusion = Exclusions(exclude)
        elif isinstance(exclude, str):
            self.exclusion = Exclusions((exclude,))

    def __call__(self):
        """Iterators and Mappers do not get called as Targets, Tasks and
Sequentials."""
        raise NotImplemented

    def __iter__(self):
        # this is a list so we can modify it later, if necessary
        self.pool = list(self.get_args('path'))
        self.curset = iter([])
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """Cycle through the curset, returning strings that would "match".
Matching strings are not in the exclusions, if a pattern is set, would
match the pattern, and if recursive and a directory.  If it is a directory,
then prepend the directory's contents to the pool (not the curset).
"""
        while True:
            try:
                candidate = next(self.curset)
            except StopIteration:
                #self.logger.debug('caught StopIteration on next()')
                self.getnextset()  # can raise StopIteration
                try:
                    candidate = next(self.curset)  # can raise StopIteration
                except TypeError:
                    exc = sys.exc_info()[1]
                    raise TypeError(self.curset, exc)
            if isinstance(candidate, tuple) and len(candidate) == 2:
                break
            if self.exclusion.match(candidate):
                continue
            if self.check_candidate(candidate):
                break
        return self.post_process_candidate(candidate)

    def getnextset(self):
        if not self.pool:
            self.logger.debug('nothing left')
            raise StopIteration
        item = self.pool[0]
        del self.pool[0]
        self.logger.debug('next item from pool is %s', repr(item))
        if isinstance(item, Iterator):
            self.curset = iter(item)
        elif isinstance(item, (tuple, list)):
            items = [self.adjust(i) for i in item]
            if items:
                self.curset = iter(reduce(lambda a, b: a+b, items))
            else:
                self.curset = iter(())
        elif isinstance(item, str):
            self.curset = iter(self.adjust(item))
        #self.logger.debug('curset = %s', repr(self.curset))

    def append(self, item):
        """Add an item to the end of the pool."""
        path = list(self.get_args('path'))
        if isinstance(item, (tuple, list)):
            path.extend(item)
        else:
            path.append(item)
        self.path = tuple(path)

    def _prepend(self, item):
        """Add a string or sequence to the beginning of the pool."""
        if isinstance(item, str):
            item = [item]
        self.pool[:0] = list(item)
        self.logger.debug('adding to pool: %s', repr(item))

    # text based
    def post_process_candidate(self, candidate):
        return candidate
    def adjust(self, candidate):
        return [candidate]
    def check_candidate(self, candidate):
        pattern = self.get_kwarg('pattern', str)
        if not pattern:
            return True
        elif fnmatch.fnmatchcase(candidate, pattern):
            return True
        else:
            return False


class Mapper(Iterator):
    """Maps source files to destination files, using a base path, destdir.
The mapper member is either a string or callable that will adjust the
basename; if None, then there is no adjustment.
The map() method can also adjust the basename.

An example of using a mapper would be:
    FileMapper(
        FileIterator('src', pattern='*.py'),
        destdir='build', mapper=lambda n: n+'c'
        destdir='build', mapper='%(name)sc'
    )
This would map each py file in src to a pyc file in build:
    src/base.py  ->  build/base.pyc
    src/main.py  ->  build/main.pyc
"""
    destdir = None
    mapper = None
    def __init__(self, *files, **kwargs):
        super(Mapper, self).__init__(*files, **kwargs)
        mapper = self.get_kwarg('mapper', (callable, str))
        if mapper is None:  # identity mapper
            self.mapper_func = lambda x: x
        elif callable(mapper):
            self.mapper_func = mapper
        elif isinstance(mapper, str):
            self.mapper_func = \
                lambda name, mapstr = mapper: mapstr % {'name': name}
        else:
            raise TypeError('map must be string or callable', mapper)

    def next(self):
        """Return the next item, with its mapped destination."""
        destdir = self.get_kwarg('destdir', str)
        if destdir is None:
            destdir = ''
        # do _not_ catch StopIteration
        item = super(Mapper, self).next()
        #self.logger.debug('super.next() = %s', item)
        if isinstance(item, tuple) and len(item) == 2:
            item, temp = item
            mapped = self.mapper_func(temp)
            del temp
        else:
            mapped = self.mapper_func(item)
        assert isinstance(mapped, str), "mapper must return a str"
        self.logger.debug('self.map(%s) = %s', mapped, self.map(mapped))
        mapped = self.map(mapped)
        assert isinstance(mapped, str), 'map() must return a str'
        result = normjoin(destdir, mapped)
        self.logger.debug('mapper yields (%s, %s)', item, result)
        return item, result

    def map(self, item):
        """Identity routine, one-to-one mapping."""
        return item

    def __call__(self, *args):
        for (src, dst) in self:
            if not self.checkpair(src, dst):
                break
        else:
            self.logger.debug('%s() => True', self)
            return True
        self.logger.debug('%s() => False', self)
        return False

    def uptodate(self):
        """For each src,dst pair, check the modification times.  If the
dst is newer, then return True.
"""
        return self()  # run __call__

    def checkpair(self, src, dst):
        """To be overridden."""
        self.logger.debug('%s.checkpair(%s, %s)', self, src, dst)
        return False

    def checktree(self, src, dst):
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

    def __len__(self):
        return len(self.get_args('items'))

    def __bool__(self):
        return len(self) > 0
    __nonzero__ = __bool__

    @staticmethod
    def retrieve(name):
        """Retrieve an instance.  If an instance of a Variable, return None.
If a subclass of Initer, then return an instance of the subclass.
If an instance of Inter, return the object.
If a string (has 'lower' attribute), then find in registry and return an
instance.
Otherwise log an exception and raise Abort error.
"""
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
        """Generate the appropriate exception message."""
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
            if isinstance(obj, Mapper):
                abortive = True
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

