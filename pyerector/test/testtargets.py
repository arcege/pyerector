#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

import logging

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from .base import *
except ValueError:
    import os, sys
    sys.path.insert(
        0,
        os.path.normpath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, os.pardir
            )
        )
    )
    from base import *

PyVersionCheck()

from pyerector.config import noop
from pyerector.path import Path
from pyerector.variables import V
from pyerector.iterators import Uptodate
from pyerector.targets import *
from pyerector.targets import Target
from pyerector.tasks import *
from pyerector.tasks import Task
from pyerector.main import PyErector


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


class TestStandardTargets(TestCase):
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
InitDirs: done.
Init: done.
Compile: done.
Build: done.
Test: done.
All: done.
"""

    def setUp(self):
        self.noop_state = noop.state
        noop.on()

    def tearDown(self):
        noop.state = self.noop_state

    #@unittest.skip("not working on reillym-lt")
    def _test_all(self):
        PyErector("all")
        output = self.stream.getvalue()
        long_output = self.clean_output + self.long_output + self.all_output
        short_output = self.clean_output + self.all_output
        self.assertEqual(output, long_output)

    #@unittest.skip("not working on reillym-lt")
    def _test_default(self):
        PyErector("default")
        output = self.stream.getvalue()
        long_output = self.long_output + self.default_output
        short_output = self.default_output
        self.assertEqual(output, long_output)


# test code
def test():
    from os.path import join
    import os
    import tempfile
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
                uptodates = (Foobar_utd,)

                def run(self):
                    Copy()(
                        'foobar',
                        dest=join('build', 'foobar')
                    )

            class DistTar_t(Tar):
                name = join('dist', 'xyzzy.tgz')
                root = 'build'
                files = ('foobar',)
            # end setup
            f = open(join(tmpdir, 'foobar'), 'w')
            f.write("""\
This is a story,
Of a lovely lady,
With three very lovely girls.
""")
            f.close()
            Packaging.tasks = (DistTar_t,)
            Packaging.uptodates = (DistTar_utd,)
            Clean.files = ('build', 'dist')
            InitDirs.files = ('build', 'dist')
            tmpdiropt = '--directory=' + str(tmpdir)
            logger = logging.getLogger('pyerector')
            logger.debug('PyErector("-v", "' + tmpdiropt + '", "clean")')
            PyErector('-v', tmpdiropt, 'clean')
            if logger.isEnabledFor(logging.DEBUG):
                os.system('ls -lAtr ' + str(tmpdir))
            logger.debug('PyErector("-v", "' + tmpdiropt + '")')
            PyErector('-v', tmpdiropt)  # default
            if logger.isEnabledFor(logging.DEBUG):
                os.system('ls -lAtr ' + str(tmpdir))
            logger.debug('PyErector("-v", "' + tmpdiropt + '")')
            PyErector('-v', tmpdiropt)  # default with uptodate
            if logger.isEnabledFor(logging.DEBUG):
                os.system('ls -lAtr ' + str(tmpdir))
        finally:
            Remove()(tmpdir)

