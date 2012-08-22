#!/usr/bin/python
# Copyright @ 2010-2012 Michael P. Reilly. All rights reserved.
# pyerector.py
#
# Options available to pymain():
#    -h|--help               call the 'help' target and exit
#    -v|--verbose            display debugging output
#    -N|--dry-run            do not perform actual steps (bypass 'run()' method)
#    -d=DIR|--directory=DIR  change the basedir value
# Options available to pyerector.py:
#    help                    call the 'help' target and exit
#    version                 display library version
#    test                    run test of pyerector.py
#
# Example code:
# ---------------------------------------------
# from pyerector import *
# Compile.dependencies = ('PythonPrecompile',)
# class PreCompile_utd(Uptodate):
#     sources = ('*.py',)
#     destinations = ('build/*.pyc',)
# class PyCopy_t(Copy):
#     sources = ('*.py',)
#     destination = 'build'
# class PyCopy(Target):
#     files = ('*.py',)
#     tasks = ("PyCopy_t",)
# class PythonPreCompile(Target):
#     dependencies = ("PyCopy",)
#     uptodates = ("PreCompile_utd",)
#     files = ('build/*.py',)
#     def run(self):
#         from py_compile import compile
#         for file in self.get_files():
#             compile(file)
#
# pymain()
# ---------------------------------------------
# $Id$

from __future__ import print_function
_RCS_VERSION = '$Revision$'

from sys import version
if version < '3':
    def u(x):
        from codecs import unicode_escape_decode
        return unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

import unittest

# Future Py3000 work prevents the use of string formatting using '%'
# trying to use both string formatting and ''.format is UGLY!!!!
# A LOT of the code below will be using the less efficient string
# concatentation which is supported across both sets of releases.
try:
    ''.format
except AttributeError:
    hasformat = False
else:
    hasformat = True

__all__ = [
  'Target', 'Uptodate', 'pymain', 'symbols_to_global',
  # standard targets
  'All', 'Default', 'Help', 'Clean', 'Init', 'InitDirs',
  'Build', 'Compile', 'Dist', 'Packaging', 'Test',
  # tasks
  'Task', 'Spawn', 'Remove', 'Copy', 'CopyTree', 'Mkdir', 'Chmod', 'Java',
  'Shebang', 'Tar', 'Unittest', 'Untar', 'Unzip', 'Zip',
]

class Config:
    initialized = False
    _basedir = None
    def __init__(self, basedir=None):
        from os import curdir
        if basedir is not None:
            self.basedir = basedir
    def _get_basedir(self, value):
        return self._basedir
    def _set_basedir(self, value):
        from os.path import normpath, realpath, isdir
        dir = normpath(realpath(value))
        if isdir(dir):
            self._basedir = dir
        else:
            raise ValueError('no such file or directory: %s' % dir)
    basedir = property(_get_basedir, _set_basedir)

class Verbose(object):
    from os import linesep as eoln
    from sys import stdout as stream
    def __init__(self, state=False):
        self.state = bool(state)
    def __bool__(self):
        return self.state
    __nonzero__ = __bool__
    def on(self):
        self.state = True
    def off(self):
        self.state = False
    def _write(self, msg):
        if self.state:
            self.stream.write(u(msg))
            self.stream.write(u(self.eoln))
            self.stream.flush()
    def __call__(self, *args):
        self._write(u(' ').join([u(str(s)) for s in args]))
verbose = Verbose()
noop = Verbose()
from os import environ
debug = Verbose('DEBUG' in environ and environ['DEBUG'] != '')
del environ

# the main program, an instance to be called by pyerect program
class Main(object):
    import argparse
    parser = argparse.ArgumentParser('Pyerector build system')
    del argparse
    parser.add_argument('targets', metavar='TARGET', nargs='*',
                        help='names of targets to call')
    parser.add_argument('--directory', '-d',
                        help='base directory')
    parser.add_argument('--dry-run', '-N', dest='noop', action='store_true',
                        help='do not perform operations')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='more verbose output')
    def __call__(self, *args):
        from sys import argv
        self.basedir = None
        self.targets = []
        self.arguments(args or argv[1:])
        self.validate_targets()
        self.run()
    def arguments(self, args):
        global verbose, noop
        import __main__
        args = self.parser.parse_args(args)
        if args.verbose:
            verbose.on()
        if args.noop:
            noop.on()
        if args.directory:
            self.basedir = args.directory
        if args.targets:
            self.targets = []
            all_targets = Target.get_targets()
            for name in args.targets:
                try:
                    obj = all_targets[name.capitalize()]
                except KeyError:
                    raise SystemExit('Error: unknown target: ' + str(name))
                else:
                    if not issubclass(obj, Target):
                        raise SystemExit('Error: unknown target: ' + str(name))
                    self.targets.append(obj)
        else:
            self.targets = [__main__.Default]
    def handle_error(self, text=''):
        from sys import argv, exc_info
        if debug:
            raise
        else:
            e = exc_info()[1]
            if text:
                raise SystemExit('%s: %s' % (text, e))
            else:
                raise SystemExit(str(e))
    def validate_targets(self):
        # validate the dependency tree, make sure that all are subclasses of
        # Target, validate all Uptodate values and all Task values
        for target in self.targets:
            try:
                target.validate_tree()
            except ValueError:
                self.handle_error('Error')
    def run(self):
        # run all targets in the tree of each argument
        for target in self.targets:
            try:
                target(basedir=self.basedir)()
            except ValueError:
                self.handle_error()
            except KeyboardInterrupt:
                self.handle_error()
            except AssertionError:
                self.handle_error('AssertionError')

pymain = Main()

# helper function to reference classes in current scope
def symbols_to_global(*classes, **kwargs):
    from sys import modules
    if 'modname' in kwargs:
        modname = kwargs['modname']
    else:
        modname = __name__
    moddict = modules[modname].__dict__
    for klass in classes:
        moddict[klass.__name__] = klass

# the classes

# a helper class to handle file/directory lists better
class FileIterator(object):
    def __init__(self, path, exclude=None, basedir=None):
        from os import curdir
        super(FileIterator, self).__init__()
        if isinstance(path, (tuple, list)):
            self.pool = list(path)
        else:
            self.pool = [path]
        self.pos = 0
        self.exclude = exclude
        if basedir is None:
            basedir = _Initer.config.basedir or curdir
        self.basedir = basedir
    def __iter__(self):
        self.pos = 0
        return self
    def next(self):
        from os.path import normpath, join
        while True:
            if self.pos >= len(self.pool):
                raise StopIteration
            item = self.pool[self.pos]
            self.pos += 1
            if not self.apply_exclusion(item):
                return item
    def apply_exclusion(self, filename):
        from fnmatch import fnmatch
        result = self.exclude and fnmatch(filename, self.exclude)
        debug('apply_exclusion(%s, %s) =' % (filename, self.exclude),
                result)
        return result
class FileList(FileIterator):
    def __init__(self, *args, **kwargs):
        super(FileList, self).__init__(path=args, **kwargs)

class DirList(FileIterator):
    def __init__(self, path, recurse=False, filesonly=True, **kwargs):
        super(DirList, self).__init__(path, **kwargs)
        self.recurse = bool(recurse)
        self.filesonly = bool(filesonly)
        self.update_dirpath()
    def update_dirpath(self):
        from os import listdir
        from os.path import basename, isdir, isfile, islink, join
        dirs = self.pool[:]
        paths = []
        while dirs:
            thisdir = dirs[0]
            del dirs[0]
            if not self.filesonly:
                paths.append(thisdir)
            if not self.apply_exclusion(basename(thisdir)):
                for name in listdir(join(self.basedir, thisdir)):
                    spath = join(thisdir, name)
                    dpath = join(self.basedir, thisdir, name)
                    if self.apply_exclusion(name):
                        pass
                    elif islink(dpath) or isfile(dpath):
                        paths.append(spath)
                    elif self.recurse:
                        dirs.append(spath)
        self.pool[:] = paths # replace the pool with the gathered set

# the base class to set up the others
class _Initer(object):
    class Error(Exception):
        def __str__(self):
            return str(self[0]) + ': ' + str(self[1])
        def __format__(self, format_spec):
            if isinstance(self, unicode):
                return unicode(str(self))
            else:
                return str(self)
    config = Config()
    from os import curdir
    def __init__(self, basedir=None, curdir=curdir):
        from os.path import normpath, realpath
        if basedir is None:
            basedir = curdir
        if not self.config.initialized:
            self.config.basedir = normpath(realpath(basedir))
            self.config.initialized = True
        self.basedir = normpath(realpath(basedir))
    del curdir
    def get_files(self, files=None, noglob=False, subdir=None):
        from glob import glob
        from os.path import join
        from os import curdir
        if noglob:
            glob = lambda x: [x]
        if subdir is None:
            subdir = curdir
        if not files:
            files = self.files
        filelist = []
        for entry in files:
            if isinstance(entry, FileIterator):
                s = [self.join(e) for e in entry]
            else:
                s = glob(self.join(subdir, entry))
            filelist.extend(s)
        return filelist
    def join(self, *path):
        from os.path import join
        return join(self.basedir, *path)
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
        if name in self.kwargs:
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
        if self.args:
            value = self.args
        else:
            value = getattr(self, name)
        self.asserttype(value, (tuple, list), name)
        return value

class Test_Initer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tempfile import mkdtemp
        cls.dir = mkdtemp()
    @classmethod
    def tearDownClass(cls):
        from shutil import rmtree
        rmtree(cls.dir)
    def test_initialized(self):
        #"""Is system initialized on first instantiation."""
        old_config = _Initer.config
        try:
            _Initer.config = Config()
            _Initer.config.initialized = False
            self.assertFalse(_Initer.config.initialized)
            obj = _Initer()
            self.assertTrue(_Initer.config.initialized)
        finally:
            _Initer.config = old_config
    def test_basedir(self):
        from os import curdir, getcwd
        from os.path import normpath, realpath
        obj = _Initer()
        self.assertEqual(obj.basedir, normpath(realpath(getcwd())))
        obj = _Initer(basedir=self.dir)
        self.assertEqual(obj.basedir, self.dir)
    def test_join(self):
        #"""Ensure that join() method returns proper values."""
        from os.path import join
        obj = _Initer(basedir=self.dir)
        self.assertEqual(obj.join('foobar'), join(self.dir, 'foobar'))
        self.assertEqual(obj.join('xyzzy', 'foobar'),
                         join(self.dir, 'xyzzy', 'foobar'))
    def test_asserttype(self):
        obj = _Initer(basedir=self.dir)
        self.assertIsNone(obj.asserttype('foo', str, 'foobar'))
        for test in (('foo', int, 'name'), (1, str, 'foobar')):
            self.assertRaises(AssertionError, obj.asserttype, *test)
        with self.assertRaises(AssertionError) as cm:
            obj.asserttype(1, str, 'foobar')
        exc = cm.exception
        self.assertEqual(str(exc), "Must supply str to 'foobar' in '_Initer'")
    def test_get_files_simple(self):
        #"""Retrieve files in basedir properly."""
        from os import mkdir, curdir
        from os.path import join
        obj = _Initer(basedir=self.dir)
        # no files
        self.assertEqual(obj.get_files(('get_files_simple-*',)), [])
        subdir = curdir
        open(join(self.dir, subdir, 'get_files_simple-bar'), 'w').close()
        open(join(self.dir, subdir, 'get_files_simple-far'), 'w').close()
        open(join(self.dir, subdir, 'get_files_simple-tar'), 'w').close()
        # test simple glob
        self.assertEqual(sorted(obj.get_files(('get_files_simple-*',))),
                         [join(self.dir, subdir, 'get_files_simple-bar'),
                          join(self.dir, subdir, 'get_files_simple-far'),
                          join(self.dir, subdir, 'get_files_simple-tar')])
        # test glob pattern against noglob
        self.assertEqual(obj.get_files(('get_files_simple-*',), noglob=True),
                         [join(self.dir, subdir, 'get_files_simple-*')])
        # test single file
        self.assertEqual(obj.get_files(('get_files_simple-bar',)),
                         [join(self.dir, subdir, 'get_files_simple-bar')])
        # test single file, no glob
        self.assertEqual(obj.get_files(('get_files_simple-tar',), noglob=True),
                         [join(self.dir, subdir, 'get_files_simple-tar')])
        # test simple file tuple, with glob
        self.assertEqual(sorted(obj.get_files(('get_files_simple-bar', 'get_files_simple-tar'))),
                         [join(self.dir, subdir, 'get_files_simple-bar'),
                          join(self.dir, subdir, 'get_files_simple-tar')])
        # test glob file tuple, with glob
        self.assertEqual(sorted(obj.get_files(('get_files_simple-bar', 'get_files_simple-t*'))),
                         [join(self.dir, subdir, 'get_files_simple-bar'),
                          join(self.dir, subdir, 'get_files_simple-tar')])
        # test globl file tuple, no glob
        self.assertEqual(sorted(obj.get_files(('get_files_simple-bar', 'get_files_simple-t*'),
                                              noglob=True)),
                         [join(self.dir, subdir, 'get_files_simple-bar'),
                          join(self.dir, subdir, 'get_files_simple-t*')])
    def test_get_files_subdir(self):
        from os import mkdir, curdir
        from os.path import join
        obj = _Initer(basedir=self.dir)
        # test subdir value
        subdir = 'subdir'
        mkdir(join(self.dir, subdir))
        open(join(self.dir, subdir, 'get_files_subdir-par'), 'w').close()
        open(join(self.dir, subdir, 'get_files_subdir-rar'), 'w').close()
        self.assertEqual(sorted(obj.get_files(('get_files_subdir-*',),
                                              subdir=subdir)),
                         [join(self.dir, subdir, 'get_files_subdir-par'),
                          join(self.dir, subdir, 'get_files_subdir-rar')])
        self.assertEqual(sorted(obj.get_files(('get_files_subdir-par',
                                               'get_files_subdir-rar'),
                                              subdir=subdir)),
                         [join(self.dir, subdir, 'get_files_subdir-par'),
                          join(self.dir, subdir, 'get_files_subdir-rar')])
        self.assertEqual(obj.get_files(('get_files_subdir-par',),
                                       noglob=True,
                                       subdir=subdir),
                         [join(self.dir, subdir, 'get_files_subdir-par')])

class Uptodate(_Initer):
    sources = ()
    destinations = ()
    def __call__(self, *args):
        klsname = self.__class__.__name__
        from os.path import getmtime
        try:
            from sys import maxsize as maxint
        except ImportError:
            from sys import maxint
        self.srcs = []
        self.dsts = []
        if not self.sources or not self.destinations:
            verbose(klsname, '*>', False)
            return False
        self.srcs = self.get_files(self.sources)
        self.dsts = self.get_files(self.destinations)
        # if no actual destination files then nothing is uptodate
        if not self.dsts and self.destinations:
            verbose(klsname, '+>', False)
            return False
        # compare the latest mtime of the sources with the earliest
        # mtime of the destinations
        latest_src = 0
        earliest_dst = maxint
        for src in self.srcs:
            latest_src = max(latest_src, getmtime(src))
        for dst in self.dsts:
            earliest_dst = min(earliest_dst, getmtime(dst))
        result = round(earliest_dst, 4) >= round(latest_src, 4)
        verbose(klsname, '=>', result and "False" or "True")
        return result

class TestUptodate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.dir = tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.dir)
    def test_older(self):
        #"""Test that newer files indeed do trigger the test."""
        import os, time
        older = os.path.join(self.dir, 'older-older')
        newer = os.path.join(self.dir, 'older-newer')
        open(older, 'w').close()
        open(newer, 'w').close()
        now = time.time()
        then = now - 600 # 10 minutes
        os.utime(older, (then, then))
        os.utime(newer, (now, now))
        utd = Uptodate(basedir=self.dir)
        utd.sources = (older,)
        utd.destinations = (newer,)
        self.assertTrue(utd())
    def test_newer(self):
        #"""Test that older files indeed do not trigger the test."""
        import os, time
        older = os.path.join(self.dir, 'newer-older')
        newer = os.path.join(self.dir, 'newer-newer')
        open(older, 'w').close()
        open(newer, 'w').close()
        now = time.time()
        then = now - 600 # 10 minutes
        os.utime(older, (now, now))
        os.utime(newer, (then, then))
        utd = Uptodate(basedir=self.dir)
        utd.sources = (older,)
        utd.destinations = (newer,)
        self.assertFalse(utd())
    def test_same(self):
        #"""Test that files of the same age do trigger the test."""
        import os, time
        older = os.path.join(self.dir, 'same-older')
        newer = os.path.join(self.dir, 'same-newer')
        open(older, 'w').close()
        open(newer, 'w').close()
        now = time.time()
        then = now  # no change
        os.utime(older, (then, then))
        os.utime(newer, (now, now))
        utd = Uptodate(basedir=self.dir)
        utd.sources = (older,)
        utd.destinations = (newer,)
        self.assertTrue(utd())
    def test_multi_older(self):
        #"""Test that files in directories are handled properly."""
        import os, time
        older_d = os.path.join(self.dir, 'multi_older-older')
        newer_d = os.path.join(self.dir, 'multi_older-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, then), (newer_d, now)):
            for i in range(0, 3):
                fn = os.path.join(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertTrue(utd())
    def test_multi_newer(self):
        import os, time
        older_d = os.path.join(self.dir, 'multi_newer-older')
        newer_d = os.path.join(self.dir, 'multi_newer-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, now), (newer_d, then)):
            for i in range(0, 3):
                fn = os.path.join(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertFalse(utd())
    def test_multi_same(self):
        import os, time
        older_d = os.path.join(self.dir, 'multi_same-older')
        newer_d = os.path.join(self.dir, 'multi_same-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, then), (newer_d, now)):
            for i in range(0, 11, 5):
                fn = os.path.join(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertTrue(utd())
    def test_multi_mixed(self):
        import os, time
        older_d = os.path.join(self.dir, 'multi_mixed-older')
        newer_d = os.path.join(self.dir, 'multi_mixed-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, now), (newer_d, then)):
            for i in range(0, 16, 5):
                fn = os.path.join(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertFalse(utd())

class Target(_Initer):
    from sys import stdout as stream
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
        if self.allow_reexec:
            return False
        return self.__class__._been_called
    def set_been_called(self, value):
        self.__class__._been_called = value
    been_called = property(get_been_called, set_been_called)
    def __str__(self):
        return self.__class__.__name__
    @classmethod
    def validate_tree(klass):
        name = klass.__name__
        targets = klass.get_targets()
        uptodates = klass.get_uptodates()
        tasks = klass.get_tasks()
        try:
            deps = klass.dependencies
        except AttributeError:
            pass
        else:
            for dep in deps:
                if dep not in targets:
                    raise ValueError(
                        str(name) + ': invalid dependency: ' + str(dep)
                    )
                targets[dep].validate_tree()
        try:
            utds = klass.uptodates
        except AttributeError:
            pass
        else:
            for utd in utds:
                if utd not in uptodates:
                    raise ValueError(
                        str(name) + ': invalid uptodate: ' + str(utd)
                    )
        try:
            tsks = klass.tasks
        except AttributeError:
            pass
        else:
            for tsk in tsks:
                if tsk not in tasks:
                    raise ValueError(
                        str(name) + ': invalid task: ' + str(tsk)
                    )
    def call_uptodate(self, klassname):
        uptodates = self.get_uptodates()
        try:
            klass = uptodates[klassname]
        except KeyError:
            if not debug:
                raise self.Error(str(self), 'no such uptodate: ' + str(klassname))
            else:
                raise
        return klass(basedir=self.basedir)()
    def call_dependency(self, klassname):
        targets = self.get_targets()
        try:
            klass = targets[klassname]
        except KeyError:
            if not debug:
                raise self.Error(str(self), 'no such dependency: ' + str(klassname))
            else:
                raise
        klass(basedir=self.basedir)()
    def call_task(self, klassname, args):
        tasks = self.get_tasks()
        try:
            klass = tasks[klassname]
        except KeyError:
            if not debug:
                raise self.Error(str(self), 'no such task: ' + str(klassname))
            else:
                raise
        return klass(basedir=self.basedir)(*args)
    def __call__(self, *args):
        from sys import exc_info
        if self.been_called:
            return
        if self.uptodates:
            for utd in self.uptodates:
                if not self.call_uptodate(utd):
                    break
            else:
                self.verbose('uptodate.')
                return
        for dep in self.dependencies:
            self.call_dependency(dep)
        for task in self.tasks:
            try:
                self.call_task(task, args) # usually args would be (), but...
            except self.Error:
                if not debug:
                    e = exc_info()[1]
                    raise self.Error(str(self) + ':' + str(e[0]), e[1])
                else:
                    raise
        try:
            self.run()
        except (TypeError, RuntimeError, AttributeError):
            raise
        except Task.Error:
            if not debug:
                e = exc_info()[1]
                raise self.Error(str(self) + ':' + str(e[0]), e[1])
            else:
                raise
        except self.Error:
            raise
        except Exception:
            if not debug:
                e = exc_info()[1]
                raise self.Error(str(self), e)
            else:
                raise
        else:
            self.verbose('done.')
            self.been_called = True
    def run(self):
        pass
    def verbose(self, *args):
        self.stream.write(u(str(self)))
        self.stream.write(u(': '))
        self.stream.write(u(' ').join([u(str(s)) for s in args]))
        self.stream.write(u('\n'))
        self.stream.flush()
    @staticmethod
    def get_tasks():
        import __main__
        if not hasattr(__main__, '_tasks_cache'):
            tasks = {}
            for name, obj in list(vars(__main__).items()):
                if not name.startswith('_') \
                   and obj is not Task \
                   and isinstance(obj, type(Task)) \
                   and issubclass(obj, Task):
                    tasks[name] = obj
            setattr(__main__, '_tasks_cache', tasks)
        return getattr(__main__, '_tasks_cache')
    @staticmethod
    def get_targets():
        import __main__
        if not hasattr(__main__, '_targets_cache'):
            targets = {}
            for name, obj in list(vars(__main__).items()):
                if not name.startswith('_') \
                   and obj is not Target \
                   and isinstance(obj, type(Target)) \
                   and issubclass(obj, Target):
                    targets[name] = obj
            setattr(__main__, '_targets_cache', targets)
        return getattr(__main__, '_targets_cache')
    @staticmethod
    def get_uptodates():
        import __main__
        if not hasattr(__main__, '_uptodates_cache'):
            uptodates = {}
            for name, obj in list(vars(__main__).items()):
                if not name.startswith('_') \
                   and obj is not Uptodate \
                   and isinstance(obj, type(Uptodate)) \
                   and issubclass(obj, Uptodate):
                    uptodates[name] = obj
            setattr(__main__, '_uptodates_cache', uptodates)
        return getattr(__main__, '_uptodates_cache')

class TestTarget(unittest.TestCase):
    maxDiff = None
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.dir = tempfile.mkdtemp()
        Target.allow_reexec = True
        class TestBeenCalled(Target):
            allow_reexec = False
        class TestUptodate_utd(Uptodate):
            pass
        class TestCallUptodate_utd(Uptodate):
            sources = ('call_uptodate,older',)
            destinations = ('call_uptodate.newer',)
        class TestCallUptodate_T(Target):
            uptodates = ("TestCallUptodate_utd",)
        class TestCallTask_t(Task):
            def run(self):
                verbose('Creating', self.join(self.args[0]))
                open(self.join(self.args[0]), 'w').close()
        class TestCallTask_T(Target):
            tasks = ("TestCallTask_t",)
        class TestCallDependency_t(Task):
            def run(self):
                open(self.join('calldependency'), 'w').close()
        class TestCallDependency_T1(Target):
            tasks = ("TestCallDependency_t",)
        class TestCallDependency_T(Target):
            dependencies = ("TestCallDependency_T1",)
        class TestE2E_t1(Task):
            def run(self):
                from time import sleep
                open(self.join('e2e_t1'), 'w').close()
                #sleep(1)
        class TestE2E_t2(Task):
            def run(self):
                open(self.join('e2e_t2'), 'w').close()
        class TestE2E_utd(Uptodate):
            sources = ('e2e_t1',)
            destinations = ('e2e_t2',)
        class TestE2E_T(Target):
            uptodates = ('TestE2E_utd',)
            tasks = ('TestE2E_t1', 'TestE2E_t2')
        cls.uptodate_classes = {
            'TestUptodate_utd': TestUptodate_utd,
            'TestCallUptodate_utd': TestCallUptodate_utd,
            'TestE2E_utd': TestE2E_utd,
        }
        cls.target_classes = {
            'Help': Help, 'All': All, 'Default': Default, 'Dist': Dist,
            'Packaging': Packaging, 'Build': Build, 'Compile': Compile,
            'Init': Init, 'InitDirs': InitDirs, 'Clean': Clean, 'Test': Test,
            'TestCallUptodate_T': TestCallUptodate_T,
            'TestBeenCalled': TestBeenCalled,
            'TestCallTask_T': TestCallTask_T,
            'TestCallDependency_T1': TestCallDependency_T1,
            'TestCallDependency_T': TestCallDependency_T,
            'TestE2E_T': TestE2E_T,
        }
        cls.task_classes = {
            'Spawn': Spawn, 'Unzip': Unzip, 'Java': Java, 'Tar': Tar,
            'Zip': Zip, 'Shebang': Shebang, 'Untar': Untar,
            'Mkdir': Mkdir, 'Remove': Remove, 'Chmod': Chmod,
            'CopyTree': CopyTree, 'Copy': Copy, 'Unittest': Unittest,
            'TestCallTask_t': TestCallTask_t,
            'TestCallDependency_t': TestCallDependency_t,
            'TestE2E_t1': TestE2E_t1, 'TestE2E_t2': TestE2E_t2,
        }
        # if called from ./pyerector.py, use mod1, if called
        # from unittest itself, then use mod1 and mod2
        mod1 = {'modname': '__main__'}
        if __name__ != '__main__':
            mod2 = {'modname': __name__}
        else:
            mod2 = {}
        symbols_to_global(*list(cls.uptodate_classes.values()), **mod1)
        symbols_to_global(*list(cls.uptodate_classes.values()), **mod2)
        symbols_to_global(*list(cls.target_classes.values()), **mod1)
        symbols_to_global(*list(cls.target_classes.values()), **mod2)
        symbols_to_global(*list(cls.task_classes.values()), **mod1)
        symbols_to_global(*list(cls.task_classes.values()), **mod2)
    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.dir)
    def setUp(self):
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        self.real_stream = Target.stream
        Target.stream = StringIO()
    def tearDown(self):
        if hasattr(self, 'real_stream'):
            Target.stream = getattr(self, 'real_stream')
    def test_been_called(self):
        target = TestBeenCalled()
        self.assertFalse(target.been_called)
        target()
        self.assertTrue(target.been_called)
    def test_get_uptodates(self):
        global TestUptodate_utd
        import __main__
        result = Target.get_uptodates()
        self.assertEqual(Target.get_uptodates(), self.uptodate_classes)
    def test_get_targets(self):
        self.assertEqual(Target.get_targets(), self.target_classes)
    def test_get_tasks(self):
        self.assertEqual(Target.get_tasks(), self.task_classes)
    def test_verbose(self):
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        target = Target()
        target.stream = StringIO()
        target.verbose('hi there')
        self.assertEqual(target.stream.getvalue(), 'Target: hi there\n')
        target.stream = StringIO()
        target.verbose('hi', 'there')
        self.assertEqual(target.stream.getvalue(), 'Target: hi there\n')
    def test_nothing(self):
        class NothingTarget(Target):
            pass
        target = NothingTarget()
        self.assertIsNone(NothingTarget.validate_tree())
        self.assertIsNone(target())
    def test_call_uptodate(self):
        import __main__, tempfile, time
        from os.path import join, isfile
        open(join(self.dir, 'call_uptodate.older'), 'w').close()
        #time.sleep(1)
        open(join(self.dir, 'call_uptodate.newer'), 'w').close()
        self.assertTrue(TestCallUptodate_utd(basedir=self.dir)())
        target = TestCallUptodate_T(basedir=self.dir)
        self.assertTrue(target.call_uptodate('TestCallUptodate_utd'))
    def test_call_task(self):
        import os
        from os.path import join, isfile
        self.assertFalse(isfile(join(self.dir, 'calltask')))
        target = TestCallTask_T(basedir=self.dir)
        self.assertIsNone(target.call_task("TestCallTask_t", ('calltask',)))
        self.assertTrue(isfile(join(self.dir, 'calltask')))
    def test_call_dependency(self):
        from os.path import join, isfile
        self.assertFalse(isfile(join(self.dir, 'calldependency')))
        target = TestCallDependency_T(basedir=self.dir)
        self.assertIsNone(target.call_dependency("TestCallDependency_T"))
        self.assertTrue(isfile(join(self.dir, 'calldependency')))
    def test_end_to_end(self):
        from os.path import join, isfile, getmtime
        self.assertFalse(isfile(join(self.dir, 'e2e_t1')))
        self.assertFalse(isfile(join(self.dir, 'e2e_t2')))
        target = TestE2E_T(basedir=self.dir)
        self.assertIsNone(target())
        self.assertTrue(isfile(join(self.dir, 'e2e_t1')))
        self.assertTrue(isfile(join(self.dir, 'e2e_t2')))
        t1 = getmtime(join(self.dir, 'e2e_t1'))
        t2 = getmtime(join(self.dir, 'e2e_t2'))
        target = TestE2E_T(basedir=self.dir)
        self.assertIsNone(target())
        self.assertEqual(round(t1, 4), round(getmtime(join(self.dir, 'e2e_t1')), 4))
        self.assertEqual(round(t2, 4), round(getmtime(join(self.dir, 'e2e_t2')), 4))

# Tasks
class Task(_Initer):
    args = []
    def __str__(self):
        return self.__class__.__name__
    def __call__(self, *args, **kwargs):
        from sys import exc_info
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
                e = exc_info()[1]
                raise self.Error(str(self), e)
            else:
                raise
        if rc:
            raise self.Error(str(self), 'return error = ' + str(rc))
    def run(self):
        pass
    def handle_args(self, args, kwargs):
        self.args = list(args)
        self.kwargs = dict(kwargs)

class TestTask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.dir = tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.dir)
    def test_instantiation(self):
        obj = Task()
        self.assertEqual(str(obj), Task.__name__)
        self.assertIsNone(obj('foobar', 'xyzzy', widget=True))
        # after calling __call__()
        self.assertEqual(obj.args, ['foobar', 'xyzzy'])
        self.assertEqual(obj.kwargs, {'widget': True})
    def test_failure(self):
        class SuccessTask(Task):
            def run(self):
                return 0
        class FailureTask(Task):
            def run(self):
                return 255
        self.assertIsNone(SuccessTask()())
        self.assertRaises(Task.Error, FailureTask())
    def test_exception(self):
        class TypeErrorTask(Task):
            def run(self):
                raise TypeError
        class ValueErrorTask(Task):
            def run(self):
                raise ValueError
        self.assertRaises(TypeError, TypeErrorTask())
        self.assertRaises(Task.Error, ValueErrorTask())
    def test_noop(self):
        global noop
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        old_noop = noop
        try:
            noop = Verbose()
            noop.on()
            noop.stream = StringIO()
            class NoopTask(Task):
                foobar = False
                def run(self):
                    self.foobar = True
            obj = NoopTask()
            obj()
            self.assertEqual(noop.stream.getvalue(),
                             'Calling NoopTask(*(), **{})\n')
            self.assertFalse(obj.foobar)
        finally:
            noop = old_noop

# standard tasks

class Spawn(Task):
    cmd = ()
    infile = None
    outfile = None
    errfile = None
    def run(self):
        infile = self.get_kwarg('infile', str)
        outfile = self.get_kwarg('outfile', str)
        errfile = self.get_kwarg('errfile', str)
        cmd = self.get_args('cmd')
        from os import WIFSIGNALED, WTERMSIG, WEXITSTATUS
        try:
            from subprocess import call
            ifl = of = ef = None
            if infile:
                ifl = open(infile, 'r')
            if outfile:
                of = open(outfile, 'w')
            if errfile == outfile:
                ef = of
            elif errfile:
                ef = open(errfile, 'w')
            if isinstance(cmd, list) and len(cmd) == 1:
                cmd = cmd[0]
            verbose('spawn("' + str(cmd) + '")')
            shellval = not isinstance(cmd, tuple)
            rc = call(cmd, shell=shellval, stdin=ifl, stdout=of, stderr=ef, bufsize=0)
            if rc < 0:
                raise self.Error(str(self), 'signal ' + str(abs(rc)) + 'raised')
            elif rc > 0:
                raise self.Error(str(self), 'returned error + ' + str(rc))
            pass
        except ImportError:
            from popen2 import Popen3
            if isinstance(cmd, tuple):
                pcmd = ' '.join('"%s"' % str(s) for s in cmd)
            pcmd = cmd
            if outfile:
                pcmd += '>"' + str(outfile) + '"'
            if errfile == outfile:
                pcmd += '2>&1'
            elif errfile:
                pcmd += '2>"' + str(errfile) + '"'
            verbose('spawn("' + str(pcmd) + '")')
            rc = Popen3(pcmd, capturestderr=False, bufsize=0).wait()
            if WIFSIGNALED(rc):
                raise self.Error(str(self),
                                 'signal ' + str(WTERMSIG(rc)) + 'raised')
            elif WEXITSTATUS(rc):
                raise self.Error(str(self), 'returned error = ' + str(rc))
            pass
class Remove(Task):
    files = ()
    noglob = False
    def run(self):
        from os import remove
        from os.path import isdir, isfile, islink
        from shutil import rmtree
        files = tuple(self.get_args('files'))
        for fname in self.get_files(files, self.noglob):
            self.asserttype(fname, str, 'files')
            if isfile(fname) or islink(fname):
                verbose('remove(' + str(fname) + ')')
                remove(fname)
            elif isdir(fname):
                verbose('rmtree(' + str(fname) + ')')
                rmtree(fname)
class Copy(Task):
    files = ()
    dest = None
    noglob = False
    def wantnoglob(self):
        return (('noglob' in self.kwargs and self.kwargs['noglob']) or
                self.noglob)
    def run(self):
        from shutil import copy2
        verbose('starting Copy')
        dst = self.join(self.get_kwarg('dest', str, noNone=True))
        srcs = self.get_files(self.get_args('files'), noglob=self.wantnoglob())
        for fname in srcs:
            self.asserttype(fname, str, 'files')
            verbose('copy2(' + str(fname) + ', ' + str(dst) + ')')
            copy2(fname, dst)
class Shebang(Copy):
    files = ()
    token = '#!'
    def run(self):
        from shutil import copyfileobj
        verbose('starting Shebang')
        program = self.get_kwarg('program', str, noNone=True)
        srcs = self.get_files(self.get_args('files'), noglob=self.wantnoglob())
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        from os import linesep
        for fname in srcs:
            inf = open(fname, 'r')
            outf = StringIO()
            first = inf.readline()
            if first.startswith(self.token):
                if ' ' in first:
                    w = first.find(' ')
                else:
                    w = first.find(linesep)
                first = first.replace(first[len(self.token):w], program)
                outf.write(first)
            else:
                outf.write(first)
            copyfileobj(inf, outf)
            inf.close()
            outf.seek(0)
            inf = open(fname, 'w')
            copyfileobj(outf, inf)
class CopyTree(Task):
    srcdir = None
    dstdir = None
    excludes = ('.svn',)
    def run(self):
        from fnmatch import fnmatch
        from os import curdir, error, listdir
        from os.path import exists, join, isdir, normpath
        srcdir = self.get_kwarg('srcdir', str, noNone=True)
        dstdir = self.get_kwarg('dstdir', str, noNone=True)
        if not exists(self.join(srcdir)):
            raise error(2, "No such file or directory: " + srcdir)
        elif not isdir(self.join(srcdir)):
            raise error(20, "Not a directory: " + srcdir)
        copy_t = Copy()
        mkdir_t = Mkdir()
        # override what is set in the class definition
        copy_t.noglob = True
        dirs = [curdir]
        while dirs:
            dir = dirs[0]
            del dirs[0]
            if self.check_exclusion(dir):
                mkdir_t(normpath(self.join(dstdir, dir)))
                for fname in listdir(self.join(srcdir, dir)):
                    if self.check_exclusion(fname):
                        spath = self.join(srcdir, dir, fname)
                        dpath = self.join(dstdir, dir, fname)
                        if isdir(spath):
                            dirs.append(join(dir, fname))
                        else:
                            copy_t(spath, dest=dpath)
    def check_exclusion(self, filename):
        from fnmatch import fnmatch
        for excl in self.excludes:
            if fnmatch(filename, excl):
                return False
        else:
            return True
class Mkdir(Task):
    files = ()
    def run(self):
        for arg in self.get_args('files'):
            self.asserttype(arg, str, 'files')
            self.mkdir(self.join(arg))
    @classmethod
    def mkdir(klass, path):
        from os import mkdir, remove
        from os.path import dirname, isdir, isfile, islink
        if islink(path) or isfile(path):
            verbose('remove(' + str(path) + ')')
            remove(path)
            klass.mkdir(path)
        elif not isdir(path):
            klass.mkdir(dirname(path))
            verbose('mkdir(' + str(path) + ')')
            mkdir(path)
class Chmod(Task):
    files = ()
    mode = int('666', 8) # gets around Python 2.x vs 3.x octal issue
    def run(self):
        from os import chmod
        mode = self.get_kwarg('mode', int)
        for fname in self.get_files(self.get_args('files')):
            self.asserttype(fname, str, 'files')
            verbose('chmod(' + fname + ', ' + oct(mode) + ')')
            chmod(fname, mode)
class Tar(Task):
    from os import curdir as root
    name = None
    files = ()
    exclude = ()
    def run(self):
        from tarfile import open
        from os import sep, listdir
        from os.path import join, islink, isfile, isdir
        name = self.get_kwarg('name', str, noNone=True)
        root = self.join(self.get_kwarg('root', str))
        excludes = self.get_kwarg('exclude', (tuple, list))
        if excludes:
            exctest = lambda t, e=excludes: [v for v in e if t.endswith(v)]
            filter = lambda t, e=exctest: not e(t.name) and t or None
            exclusion = lambda t, e=exctest: e(t)
        else:
            exctest = None
            filter = None
            exclusion = None
        toadd = []
        # do not use Task.get_files()
        from glob import glob
        queue = list(self.get_args('files'))
        while queue:
            entry = queue[0]
            del queue[0]
            for fn in glob(self.join(root, entry)):
                if exctest and exctest(fn):  # if true, then ignore
                    pass
                elif islink(fn) or isfile(fn):
                    toadd.append(fn)
                elif isdir(fn):
                    fnames = [join(fn, f) for f in listdir(fn)]
                    queue.extend(fnames)
        file = open(self.join(name), 'w:gz')
        for fname in toadd:
            fn = fname.replace(
                root + sep, ''
            )
            verbose('tar.add(' +
                    str(fname) + ', ' +
                    str(fn) + ')'
            )
            file.add(fname, fn)
        file.close()
class Untar(Task):
    name = None
    root = None
    files = ()
    def run(self):
        from tarfile import open
        from os import pardir, sep
        from os.path import join
        name = self.get_kwarg('name', str, noNone=True)
        root = self.get_kwarg('root', str)
        self.asserttype(root, str,'root')
        files = tuple(self.get_args('files'))
        file = open(name, 'r:gz')
        fileset = []
        for member in file.getmembers():
            if member.name.startswith(sep) or member.name.startswith(pardir):
                pass
            elif not files or member.name in files:
                fileset.append(member)
        for fileinfo in fileset:
            verbose('tar.extract(' + str(fileinfo.name) + ')')
            file.extract(fileinfo, path=(root or ""))
        file.close()
class Zip(Task):
    from os import curdir as root
    name = None
    files = ()
    exclude = ()
    def run(self):
        from zipfile import ZipFile
        from os import listdir, sep
        from os.path import isdir, isfile, islink, join
        name = self.get_kwarg('name', str, noNone=True)
        root = self.join(self.get_kwarg('root', str))
        excludes = tuple(self.get_kwarg('exclude', (tuple, list)))
        files = tuple(self.get_args('files'))
        if excludes:
            exctest = lambda t, e=excludes: [v for v in e if t.endswith(v)]
            filter = lambda t, e=exctest: not e(t.name) and f or None
            exclusion = lambda t, e=exctest: e(t)
        else:
            exctest = None
            filter = None
            exclusion = None
        toadd = []
        # do not use Task.get_files()
        from glob import glob
        queue = list(files)
        while queue:
            entry = queue[0]
            del queue[0]
            for fn in glob(self.join(root, entry)):
                if exctest and exctest(fn): # if true then ignore
                    pass
                elif islink(fn) or isfile(fn):
                    toadd.append(fn)
                elif isdir(fn):
                    files = [join(fn, f) for f in listdir(fn)]
                    queue.extend(files)
        file = ZipFile(self.join(name), 'w')
        for fname in toadd:
            fn = fname.replace(
                root + sep, ''
            )
            verbose('zip.add(' + str(fname) + ', ' + str(fn) + ')' )
            file.write(fname, fn)
        file.close()
class Unzip(Task):
    name = None
    root = None
    files = ()
    def run(self):
        from zipfile import ZipFile
        from os import pardir, sep
        from os.path import dirname, join
        name = self.get_kwarg('name', str, noNone=True)
        root = self.get_kwarg('root', str)
        files = tuple(self.get_args('files'))
        file = ZipFile(name, 'r')
        fileset = []
        for member in file.namelist():
            if member.startswith(sep) or member.startswith(pardir):
                pass
            elif not files or member in files:
                fileset.append(member)
        for member in fileset:
            dname = join(root, member)
            Mkdir.mkdir(dirname(dname))
            verbose('zip.extract(' + str(member) + ')')
            dfile = open(dname, 'wb')
            dfile.write(file.read(member))
        file.close()
class Java(Task):
    from os import environ
    java_home = environ['JAVA_HOME']
    classpath = ()
    properties = []
    del environ
    jar = None
    def __init__(self):
        Task.__init__(self)
        from os import access, X_OK
        from os.path import expanduser, exists, join
        import os
        if exists(self.java_home):
            self.java_prog = join(self.java_home, 'bin', 'java')
        elif exists(expanduser(join('~', 'java'))):
            self.java_prog = expanduser(
                join('~', 'java', 'bin', 'java')
            )
        else:
            raise Task.Error("no java program to execute")
        if not access(self.java_prog, X_OK):
            raise Task.Error("no java program to execute")
    def addprop(self, var, val):
        self.properties.append( (var, val) )
    def run(self):
        from os import environ
        from os.path import pathsep
        jar = self.get_kwarg('jar', str, noNone=True)
        if self.properties:
            if hasformat:
                sp = ['-D{0}={1}'.format(x[0], x[1]) for x in self.properties]
            else:
                sp = ['-D%s=%s' % x for x in self.properties]
        else:
            sp = ()
        cmd = (self.java_prog,) + tuple(sp) + ('-jar', jar,) + \
            tuple([str(s) for s in self.args])
        env = environ.copy()
        if self.classpath:
            env['CLASSPATH'] = pathsep.join(self.classpath)
        Spawn()(
            cmd,
            env=env,
        )
class Unittest(Task):
    modules = ()
    path = ()
    def run(self):
        modules = tuple(self.get_args('modules'))
        import imp, unittest
        from sys import argv
        from os.path import realpath
        loader = unittest.loader.TestLoader()
        runner = unittest.runner.TextTestRunner()
        real_sys_name = argv[0]
        try:
            path = [realpath(p) for p in self.path]
            if not path:
                path = ['.']
            for modname in modules:
                argv[0] = modname
                packet = imp.find_module(modname, path)
                mod = imp.load_module(modname, *packet)
                tests = loader.loadTestsFromModule(mod)
                runner.run(tests)
        finally:
            argv[0] = real_sys_name

# standard targets

class Help(Target):
    """This information"""
    def run(self):
        for name, obj in sorted(self.get_targets().items()):
            if hasformat:
                print('{0:20}  {1}'.format(
                        obj.__name__.lower(),
                        obj.__doc__ or ""
                    )
                )
            else:
                print('%-20s  %s' % (obj.__name__.lower(), obj.__doc__ or ""))
class Clean(Target):
    """Clean directories and files used by the build"""
    files = ()
    def run(self):
        Remove(basedir=self.basedir)(*self.files)
class InitDirs(Target):
    """Create initial directories"""
    files = ()
    def run(self):
        Mkdir(basedir=self.basedir)(*self.files)
class Init(Target):
    """Initialize the build."""
    dependencies = ("InitDirs",)
class Compile(Target):
    """Do something interesting."""
    # meant to be overriden
class Build(Target):
    """The primary build."""
    dependencies = ("Init", "Compile")
class Packaging(Target):
    """Do something interesting."""
    # meant to be overriden
class Dist(Target):
    """The primary packaging."""
    dependencies = ("Build", "Packaging")
    # may be overriden
class Test(Target):
    """Run (unit)tests."""
    tasks = ("Unittest",)
# default target
class All(Target):
    """Do it all"""
    dependencies = ("Clean", "Dist", "Test")
class Default(Target):
    dependencies = ("Dist",)

#@unittest.skip('conflict with other TestCase classes')
class TestStandardTargets: #(unittest.TestCase):
    long_output = """\
InitDirs: done.
Init: done.
Compile: done.
Build: done.
Packaging: done.
Dist: done.
"""
    clean_output = """\
Clean: done.
"""
    default_output = """\
Default: done.
"""
    all_output = """\
All: done.
"""
    def setUp(self):
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        self.stream = StringIO
        self.real_stream = verbose.stream
        verbose.stream = self.stream
    def tearDown(self):
        verbose.stream = self.real_stream
    def test_all(self):
        pymain("all")
        output = self.stream.getvalue()
        long_output = self.clean_output + self.long_output + self.all_output
        short_output = self.clean_output + self.all_output
        if output == long_output:
            self.assertEqual(output, long_output)
        elif output == short_output:
            self.assertEqual(output, short_output)
        else:
            self.assertEqual(output, '')
    def test_default(self):
        pymain("default")
        output = self.stream.getvalue()
        long_output = self.long_output + self.default_output
        short_output = self.default_output
        if output == long_output:
            self.assertEqual(output, long_output)
        elif output == short_output:
            self.assertEqual(output, short_output)
        else:
            self.assertEqual(output, '')
# test code
def test():
    from os.path import join
    import os, tempfile
    from sys import exc_info
    try:
        tmpdir = tempfile.mkdtemp('.d', 'pymake')
    except OSError:
        e = exc_info()[1]
        raise SystemExit(e)
    else:
        try:
            Target.allow_reexec = True
            # setup
            class Foobar_utd(Uptodate):
                sources = ('foobar',)
                destinations = (join('build', 'foobar'),)
            class DistTar_utd(Uptodate):
                sources = ('foobar',)
                destinations = (join('dist', 'xyzzy.tgz'),)
            class Compile(Target):
                uptodates = ('Foobar_utd',)
                def run(self):
                    Copy()(
                        'foobar',
                        dest=join('build', 'foobar')
                    )
            class DistTar_t(Tar):
                name = join('dist', 'xyzzy.tgz')
                root = 'build'
                files = ('foobar',)
            symbols_to_global(Foobar_utd, DistTar_utd, DistTar_t, Compile)
            # end setup
            f = open(join(tmpdir, 'foobar'), 'w')
            f.write("""\
This is a story,
Of a lovely lady,
With three very lovely girls.
""")
            f.close()
            Packaging.tasks = ('DistTar_t',)
            Packaging.uptodates = ('DistTar_utd',)
            Clean.files = ('build', 'dist')
            InitDirs.files = ('build', 'dist')
            tmpdiropt = '--directory=' + str(tmpdir)
            debug('pymain("-v", "' + tmpdiropt + '", "clean")')
            pymain('-v', tmpdiropt, 'clean')
            if debug:
                os.system('ls -lAtr ' + str(tmpdir))
            debug('pymain("-v", "' + tmpdiropt + '")')
            pymain('-v', tmpdiropt) # default
            if debug:
                os.system('ls -lAtr ' + str(tmpdir))
            debug('pymain("-v", "' + tmpdiropt + '")')
            pymain('-v', tmpdiropt) # default with uptodate
            if debug:
                os.system('ls -lAtr ' + str(tmpdir))
        finally:
            Remove()(tmpdir)

def get_version():
    return _RCS_VERSION.replace('Revision: ', '').replace('$', '')

if __name__ == '__main__':
    from os.path import splitext, basename
    from sys import argv
    progname = splitext(basename(argv[0]))[0]
    if len(argv) == 1 or argv[1] == 'help':
        print(progname, 'help|version|test|unit')
    elif argv[1] == 'version':
        print(progname, get_version())
    elif argv[1] == 'test':
        test()
    elif argv[1] == 'unit':
        argv[1:] = []
        unittest.main()
    else:
        print('Error: %s: Invalid argument: %s' % (progname, argv[1]))
