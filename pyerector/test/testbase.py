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

from .base import *

PyVersionCheck()

from pyerector import normjoin, verbose, display, debug, noop
from pyerector.helper import normjoin, Verbose
from pyerector.exception import Error
from pyerector.base import Initer, Target, Task, Iterator
from pyerector.targets import *
from pyerector.tasks import *
from pyerector.iterators import Uptodate
from pyerector.variables import V

class TestIniter(TestCase):
    def test_basedir(self):
        #obj = Initer()
        #self.assertEqual(V['basedir'], os.path.realpath(os.getcwd()))
        obj = Initer(basedir=self.dir)
        self.assertEqual(V['basedir'], self.dir)
    def test_join(self):
        #"""Ensure that join() method returns proper values."""
        obj = Initer(basedir=self.dir)
        self.assertEqual(obj.join('foobar'),
                         normjoin(self.dir, 'foobar'))
        self.assertEqual(obj.join('xyzzy', 'foobar'),
                         normjoin(self.dir, 'xyzzy', 'foobar'))
    def test_asserttype(self):
        obj = Initer(basedir=self.dir)
        if hasattr(self, 'assertIsNone'):
            self.assertIsNone(obj.asserttype('foo', str, 'foobar'))
        else:
            self.assertEqual(obj.asserttype('foo', str, 'foobar'), None)
        for test in (('foo', int, 'name'), (1, str, 'foobar')):
            self.assertRaises(AssertionError, obj.asserttype, *test)
        with self.assertRaises(AssertionError) as cm:
            obj.asserttype(1, str, 'foobar')
        exc = cm.exception
        self.assertEqual(str(exc), "Must supply str to 'foobar' in 'Initer'")
    def test_get_files_simple(self):
        #"""Retrieve files in basedir properly."""
        subdir = normjoin(self.dir, 'get_files_simple')
        os.mkdir(subdir)
        obj = Initer(basedir=subdir)
        # no files
        self.assertEqual(list(obj.get_files(('*',))), [])
        for n in ('bar', 'far', 'tar'):
            fn = normjoin(subdir, '%s' % n)
            open(fn, 'w').close()
        logger.debug('files in %s are %s', subdir, os.listdir(subdir))
        # test simple glob
        self.assertEqual(sorted(obj.get_files(('*',))),
                         ['bar',
                          'far',
                          'tar'])
        # test single file
        self.assertEqual(list(obj.get_files(('bar',))),
                         ['bar'])
        # test single file, no glob
        obj.noglob=True
        self.assertEqual(list(obj.get_files(('tar',))),
                         ['tar'])
        obj.noglob=False
        # test simple file tuple, with glob
        self.assertEqual(sorted(obj.get_files(('bar', 'tar'))),
                         ['bar',
                          'tar'])
        # test glob file tuple, with glob
        self.assertEqual(sorted(obj.get_files(('bar', 't*'))),
                         ['bar',
                          'tar'])
    #@unittest.skip('noglob not working from this level')
    def _test_get_files_noglob(self):
        #"""Retrieve files in basedir properly."""
        subdir = normjoin(self.dir, 'get_files_noglob')
        os.mkdir(subdir)
        obj = Initer(basedir=subdir)
        #open(normjoin(self.dir, subdir, 'get_files_simple-*'), 'wt')
        open(normjoin(subdir, 'bar'), 'wt')
        # test glob pattern against noglob
        self.assertEqual(list(obj.get_files(('*',),
                                            noglob=True)),
                         ['bar', '*'])
        # test glob file tuple, no glob
        self.assertEqual(sorted(obj.get_files(('bar', 't*'),
                                              noglob=True)),
                         ['bar', 't*'])


class TestBeenCalled(Target):
    allow_reexec = False
class TestUptodate_utd(Uptodate):
    pass
class TestCallUptodate_utd(Uptodate):
    sources      = ('call_uptodate.older',)
    destinations = ('call_uptodate.newer',)
class TestCallUptodate_T(Target):
    uptodates = (TestCallUptodate_utd,)
class TestCallTask_t(Task):
    def run(self):
        logger.debug('Creating %s', self.join(self.args[0]))
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
        #from time import sleep
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

class TestTarget_basics(TestCase):
    maxDiff = None
    def setUp(self):
        self.realstream = verbose.stream
        verbose.stream = StringIO()
        display.stream = verbose.stream
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
        self.assertEqual(verbose.stream.getvalue(), 'Target: hi there' + os.linesep)
        display.stream = StringIO()
        target.verbose('hi', 'there')
        self.assertEqual(verbose.stream.getvalue(), 'Target: hi there' + os.linesep)

class TestTarget_functionality(TestCase):
    def test_nothing(self):
        class NothingTarget(Target):
            pass
        target = NothingTarget(basedir=self.dir)
        self.assertIsNone(NothingTarget.validate_tree())
        self.assertIsNone(target())
    def test_call_uptodate(self):
        open(normjoin(self.dir, 'call_uptodate.older'), 'w').close()
        open(normjoin(self.dir, 'call_uptodate.newer'), 'w').close()
        utd = TestCallUptodate_utd(basedir=self.dir)
        result = utd()
        self.assertTrue(result)
        target = TestCallUptodate_T(basedir=self.dir)
        self.assertTrue(target.call(TestCallUptodate_utd, Uptodate, 'uptodate'))
    def test_call_task(self):
        self.assertFalse(os.path.isfile(normjoin(self.dir, 'calltask')))
        target = TestCallTask_T(basedir=self.dir)
        self.assertIsNone(target.call(TestCallTask_t, Task, 'task', ('calltask',)))
        self.assertTrue(os.path.isfile(normjoin(self.dir, 'calltask')))
    def test_call_dependency(self):
        self.assertFalse(os.path.isfile(normjoin(self.dir, 'calldependency')))
        target = TestCallDependency_T(basedir=self.dir)
        self.assertIsNone(target.call(TestCallDependency_T, Target, 'dependencies'))
        self.assertTrue(os.path.isfile(normjoin(self.dir, 'calldependency')))
    def test_end_to_end(self):
        self.assertFalse(os.path.isfile(normjoin(self.dir, 'e2e_t1')))
        self.assertFalse(os.path.isfile(normjoin(self.dir, 'e2e_t2')))
        target = TestE2E_T(basedir=self.dir)
        self.assertIsNone(target())
        self.assertTrue(os.path.isfile(normjoin(self.dir, 'e2e_t1')))
        self.assertTrue(os.path.isfile(normjoin(self.dir, 'e2e_t2')))
        t1 = os.path.getmtime(normjoin(self.dir, 'e2e_t1'))
        t2 = os.path.getmtime(normjoin(self.dir, 'e2e_t2'))
        # maybe change the mtime of one then other to test uptodate?
        target = TestE2E_T(basedir=self.dir)
        self.assertIsNone(target())
        # not testing what I think should be tested
        self.assertEqual(round(t1, 4),
            round(os.path.getmtime(normjoin(self.dir, 'e2e_t1')), 4)
        )
        self.assertEqual(round(t2, 4),
            round(os.path.getmtime(normjoin(self.dir, 'e2e_t2')), 4)
        )

class TestTask(TestCase):
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
        self.assertRaises(ValueError, ValueErrorTask())
    def test_noop(self):
        try:
            from io import StringIO
        except ImportError:
            from StringIO import StringIO
        old_noop = noop.state
        try:
            noop.on()
            self.assertTrue(bool(noop))
            class NoopTask(Task):
                foobar = False
                def run(self):
                    self.foobar = True
            obj = NoopTask()
            obj()
            self.assertFalse(obj.foobar)
        finally:
            noop.state = old_noop

