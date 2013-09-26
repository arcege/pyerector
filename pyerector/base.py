#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import logging
import os
from sys import version
try:
    reduce
except NameError:
    from functools import reduce
if version[0] > '2': # python 3+
    from .py3.base import Base
else:
    from .py2.base import Base
from . import noop
from .helper import normjoin, u, Timer, extract_stack
from .register import registry
from .exception import Abort, Error
from .config import Config
from .variables import V

__all__ = [
    'Target', 'Task',
]

class ExecStack(object):
    def __init__(self):
        self.stack = []
        self.pos = None
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.stack)
    def push(self, frame):
        self.stack.append(frame)
    def pop(self):
        return self.stack.pop()
    def __len__(self):
        return len(self.stack)
    def __iter__(self):
        self.pos = 0
        return self
    def next(self):
        if self.pos >= len(self):
            raise StopIteration
        item = self.stack[self.pos]
        self.pos += 1
        return item
    def extract(self):
        lines = []
        indent = 0
        for item in self:
            lines.append('%s%s\n' % ('  ' * indent, item.__class__.__name__))
            indent += 1
        return lines

stack = ExecStack()

# the base class to set up the others
class Initer(Base):
    config = Config()  # for backward compatibility only
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
    def wantnoglob(self):
        return ((hasattr(self, 'kwargs') and 'noglob' in  self.kwargs and
                    self.kwargs['noglob']) or
                (hasattr(self, 'noglob') and self.noglob))
    def get_files(self, files=None):
        if files is None:
            try:
                files = self.files
            except AttributeError:
                files = ()
        if isinstance(files, Iterator):
            return files
        else:
            # import here to avoid recursive references
            from .iterators import StaticIterator, FileIterator, FileSet
            if self.wantnoglob():
                iterator = StaticIterator
            else:
                iterator = FileIterator
            fs = FileSet()
            for entry in files:
                if isinstance(entry, Iterator):
                    i = entry
                elif isinstance(entry, (tuple, list)):
                    i = iterator(entry)
                else:
                    i = iterator((entry,),)
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
            assert callable(value) or isinstance(value, l), text
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
    def validate_tree(self):
        pass # do nothing, Target will do something with this

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
    def get_been_called(self):
        return not self.allow_reexec and self.__class__._been_called
    def set_been_called(self, value):
        self.__class__._been_called = value
    been_called = property(get_been_called, set_been_called)
    def __str__(self):
        return self.__class__.__name__
    @classmethod
    def validate_tree(klass):
        def validate_class(kobj, kset, ktype, ktname):
            klass = registry[ktype]
            klasses = registry.get(ktype)
            for name in kset:
                if ktype == 'Mapper' and isinstance(name, klass):
                    # special case, allow direct instance of Uptodate
                    obj = name
                elif isinstance(name, str) and name in klasses:
                    obj = klasses[name]
                elif isinstance(name, type) and issubclass(name, klass):
                    obj = klasses[name.__name__]
                elif isinstance(name, klass):
                    obj = klasses[name.__class__.__name__]
                else:
                    raise ValueError(
                        '%s: invalid %s: %s' % (kobj, ktname, name)
                    )
                obj.validate_tree()
        validate_class(klass.__name__, klass.dependencies, 'Target', 'dependency')
        validate_class(klass.__name__, klass.uptodates, 'Mapper', 'uptodate')
        validate_class(klass.__name__, klass.tasks, 'Task', 'task')
    def call(self, name, klass, ktype, args=None):
        if (isinstance(name, type) and issubclass(name, klass)):
            obj = name()
        elif isinstance(name, klass):
            obj = name
        else:
            try:
                kobj = registry[name]
                assert issubclass(kobj, klass), \
                    "%s is not a %s" % (kobj, klass)
            except (KeyError, AssertionError):
                raise Error('%s no such %s: %s' % (self, ktype, name))
                logging.getLogger('pyerector').exception('Cannot find %s', name)
            else:
                obj = kobj()
        from .iterators import Uptodate
        if not isinstance(obj, Uptodate) and isinstance(obj, Mapper):
            return obj.uptodate()
        elif args is None:
            return obj()
        else:
            return obj(*args)
    def __call__(self, *args):
        myname = self.__class__.__name__
        global stack
        self.logger.debug('%s.__call__(*%s)', myname, args)
        timer = Timer()
        if self.been_called:
            return
        stack.push(self) # push me onto the execution stack
        try:
            if self.uptodates:
                for utd in self.uptodates:
                    try:
                        if not self.call(utd, Mapper, 'uptodate'):
                            break
                    except Error:
                        self.logger.exception('Exception in %s.uptodates', myname)
                        raise Abort
                else:
                    self.verbose('uptodate.')
                    return
            for dep in self.dependencies:
                try:
                    self.call(dep, Target, 'dependencies')
                except Error:
                    self.logger.exception('Exception in %s.dependencies', myname)
                    raise Abort
            with timer:
                for task in self.tasks:
                    try:
                        self.call(task, Task, 'task', args)
                    except Error:
                        self.logger.exception('Exception in %s.tasks', myname)
                        raise Abort
                try:
                    self.logger.debug('starting %s.run', myname)
                    self.run()
                except (KeyError, ValueError, TypeError,
                        RuntimeError, AttributeError):
                    raise # reraise
                except Abort:
                    raise # reraise
                except Error:
                    self.logger.exception('Exception in %s.run', myname)
                    raise Abort
                except Exception:
                    logging.getLogger('pyerector').exception('Exception')
                    raise Abort
            import pyerector
            if pyerector.noTimer:
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
        global stack
        self.logger.debug('%s.__call__(*%s, **%s)', myname, args, kwargs)
        stack.push(self) # push me onto the execution stack
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
                raise # reraise
            except Error:
                self.logger.exception('Exception in %s.run', myname))
                raise Abort
            except Exception:
                self.logger.exception('Exception')
                raise Abort
        finally:
            stack.pop()
        if rc:
            raise Error(str(self), 'return error = ' + str(rc))
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
        from .helper import Exclusions
        exclude = self.get_kwarg('exclude',
                    (Exclusions, set, str, tuple, list, type(None))
        )
        self.exclusion = Exclusions(exclude)
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration

class Mapper(Iterator):
    pass

