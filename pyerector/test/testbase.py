#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.

import os
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from .base import *
except ValueError:
    import sys
    sys.path.insert(0,
            os.path.normpath(
                os.path.join(os.path.dirname(__file__),
                    os.pardir, os.pardir)))
    from base import *

PyVersionCheck()

from pyerector.path import Path
from pyerector.config import noop
from pyerector.helper import normjoin
from pyerector.exception import Error
from pyerector.base import Initer, Target, Task, Sequential
#from pyerector.targets import *
#from pyerector.tasks import *
from pyerector.iterators import Uptodate
from pyerector.variables import V


class TestIniter(TestCase):
    def test_basedir(self):
        #obj = Initer()
        #self.assertEqual(V['basedir'], os.path.realpath(os.getcwd()))
        Initer()
        self.assertEqual(V['basedir'], self.dir)

    def test_join(self):
        #"""Ensure that join() method returns proper values."""
        obj = Initer()
        self.assertEqual(obj.join('foobar'),
                         Path(self.dir, 'foobar'))
        self.assertEqual(obj.join('xyzzy', 'foobar'),
                         Path(self.dir, 'xyzzy', 'foobar'))

    def test_asserttype(self):
        obj = Initer()
        if hasattr(self, 'assertIsNone'):
            self.assertIsNone(obj.asserttype('foo', str, 'foobar'))
        else:
            self.assertEqual(obj.asserttype('foo', str, 'foobar'), None)
        for test in (('foo', int, 'name'), (1, str, 'foobar')):
            self.assertRaises(TypeError, obj.asserttype, *test)
        with self.assertRaises(TypeError) as cm:
            obj.asserttype(1, str, 'foobar')
        exc = cm.exception
        self.assertEqual(exc.args[0], 1)
        self.assertEqual(exc.args[1],
                         "Must supply str to 'foobar' in 'Initer'")

    def _test_get_files_simple(self):
        #"""Retrieve files in basedir properly."""
        fileset = ('bar', 'far', 'tar')
        subdir = Path(self.dir, 'get_files_simple')
        subdir.mkdir()
        obj = Initer(files=(subdir,), pattern='*')
        # no files
        ofiles = obj.get_files()
        #print 'ofiles =', repr(ofiles), vars(ofiles)
        self.assertEqual(list(obj.get_files(('*',))), [])
        for n in fileset:
            f = subdir + n #V['basedir'] + n  # subdir + n
            logging.error('n %s = f %s', n, f)
            f.open('w').close()
        # test simple glob
        result = obj.get_files()
        #print 'results =', repr(result), vars(result)
        self.assertEqual(sorted(result), list(fileset))
        # test single file
        self.assertEqual(list(obj.get_files(('bar',))),
                         ['bar'])
        # test single file, no glob
        obj.noglob = True
        self.assertEqual(list(obj.get_files(('tar',))),
                         ['tar'])
        obj.noglob = False
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
        obj = Initer()
        #open(normjoin(self.dir, subdir, 'get_files_simple-*'), 'wt')
        open(normjoin(subdir, 'bar'), 'wt')
        # test glob pattern against noglob
        self.assertEqual(list(obj.get_files(('*',))),
                         ['bar', '*'])
        # test glob file tuple, no glob
        self.assertEqual(sorted(obj.get_files(('bar', 't*'))),
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
    from pyerector import Touch
    tasks = (Touch('call_uptodate.newer'),)
    del Touch


class TestCallTask_t(Task):
    def run(self):
        logger.debug('Creating %s', self.join(self.args[0]))
        self.join(self.args[0]).open('w').close()


class TestCallTask_T(Target):
    tasks = (TestCallTask_t,)


class TestCallDependency_t(Task):
    def run(self):
        #self.join('calldependency').open('w').close()
        Path(V['basedir'], 'calldependency').open('w')


class TestCallDependency_T1(Target):
    tasks = (TestCallDependency_t,)


class TestCallDependency_T(Target):
    dependencies = (TestCallDependency_T1,)


class TestE2E_t1(Task):
    def run(self):
        #from time import sleep
        self.join('e2e_t1').open('w').close()
        #sleep(1)


class TestE2E_t2(Task):
    def run(self):
        self.join('e2e_t2').open('w').close()


class TestE2E_utd(Uptodate):
    sources = (Path('e2e_t1'),)
    destinations = (Path('e2e_t2'),)


class TestE2E_T(Target):
    uptodates = ('TestE2E_utd',)
    tasks = ('TestE2E_t1', 'TestE2E_t2')


class TestTarget_basics(TestCase):
    maxDiff = None

    def test_been_called(self):
        target = TestBeenCalled()
        self.assertFalse(target.been_called)
        target()
        self.assertTrue(target.been_called)


class TestTarget_functionality(TestCase):
    def test_nothing(self):

        class NothingTarget(Target):
            pass
        target = NothingTarget()
        self.assertIsNone(NothingTarget.validate_tree())
        self.assertIsNone(target())

    def _test_call_uptodate(self):
        Path(self.dir, 'call_uptodate.older').open('w').close()
        Path(self.dir, 'call_uptodate.newer').open('w').close()
        utd = TestCallUptodate_utd()
        result = utd()
        self.assertTrue(result)
        target = TestCallUptodate_T()
        self.assertTrue(TestCallUptodate_utd()())

    def test_call_task(self):
        self.assertFalse(Path(self.dir, 'calltask').isfile)
        target = TestCallTask_T()
        self.assertIsNone(TestCallTask_t()('calltask'))
        self.assertTrue(Path(self.dir, 'calltask').isfile)

    def test_call_dependency(self):
        self.assertFalse(Path(self.dir, 'calldependency').isfile)
        target = TestCallDependency_T()
        self.assertIsNone(target())
        self.assertTrue(Path(self.dir, 'calldependency').isfile)

    def test_end_to_end(self):
        p1 = Path(self.dir, 'e2e_t1')
        p2 = Path(self.dir, 'e2e_t2')
        self.assertFalse(p1.isfile)
        self.assertFalse(p2.isfile)
        target = TestE2E_T()
        self.assertIsNone(target())
        self.assertTrue(p1.isfile)
        self.assertTrue(p2.isfile)
        t1 = p1.mtime
        t2 = p2.mtime
        # maybe change the mtime of one then other to test uptodate?
        target = TestE2E_T()
        self.assertIsNone(target())
        # not testing what I think should be tested
        self.assertEqual(round(t1, 4), round(p1.mtime, 4))
        self.assertEqual(round(t2, 4), round(p2.mtime, 4))


class TestTask(TestCase):
    def test_instantiation(self):
        obj = Task()
        self.assertEqual(str(obj), Task.__name__)
        self.assertIsNone(obj('foobar', 'xyzzy', widget=True))
        # after calling __call__()
        self.assertEqual(obj.args, ('foobar', 'xyzzy'))
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


class TestSequential(TestCase):
    def test_iter(self):
        s = Sequential(1, 2, 3, 4)
        self.assertSequenceEqual(tuple(s), (1, 2, 3, 4))

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
