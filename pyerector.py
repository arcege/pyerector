#!/usr/bin/python
# Copyright @ 2010 Michael P. Reilly. All rights reserved.
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
  'Build', 'Compile', 'Dist', 'Packaging',
  # tasks
  'Task', 'Spawn', 'Remove', 'Copy', 'CopyTree', 'Mkdir', 'Chmod', 'Java',
  'Shebang', 'Tar', 'Untar', 'Zip', 'Unzip',
]

Config = {
    'initialized': False,
    'basedir': None,
}

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

# the main program, to be called by pyerect program
def pymain(*args):
    global verbose, noop
    showhelp = False
    from sys import argv, exc_info
    # need to "import __main__" and not "from __main__ import Default"
    import getopt
    basedir = None
    targets = []
    try:
        opts, args = getopt.getopt(args or argv[1:], 'd:hNv', [
                'directory=', 'dry-run', 'help', 'verbose',
            ]
        )
    except getopt.error:
        e = exc_info()[1]
        raise SystemExit(e)
    else:
        for opt, val in opts:
            if opt == '--':
                break
            elif opt in ('-h', '--help'):
                showhelp = True
            elif opt in ('-d', '--directory'):
                basedir = val
            elif opt in ('-N', '--dry-run'):
                noop.on()
            elif opt in ('-v', '--verbose'):
                verbose.on()
            else:
                raise SystemExit('invalid option: ' + str(opt))
    # map arguments into classes above: e.g. 'all' into All
    if showhelp:
        import __main__
        targets[:] = [__main__.Help]
    elif len(args) == 0:
        try:
            import __main__
            targets.append(__main__.Default)
        except AttributeError:
            raise SystemExit('Must supply at least a Default target')
    else:
        all_targets = Target.get_targets()
        for name in args:
            try:
                obj = all_targets[name.capitalize()]
            except KeyError:
                raise SystemExit('Error: unknown target: ' + str(name))
            else:
                if not issubclass(obj, Target):
                    raise SystemExit('Error: unknown target: ' + str(name))
                targets.append(obj)
    # validate the dependency tree, make sure that all are subclasses of
    # Target, validate all Uptodate values and all Task values
    for target in targets:
        try:
            target.validate_tree()
        except ValueError:
            if not debug:
                e = exc_info()[1]
                raise SystemExit('Error: ' + str(e))
            else:
                raise
    # run all the targets in the tree of each argument
    for target in targets:
        try:
            target(basedir=basedir)()
        except target.Error:
            if not debug:
                e = exc_info()[1]
                raise SystemExit(e)
            else:
                raise
        except KeyboardInterrupt:
            if not debug:
                e = exc_info()[1]
                raise SystemExit(e)
            else:
                raise
        except AssertionError:
            if not debug:
                e = exc_info()[1]
                raise SystemExit('AssertionError: %s' % e)
            else:
                raise

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
    global Config
    config = Config
    from os import curdir
    def __init__(self, basedir=None, curdir=curdir):
        from os.path import normpath, realpath
        if basedir is None:
            basedir = curdir
        if not self.config['initialized']:
            self.config['basedir'] = normpath(realpath(basedir))
            self.config['initialized'] = True
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
            s = glob(self.join(subdir, entry))
            filelist.extend(s)
        return filelist
    def join(self, *path):
        from os.path import join
        return join(self.basedir, *path)
    def asserttype(self, value, typeval, valname):
        if isinstance(typeval, type):
            text = "Must supply %%s to '%s' in '%s'" % (valname,
                                                        self.__class__.__name__)
            assert isinstance(value, typeval), text % typeval.__name__
        else:
            text = "Must supply %s to '%s' in '%s'" % (
                ' or '.join(t.__name__ for t in typeval),
                valname,
                self.__class__.__name__
            )
            for tval in typeval:
                if isinstance(value, tval):
                    break
            else:
                raise AssertionError(text)

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
        try:
            _Initer.config = Config.copy()
            _Initer.config['initialized'] = False
            self.assertFalse(_Initer.config['initialized'])
            obj = _Initer()
            self.assertTrue(_Initer.config['initialized'])
        finally:
            _Initer.config = Config
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
    validate_tree = classmethod(validate_tree)
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
    get_tasks = staticmethod(get_tasks)
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
    get_targets = staticmethod(get_targets)
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
    get_uptodates = staticmethod(get_uptodates)

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
            'Init': Init, 'InitDirs': InitDirs, 'Clean': Clean,
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
            'CopyTree': CopyTree, 'Copy': Copy,
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
        global Config
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
    cmd = ''
    infile = None
    outfile = None
    errfile = None
    def run(self):
        if self.args:
            cmd = self.args[0]
        else:
            cmd = self.cmd
        if 'infile' in self.kwargs:
            infile = self.kwargs['infile']
        else:
            infile = self.infile
        if 'outfile' in self.kwargs:
            outfile = self.kwargs['outfile']
        elif len(self.args) > 1:
            outfile = self.args[1]
        else:
            outfile = self.outfile
        if 'errfile' in self.kwargs:
            errfile = self.kwargs['errfile']
        elif len(self.args) > 2:
            errfile = self.args[2]
        else:
            errfile = self.errfile
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
            verbose('spawn("' + str(cmd) + '")')
            rc = call(cmd, shell=True, stdin=ifl, stdout=of, stderr=ef, bufsize=0)
            if rc < 0:
                raise self.Error(str(self), 'signal ' + str(abs(rc)) + 'raised')
            elif rc > 0:
                raise self.Error(str(self), 'returned error + ' + str(rc))
            pass
        except ImportError:
            from popen2 import Popen3
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
        for fname in self.get_files(self.args or None, self.noglob):
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
        if 'dest' in self.kwargs:
            dst = self.kwargs['dest']
        elif not self.dest:
            raise Task.Error('configuration error: Copy missing destination')
        else:
            dst = self.dest
        self.asserttype(dst, str, 'dest')
        dst = self.join(dst)
        if self.args:
            srcs = self.get_files(self.args, noglob=self.wantnoglob())
        else:
            srcs = self.get_files(self.files, noglob=self.wantnoglob())
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
        if 'program' in self.kwargs:
            program = self.kwargs['program']
            self.asserttype(program, str, 'program')
        else:
            raise Task.Error('No program value supplied')
        if self.args:
            srcs = self.get_files(self.args, noglob=self.wantnoglob())
        else:
            srcs = self.get_files(self.files, noglob=self.wantnoglob())
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
        if self.args:
            srcdir, dstdir = self.args
        else:
            srcdir, dstdir = self.srcdir, self.dstdir
        self.asserttype(srcdir, str, 'srcdir')
        self.asserttype(dstdir, str, 'dstdir')
        if not srcdir or not exists(self.join(srcdir)):
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
        for arg in (self.args or self.files):
            self.asserttype(arg, str, 'files')
            self.mkdir(self.join(arg))
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
    mkdir = classmethod(mkdir)
class Chmod(Task):
    files = ()
    mode = int('666', 8) # gets around Python 2.x vs 3.x octal issue
    def run(self):
        from os import chmod
        if 'mode' in self.kwargs:
            mode = self.kwargs['mode']
        else:
            mode = self.mode
        self.asserttype(mode, int, 'mode')
        if self.args:
            files = self.args
        else:
            files = self.files
        self.asserttype(files, (tuple, list), 'files')
        for fname in self.get_files(files):
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
        if 'name' in self.kwargs:
            name = self.kwargs['name']
        else:
            name = self.name
        if 'root' in self.kwargs:
            root = self.kwargs['root']
        else:
            root = self.root
        if name is not None:
            self.asserttype(name, str, 'name')
        else:
            raise ValueError("no 'name' for '%s'" % self.__class__.__name__)
        self.asserttype(root, str, 'root')
        root = self.join(root)
        if self.args:
            files = tuple(self.args)
        else:
            files = tuple(self.files)
        if 'exclude' in self.kwargs:
            excludes = self.kwargs['exclude']
        else:
            excludes = self.exclude
        self.asserttype(excludes, (tuple, list), 'exclude')
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
        queue = list(files)
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
        if self.args:
            name, root = self.args[0], self.args[1]
            files = tuple(self.args[2:])
        else:
            name, root, files = self.name, self.root, self.files
        self.asserttype(name, str, 'name')
        self.asserttype(root, str, 'root')
        self.asserttype(files, (tuple, list), 'files')
        file = open(tarname, 'r:gz')
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
        return True
class Zip(Task):
    def zip(self, zipname, root, *files):
        from zipfile import ZipFile
        from os.path import join
        file = ZipFile(zipname, 'w')
        for filename in files:
            verbose('zip.add(' + str(join(root, filename)) + ')')
            file.write(join(root, filename), filename)
        file.close()
class Unzip(Task):
    def unzip(self, zipname, root, *files):
        from zipfile import ZipFile
        from os import pardir, sep
        from os.path import dirname, join
        file = open(zipname, 'r')
        fileset = []
        for member in file.namelist():
            if member.startswith(sep) or member.startswith(pardir):
                pass
            elif not files or member in files:
                fileset.append(member)
        for member in fileset:
            dname = join(root, member)
            self.mkdir(dirname(dname))
            dfile = open(dname, 'wb')
            dfile.write(file.read(member))
        file.close()
class Java(Task):
    from os import environ
    java_home = environ['JAVA_HOME']
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
        if 'jar' in self.kwargs:
            jar = self.kwargs['jar']
        else:
            jar = self.jar
        self.asserttype(jar, str, 'jar')
        if self.properties:
            if hasformat:
                sp = ' ' + ' '.join(
                    ['-D{0}={1}'.format(x[0], x[1]) for x in self.properties]
                )
            else:
                sp = ' ' + ' '.join(['-D%s=%s' % x for x in self.properties])
        else:
            sp = ''
        if hasformat:
            cmd = '{prog}{sp} -jar {jar} {args}'.format(
                prog=self.java_prog, sp=sp, jar=jar,
                args=' '.join([str(s) for s in self.args])
            )
        else:
            cmd = '%s%s -jar %s %s' % (
                self.java_prog, sp, jar, ' '.join([str(s) for s in self.args])
            )
        Spawn()(
            cmd
        )

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
# default target
class All(Target):
    """Do it all"""
    dependencies = ("Clean", "Dist")
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
