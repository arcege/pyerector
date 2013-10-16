#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

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
from .helper import Exclusions, normjoin, Timer, u
from .execute import get_current_stack, PyThread
from .register import registry
from .exception import Abort, Error
from .config import Config, noop, noTimer
from .variables import V

__all__ = [
    'Target', 'Task', 'Sequential', 'Parallel',
]

# the base class to set up the others


class Initer(Base):
    config = Config()  # for backward compatibility only
    noglob = False
    iterator = None

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger('pyerector.execute')
        self.logger.debug('%s.__init__(*%s, **%s)', self.__class__.__name__, args, kwargs)
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
        # propagate 'noglob' keyword to the interator
        noglob = self.get_kwarg('noglob', bool)
        if files is None:
            try:
                files = self.files
            except AttributeError:
                files = ()
        if isinstance(files, Iterator):
            return files
        else:
            # import here to avoid recursive references
            from .iterators import FileIterator, FileSet
            fs = FileSet()
            for entry in files:
                if isinstance(entry, Iterator):
                    i = entry
                elif isinstance(entry, (tuple, list)):
                    i = FileIterator(entry, noglob=noglob)
                else:
                    i = FileIterator((entry,), noglob=noglob)
                fs.append(i)
            return fs

    def join(self, *path):
        self.logger.debug('%s.join(%s, *%s)', self.__class__.__name__, V['basedir'], path)
        return normjoin(V['basedir'], *path)

    def asserttype(self, value, typeval, valname):
        if isinstance(typeval, type):
            typename = typeval.__name__
        else:
            typename = ' or '.join(t.__name__ for t in typeval)
        text = "Must supply %s to '%s' in '%s'" % (
            typename, valname, self.__class__.__name__
        )
        if isinstance(typeval, (tuple, list)) and callable in typeval:
            l = list(typeval)[:]
            l.remove(callable)
            assert callable(value) or isinstance(value, tuple(l)), text
        else:
            assert isinstance(value, typeval), text

    def get_kwarg(self, name, typeval, noNone=False):
        if hasattr(self, 'kwargs') and name in self.kwargs:
            value = self.kwargs[name]
        else:
            value = getattr(self, name)
        if noNone or value is not None:
            self.asserttype(value, typeval, name)
        elif noNone and value is None:
            raise ValueError("no '%s' for '%s'" %
                             (name, self.__class__.__name__))
        return value

    def get_args(self, name):
        if hasattr(self, 'args') and self.args:
            value = self.args
        elif hasattr(self, name) and getattr(self, name):
            value = getattr(self, name)
        else:
            return ()
        self.asserttype(value, (tuple, list, Iterator), name)
        return value

    @classmethod
    def validate_tree(cls):
        pass  # do nothing, Target will do something with this

    def display(self, msg, *args, **kwargs):
        from logging import getLevelName
        self.logger.log(getLevelName('DISPLAY'), msg, *args, **kwargs)


class Target(Initer):
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

    def get_been_called(self):
        with self._been_called_lock:  # class member
            return not self.allow_reexec and self.__class__._been_called

    def set_been_called(self, value):
        with self._been_called_lock:  # class member
            self.__class__._been_called = value
    been_called = property(get_been_called, set_been_called)

    def __str__(self):
        return self.__class__.__name__

    @classmethod
    def validate_tree(cls):
        def validate_class(kobj, kset, ktype, ktname):
            klassobj = registry[ktype]
            klasses = registry.get(ktype)
            for name in kset:
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

    def call(self, name, args=()):
        # find the object
        if isinstance(name, type) and issubclass(name, Initer):
            obj = name()
        elif isinstance(name, Initer):
            obj = name
        else:
            try:
                kobj = registry[name]
            except (KeyError, AssertionError):
                logging.getLogger('pyerector').exception('Cannot find %s', name)
                raise Abort
            else:
                obj = kobj()
        # now perform the operation
        from .iterators import Uptodate
        if not isinstance(obj, Uptodate) and isinstance(obj, Mapper):
            return obj.uptodate()
        else:
            return obj(*args)

    def __call__(self, *args):
        myname = self.__class__.__name__
        self.logger.debug('%s.__call__(*%s)', myname, args)
        timer = Timer()
        if self.been_called:
            return
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
        stack = get_current_stack()
        stack.push(self)  # push me onto the execution stack
        try:
            # call uptodates
            if self.uptodates.check(self, Mapper, 'uptodate',
                                    'Exception in %s.uptodates' % myname):
                self.verbose('uptodate.')
                return

            # call dependencies
            self.dependencies.run(self, Target, 'dependencies',
                                  'Exception in %s.dependencies' % myname)

            # call tasks, and run()
            with timer:
                self.tasks.run(self, Task, 'tasks',
                               'Exception in %s.tasks' % myname)

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
        pass

    def verbose(self, *args):
        msg = u('%s: %s' % (str(self), ' '.join(str(s) for s in args)))
        self.logger.warning(msg)


# Tasks
class Task(Initer):
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
                self.logger.warning('Calling %s(*%s, **%s)', myname, args, kwargs)
                return
            try:
                rc = self.run()
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
        if rc:
            raise Error(str(self), 'return error = %s' % rc)
        else:
            self.logger.info('%s: done.', myname)

    def run(self):
        pass

    def handle_args(self, args, kwargs):
        if (hasattr(self, 'args') and not self.args) or args:
            self.args = list(args)
        if kwargs:
            self.kwargs = dict(kwargs)


class Iterator(Initer):
    def __init__(self, *path, **kwargs):
        super(Iterator, self).__init__(*path, **kwargs)
        exclude = self.get_kwarg('exclude',
                                 (Exclusions, set, str, tuple, list, type(None))
        )
        self.exclusion = Exclusions(exclude)

    def __iter__(self):
        return self

    def next(self):
        raise StopIteration


class Mapper(Iterator):
    def uptodate(self):
        return False


class Sequential(Initer):
    items = ()

    def __repr__(self):
        name = self.__class__.__name__[:1]
        return '%s%s' % (name, self.get_args('items'))

    def __iter__(self):
        return iter(self.get_args('items'))

    def __bool__(self):
        return len(self.get_args('items')) > 0
    __nonzero__ = __bool__

    def run(self, caller, itype, iname, excmsg):
        for item in self:
            try:
                caller.call(item)
            except Error:
                self.logger.exception(excmsg)
                raise Abort

    def check(self, caller, itype, iname, excmsg):
        """Used for uptodates which care about the return value."""
        if self:
            for item in self:
                try:
                    if not caller.call(item):
                        break
                except Error:
                    self.logger.exception(excmsg)
                    raise Abort
            else:
                return True
        return False


class Parallel(Sequential):
    def run(self, caller, itype, iname, excmsg):
        last_stack_item = get_current_stack()[-1]
        bname = '%s.' % last_stack_item.__class__.__name__
        threads = []
        for item in self:
            if isinstance(item, Initer):
                name = item.__class__.__name__
            elif isinstance(item, type(Initer)) and issubclass(item, Initer):
                name = item.__name__
            else:
                name = str(item)
            t = PyThread(
                name=bname + name,
                target=caller.call,
                args=(item,)
            )
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        for t in threads:
            if t.exception:
                raise Abort
        del threads
