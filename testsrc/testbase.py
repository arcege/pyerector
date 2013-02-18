#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import shutil
import sys
import tempfile
import time
import unittest
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from pyerector import normjoin, verbose, debug, noop
from pyerector.helper import Verbose
from pyerector.config import Config
from pyerector.exception import Error
from pyerector.base import Initer, Target, Task, Uptodate
from pyerector.targets import *
from pyerector.tasks import *

class TestIniter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.oldconfigbasedir = Initer.config.basedir
        Initer.config.basedir = cls.dir
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)
        Initer.config.basedir = cls.oldconfigbasedir
    def test_initialized(self):
        #"""Is system initialized on first instantiation."""
        old_config = Initer.config
        try:
            Initer.config = Config()
            Initer.config.initialized = False
            self.assertFalse(Initer.config.initialized)
            obj = Initer()
            self.assertTrue(Initer.config.initialized)
        finally:
            Initer.config = old_config
    @unittest.skip('issue with config.basedir')
    def test_basedir(self):
        #Initer.config.basedir = self.oldconfigbasedir
        obj = Initer()
        self.assertEqual(obj.config.basedir, os.path.realpath(os.getcwd()))
        Initer.config.initialized = False
        obj = Initer(basedir=self.dir)
        self.asertTrue(obj.config.initialized)
        self.assertEqual(obj.config.basedir, self.dir)
        #Initer.config.basedir = self.dir
    @unittest.skip('issue with config.basedir')
    def test_join(self):
        #"""Ensure that join() method returns proper values."""
        obj = Initer(basedir=self.dir)
        self.assertEqual(obj.join('foobar'),
                         os.path.join(self.dir, 'foobar'))
        self.assertEqual(obj.join('xyzzy', 'foobar'),
                         os.path.join(self.dir, 'xyzzy', 'foobar'))
    def test_asserttype(self):
        obj = Initer(basedir=self.dir)
        self.assertIsNone(obj.asserttype('foo', str, 'foobar'))
        for test in (('foo', int, 'name'), (1, str, 'foobar')):
            self.assertRaises(AssertionError, obj.asserttype, *test)
        with self.assertRaises(AssertionError) as cm:
            obj.asserttype(1, str, 'foobar')
        exc = cm.exception
        self.assertEqual(str(exc), "Must supply str to 'foobar' in 'Initer'")
    @unittest.skip('issue with config.basedir')
    def test_get_files_simple(self):
        #"""Retrieve files in basedir properly."""
        obj = Initer(basedir=self.dir)
        # no files
        self.assertEqual(obj.get_files(('get_files_simple-*',)), [])
        subdir = os.curdir
        for n in ('bar', 'far', 'tar'):
            fn = os.path.join(self.dir, subdir, 'get_files_simple-%s' % n)
            open(fn, 'w').close()
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
        obj = Initer(basedir=self.dir)
        # test subdir value
        subdir = 'subdir'
        os.mkdir(normjoin(self.dir, subdir))
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
        cls.dir = tempfile.mkdtemp()
        cls.oldconfigbasedir = Initer.config.basedir
        Initer.config.basedir = cls.dir
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)
        Initer.config.basedir = cls.oldconfigbasedir
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
    uptodates = (TestCallUptodate_utd,)
class TestCallTask_t(Task):
    def run(self):
        verbose('Creating', self.join(self.args[0]))
        open(self.join(self.args[0]), 'w').close()
class TestCallTask_T(Target):
    tasks = (TestCallTask_t,)
class TestCallDependency_t(Task):
    def run(self):
        open(self.join('calldependency'), 'w').close()
class TestCallDependency_T1(Target):
    tasks = (TestCallDependency_t,)
class TestCallDependency_T(Target):
    dependencies = (TestCallDependency_T1,)
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
        Target.allow_reexec = True
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)
    def setUp(self):
        self.realstream = Verbose.stream
        Verbose.stream = StringIO()
        self.realverbose = verbose.state
        self.realdebug = debug.state
    def tearDown(self):
        if hasattr(self, 'real_stream'):
            Verbose.stream = getattr(self, 'real_stream')
        debug.state = self.realdebug
        verbose.state = self.realverbose
    def test_been_called(self):
        target = TestBeenCalled(basedir=self.dir)
        self.assertFalse(target.been_called)
        target()
        self.assertTrue(target.been_called)
    def test_verbose(self):
        debug.off()
        target = Target()
        target.verbose('hi there')
        self.assertEqual(verbose.stream.getvalue(), 'Target: hi there\n')
        verbose.stream = StringIO()
        target.verbose('hi', 'there')
        self.assertEqual(verbose.stream.getvalue(), 'Target: hi there\n')
    def test_nothing(self):
        class NothingTarget(Target):
            pass
        target = NothingTarget(basedir=self.dir)
        self.assertIsNone(NothingTarget.validate_tree())
        self.assertIsNone(target())
    def test_call_uptodate(self):
        open(os.path.join(self.dir, 'call_uptodate.older'), 'w').close()
        time.sleep(1)
        open(os.path.join(self.dir, 'call_uptodate.newer'), 'w').close()
        self.assertTrue(TestCallUptodate_utd(basedir=self.dir)())
        target = TestCallUptodate_T(basedir=self.dir)
        self.assertTrue(target.call(TestCallUptodate_utd, Uptodate, 'uptodate'))
    def test_call_task(self):
        self.assertFalse(os.path.isfile(os.path.join(self.dir, 'calltask')))
        target = TestCallTask_T(basedir=self.dir)
        self.assertIsNone(target.call(TestCallTask_t, Task, 'task', ('calltask',)))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, 'calltask')))
    def test_call_dependency(self):
        self.assertFalse(os.path.isfile(os.path.join(self.dir, 'calldependency')))
        target = TestCallDependency_T(basedir=self.dir)
        self.assertIsNone(target.call(TestCallDependency_T, Target, 'dependencies'))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, 'calldependency')))
    def test_end_to_end(self):
        self.assertFalse(os.path.isfile(os.path.join(self.dir, 'e2e_t1')))
        self.assertFalse(os.path.isfile(os.path.join(self.dir, 'e2e_t2')))
        target = TestE2E_T(basedir=self.dir)
        self.assertIsNone(target())
        self.assertTrue(os.path.isfile(os.path.join(self.dir, 'e2e_t1')))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, 'e2e_t2')))
        t1 = os.path.getmtime(os.path.join(self.dir, 'e2e_t1'))
        t2 = os.path.getmtime(os.path.join(self.dir, 'e2e_t2'))
        target = TestE2E_T(basedir=self.dir)
        self.assertIsNone(target())
        self.assertEqual(round(t1, 4),
            round(os.path.getmtime(os.path.join(self.dir, 'e2e_t1')), 4)
        )
        self.assertEqual(round(t2, 4),
            round(os.path.getmtime(os.path.join(self.dir, 'e2e_t2')), 4)
        )

class TestTask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        cls.oldconfigbasedir = Initer.config.basedir
        Initer.config.basedir = cls.dir
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)
        Initer.config.basedir = cls.oldconfigbasedir
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
        self.assertRaises(Error, FailureTask())
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
            self.assertRaises(Error, ValueErrorTask())
    def test_noop(self):
        #import pyerector
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        old_noop = noop.state
        try:
            noop.on()
            noop.stream = StringIO()
            self.assertTrue(bool(noop))
            class NoopTask(Task):
                foobar = False
                def run(self):
                    self.foobar = True
            obj = NoopTask()
            obj()
            self.assertFalse(obj.foobar)
            self.assertEqual(noop.stream.getvalue(),
                             'Calling NoopTask(*(), **{})\n')
        finally:
            noop.state = old_noop

