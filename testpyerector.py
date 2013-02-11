#!/usr/bin/python
# Copyright @ 2010-2012 Michael P. Reilly. All rights reserved.

import unittest
from pyerector import *
from pyerector import _Initer, normjoin, Verbose, verbose, debug, Config, noop

class Test_Initer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tempfile import mkdtemp
        cls.dir = mkdtemp()
        #cls.oldconfigbasedir = _Initer.config.basedir
        #_Initer.config.basedir = cls.dir
    @classmethod
    def tearDownClass(cls):
        from shutil import rmtree
        rmtree(cls.dir)
        #_Initer.config.basedir = cls.oldconfigbasedir
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
    @unittest.skip('issue with config.basedir')
    def test_basedir(self):
        from os import curdir, getcwd
        from os.path import realpath
        #_Initer.config.basedir = self.oldconfigbasedir
        obj = _Initer()
        self.assertEqual(obj.config.basedir, realpath(getcwd()))
        _Initer.config.initialized = False
        obj = _Initer(basedir=self.dir)
        self.assertEqual(obj.config.basedir, self.dir)
        #_Initer.config.basedir = self.dir
    @unittest.skip('issue with config.basedir')
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
    @unittest.skip('issue with config.basedir')
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
                         [normjoin(self.dir, subdir, 'get_files_simple-bar'),
                          normjoin(self.dir, subdir, 'get_files_simple-far'),
                          normjoin(self.dir, subdir, 'get_files_simple-tar')])
        # test glob pattern against noglob
        self.assertEqual(obj.get_files(('get_files_simple-*',), noglob=True),
                         [normjoin(self.dir, subdir, 'get_files_simple-*')])
        # test single file
        self.assertEqual(obj.get_files(('get_files_simple-bar',)),
                         [normjoin(self.dir, subdir, 'get_files_simple-bar')])
        # test single file, no glob
        self.assertEqual(obj.get_files(('get_files_simple-tar',), noglob=True),
                         [normjoin(self.dir, subdir, 'get_files_simple-tar')])
        # test simple file tuple, with glob
        self.assertEqual(sorted(obj.get_files(('get_files_simple-bar', 'get_files_simple-tar'))),
                         [normjoin(self.dir, subdir, 'get_files_simple-bar'),
                          normjoin(self.dir, subdir, 'get_files_simple-tar')])
        # test glob file tuple, with glob
        self.assertEqual(sorted(obj.get_files(('get_files_simple-bar', 'get_files_simple-t*'))),
                         [normjoin(self.dir, subdir, 'get_files_simple-bar'),
                          normjoin(self.dir, subdir, 'get_files_simple-tar')])
        # test globl file tuple, no glob
        self.assertEqual(sorted(obj.get_files(('get_files_simple-bar', 'get_files_simple-t*'),
                                              noglob=True)),
                         [normjoin(self.dir, subdir, 'get_files_simple-bar'),
                          normjoin(self.dir, subdir, 'get_files_simple-t*')])
    @unittest.skip('issue with config.basedir')
    def test_get_files_subdir(self):
        from os import mkdir, curdir
        obj = _Initer(basedir=self.dir)
        # test subdir value
        subdir = 'subdir'
        mkdir(normjoin(self.dir, subdir))
        open(normjoin(self.dir, subdir, 'get_files_subdir-par'), 'w').close()
        open(normjoin(self.dir, subdir, 'get_files_subdir-rar'), 'w').close()
        self.assertEqual(sorted(obj.get_files(('get_files_subdir-*',),
                                              subdir=subdir)),
                         [normjoin(self.dir, subdir, 'get_files_subdir-par'),
                          normjoin(self.dir, subdir, 'get_files_subdir-rar')])
        self.assertEqual(sorted(obj.get_files(('get_files_subdir-par',
                                               'get_files_subdir-rar'),
                                              subdir=subdir)),
                         [normjoin(self.dir, subdir, 'get_files_subdir-par'),
                          normjoin(self.dir, subdir, 'get_files_subdir-rar')])
        self.assertEqual(obj.get_files(('get_files_subdir-par',),
                                       noglob=True,
                                       subdir=subdir),
                         [normjoin(self.dir, subdir, 'get_files_subdir-par')])

class TestUptodate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.dir = tempfile.mkdtemp()
        cls.oldconfigbasedir = _Initer.config.basedir
        _Initer.config.basedir = cls.dir
    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.dir)
        _Initer.config.basedir = cls.oldconfigbasedir
    def test_older(self):
        #"""Test that newer files indeed do trigger the test."""
        import os, time
        older = normjoin(self.dir, 'older-older')
        newer = normjoin(self.dir, 'older-newer')
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
        older = normjoin(self.dir, 'newer-older')
        newer = normjoin(self.dir, 'newer-newer')
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
        older = normjoin(self.dir, 'same-older')
        newer = normjoin(self.dir, 'same-newer')
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
        older_d = normjoin(self.dir, 'multi_older-older')
        newer_d = normjoin(self.dir, 'multi_older-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, then), (newer_d, now)):
            for i in range(0, 3):
                fn = normjoin(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertTrue(utd())
    def test_multi_newer(self):
        import os, time
        older_d = normjoin(self.dir, 'multi_newer-older')
        newer_d = normjoin(self.dir, 'multi_newer-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, now), (newer_d, then)):
            for i in range(0, 3):
                fn = normjoin(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertFalse(utd())
    def test_multi_same(self):
        import os, time
        older_d = normjoin(self.dir, 'multi_same-older')
        newer_d = normjoin(self.dir, 'multi_same-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, then), (newer_d, now)):
            for i in range(0, 11, 5):
                fn = normjoin(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertTrue(utd())
    def test_multi_mixed(self):
        import os, time
        older_d = normjoin(self.dir, 'multi_mixed-older')
        newer_d = normjoin(self.dir, 'multi_mixed-newer')
        os.mkdir(older_d)
        os.mkdir(newer_d)
        now = time.time()
        then = now - 600 # 10 minutes
        files = {older_d: [], newer_d: []}
        for dir, when in ((older_d, now), (newer_d, then)):
            for i in range(0, 16, 5):
                fn = normjoin(dir, str(i))
                files[dir].append(fn)
                open(fn, 'w').close()
                os.utime(fn, (when-(i * 60), when-(i*60)))
        utd = Uptodate(basedir=self.dir)
        utd.sources = tuple(files[older_d])
        utd.destinations = tuple(files[newer_d])
        self.assertFalse(utd())

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

class TestTarget(unittest.TestCase):
    maxDiff = None
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.dir = tempfile.mkdtemp()
        cls.oldconfigbasedir = _Initer.config.basedir
        _Initer.config.basedir = cls.dir
        Target.allow_reexec = True

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
        _Initer.config.basedir = cls.oldconfigbasedir
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
    @unittest.skip('fix after adding testpyerector.py')
    def test_been_called(self):
        target = TestBeenCalled(basedir=self.dir)
        self.assertFalse(target.been_called)
        target()
        self.assertTrue(target.been_called)
    @unittest.skip('fix names after adding testpyerector.py')
    def test_get_uptodates(self):
        global TestUptodate_utd
        import __main__
        result = Target.get_uptodates()
        self.assertEqual(Target.get_uptodates(), self.uptodate_classes)
    @unittest.skip('fix names after adding testpyerector.py')
    def test_get_targets(self):
        self.assertEqual(Target.get_targets(), self.target_classes)
    @unittest.skip('fix names after adding testpyerector.py')
    def test_get_tasks(self):
        self.assertEqual(Target.get_tasks(), self.task_classes)
    def test_verbose(self):
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        target = Target(basedir=self.dir)
        target.stream = StringIO()
        target.verbose('hi there')
        self.assertEqual(target.stream.getvalue(), 'Target: hi there\n')
        target.stream = StringIO()
        target.verbose('hi', 'there')
        self.assertEqual(target.stream.getvalue(), 'Target: hi there\n')
    def test_nothing(self):
        class NothingTarget(Target):
            pass
        target = NothingTarget(basedir=self.dir)
        self.assertIsNone(NothingTarget.validate_tree())
        self.assertIsNone(target())
    @unittest.skip('issue with new org')
    def test_call_uptodate(self):
        import __main__, tempfile, time
        from os.path import join, isfile
        open(join(self.dir, 'call_uptodate.older'), 'w').close()
        #time.sleep(1)
        open(join(self.dir, 'call_uptodate.newer'), 'w').close()
        self.assertTrue(TestCallUptodate_utd(basedir=self.dir)())
        target = TestCallUptodate_T(basedir=self.dir)
        self.assertTrue(target.call_uptodate('TestCallUptodate_utd'))
    @unittest.skip('issue with new org')
    def test_call_task(self):
        import os
        from os.path import join, isfile
        self.assertFalse(isfile(join(self.dir, 'calltask')))
        target = TestCallTask_T(basedir=self.dir)
        self.assertIsNone(target.call_task("TestCallTask_t", ('calltask',)))
        self.assertTrue(isfile(join(self.dir, 'calltask')))
    @unittest.skip('issue with new org')
    def test_call_dependency(self):
        from os.path import join, isfile
        self.assertFalse(isfile(join(self.dir, 'calldependency')))
        target = TestCallDependency_T(basedir=self.dir)
        self.assertIsNone(target.call_dependency("TestCallDependency_T"))
        self.assertTrue(isfile(join(self.dir, 'calldependency')))
    @unittest.skip('issue with new org')
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

class TestTask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.dir = tempfile.mkdtemp()
        cls.oldconfigbasedir = _Initer.config.basedir
        _Initer.config.basedir = cls.dir
    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.dir)
        _Initer.config.basedir = cls.oldconfigbasedir
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
        if debug:
            self.assertRaises(ValueError, ValueErrorTask())
        else:
            self.assertRaises(Task.Error, ValueErrorTask())
    def test_noop(self):
        import pyerector
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        old_noop = pyerector.noop
        try:
            pyerector.noop = Verbose()
            pyerector.noop.on()
            pyerector.noop.stream = StringIO()
            self.assertTrue(pyerector.noop)
            class NoopTask(Task):
                foobar = False
                def run(self):
                    self.foobar = True
            obj = NoopTask()
            obj()
            self.assertFalse(obj.foobar)
            self.assertEqual(pyerector.noop.stream.getvalue(),
                             'Calling NoopTask(*(), **{})\n')
        finally:
            pyerector.noop = old_noop

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
        PyErector("all")
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
        PyErector("default")
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
            debug('PyErector("-v", "' + tmpdiropt + '", "clean")')
            PyErector('-v', tmpdiropt, 'clean')
            if debug:
                os.system('ls -lAtr ' + str(tmpdir))
            debug('PyErector("-v", "' + tmpdiropt + '")')
            PyErector('-v', tmpdiropt) # default
            if debug:
                os.system('ls -lAtr ' + str(tmpdir))
            debug('PyErector("-v", "' + tmpdiropt + '")')
            PyErector('-v', tmpdiropt) # default with uptodate
            if debug:
                os.system('ls -lAtr ' + str(tmpdir))
        finally:
            Remove()(tmpdir)

