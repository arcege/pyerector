#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

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
from . import debug, verbose, noop
from .helper import normjoin, u
from .register import registry
from .exception import Error
from .config import Config
from .iterators import FileIterator, FileMapper, FileSet, StaticIterator

__all__ = [
    'Target', 'Task', 'Uptodate',
]

# the base class to set up the others
class Initer(Base):
    config = Config()
    def __init__(self, *args, **kwargs):
        debug('%s.__init__(*%s, **%s)' % (self.__class__.__name__, args, kwargs))
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
        if basedir is None:
            basedir = curdir
        if args:
            self.args = args
        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])
        #if not self.config.initialized:
        self.config.basedir = basedir or os.curdir
        self.config.initialized = True
    def wantnoglob(self):
        return ((hasattr(self, 'kwargs') and 'noglob' in  self.kwargs and
                    self.kwargs['noglob']) or
                (hasattr(self, 'noglob') and self.noglob))
    def get_files(self, files=None, noglob=None):
        if self.wantnoglob():
            iterator = StaticIterator
        else:
            iterator = FileIterator
        if not files:
            files = self.files
        if isinstance(files, (FileMapper, StaticIterator, FileSet)):
            return files
        else:
            fs = FileSet()
            for entry in files:
                if isinstance(entry, (FileMapper, StaticIterator, FileSet)):
                    fs.append(entry)
                elif isinstance(entry, (tuple, list)):
                    fs.append(iterator(entry, basedir=self.config.basedir))
                else:
                    fs.append(iterator((entry,), basedir=self.config.basedir))
            return fs
    def join(self, *path):
        debug('%s.join(%s, *%s)' % (self.__class__.__name__, self.config.basedir, path))
        return normjoin(self.config.basedir, *path)
    def asserttype(self, value, typeval, valname):
        if isinstance(typeval, type):
            typename = typeval.__name__
        else:
            typename = ' or '.join(t.__name__ for t in typeval)
        text = "Must supply %s to '%s' in '%s'" % (
            typename, valname, self.__class__.__name__
        )
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
        self.asserttype(value, (tuple, list, FileIterator, FileMapper), name)
        return value
    @classmethod
    def validate_tree(self):
        pass # do nothing, Target will do something with this

class Uptodate(Initer):
    sources = ()
    destinations = ()
    mappers = ()
    def __call__(self, *args):
        debug('%s.__call__(*%s)' % (self.__class__.__name__, args))
        klsname = self.__class__.__name__
        mappers = self.get_args('mappers')
        if not mappers and (not self.sources or not self.destinations):
            debug(klsname, '*>', False)
            return False
        if mappers:
            debug('using mappers')
            for mapper in mappers:
                for (s, d) in mapper:
                    sf = self.join(s)
                    df = self.join(d)
                    if os.path.isdir(sf):
                        result = self.checktree(sf, df)
                    else:
                        result = self.checkpair(sf, df)
                    if not result:
                        return False
            else:
                return True
        else:
            debug('comparing sources to destinations')
            srcs = self.get_files(self.sources)
            dsts = self.get_files(self.destinations)
            result = self.check(
                [self.join(s) for s in srcs],
                [self.join(d) for d in dsts])
            debug(klsname, '=>', result and 'False' or 'True')
            return result
    @staticmethod
    def check(srcs, dsts):
        # return True if earliest destination is newer than oldest
        # source
        debug('Uptodate.check(%s, %s)' % (srcs, dsts))
        maxval = float('inf')
        latest_src = reduce(max, [os.path.getmtime(s) for s in srcs], 0)
        earliest_dst = reduce(min, [os.path.getmtime(d) for d in dsts], maxval)
        debug('latest_src =', latest_src, 'earliest_dst =', earliest_dst)
        if earliest_dst == maxval: # empty list case
            return False
        result = round(earliest_dst, 4) >= round(latest_src, 4)
        return result
    @staticmethod
    def checkpair(src, dst):
        # return True if destination is newer than source
        try:
            s = round(os.path.getmtime(src), 4)
        except OSError:
            raise ValueError('no source:', src)
        try:
            d = round(os.path.getmtime(dst), 4)
        except OSError:
            return False
        return d >= s
    @staticmethod
    def checktree(src, dst):
        return False # always outofdate until we implement

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
                if ktype == 'Uptodate' and isinstance(name, klass):
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
        validate_class(klass.__name__, klass.uptodates, 'Uptodate', 'uptodate')
        validate_class(klass.__name__, klass.tasks, 'Task', 'task')
    def call(self, name, klass, ktype, args=None):
        if (isinstance(name, type) and issubclass(name, klass)):
            obj = name(basedir=self.config.basedir)
        elif isinstance(name, klass):
            obj = name
        else:
            try:
                kobj = registry[name]
                assert issubclass(kobj, klass), \
                    "%s is not a %s" % (kobj, klass)
            except (KeyError, AssertionError):
                if not debug:
                    raise Error('%s no such %s: %s' % (self, ktype, name))
                else:
                    raise
            else:
                obj = kobj(basedir=self.config.basedir)
        if args is None:
            return obj()
        else:
            return obj(*args)
    def __call__(self, *args):
        debug('%s.__call__(*%s)' % (self.__class__.__name__, args))
        if self.been_called:
            return
        if self.uptodates:
            for utd in self.uptodates:
                if not self.call(utd, Uptodate, 'uptodate'):
                    break
            else:
                self.verbose('uptodate.')
                return
        for dep in self.dependencies:
            self.call(dep, Target, 'dependencies')
        for task in self.tasks:
            try:
                self.call(task, Task, 'task', args)
            except Error:
                if not debug:
                    self.rewrap_exception()
                else:
                    raise
        try:
            self.run()
        except (TypeError, RuntimeError, AttributeError):
            raise
        except Error:
            if not debug:
                self.rewrap_exception()
            else:
                raise
        except Error:
            raise
        except Exception:
            if not debug:
                self.rewrap_exception()
            else:
                raise
        else:
            self.verbose('done.')
            self.been_called = True
    def run(self):
        pass
    def verbose(self, *args):
        msg = u('%s: %s' % (str(self), ' '.join(str(s) for s in args)))
        verbose.write(msg)

# Tasks
class Task(Initer):
    args = []
    def __str__(self):
        return self.__class__.__name__
    def __call__(self, *args, **kwargs):
        debug('%s.__call__(*%s, **%s)' % (self.__class__.__name__, args, kwargs))
        self.handle_args(args, kwargs)
        if noop:
            noop('Calling %s(*%s, **%s)' % (self, args, kwargs))
            return
        try:
            rc = self.run()
        except (TypeError, RuntimeError):
            raise
        except Exception:
            if not debug:
                self.rewrap_exception()
            else:
                raise
        if rc:
            raise Error(str(self), 'return error = ' + str(rc))
    def run(self):
        pass
    def handle_args(self, args, kwargs):
        if (hasattr(self, 'args') and not self.args) or args:
            self.args = list(args)
        if kwargs:
            self.kwargs = dict(kwargs)
