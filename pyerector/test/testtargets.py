#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import unittest
import sys

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    raise ImportError('wrong python version')

from pyerector import normjoin, verbose, debug, noop
from pyerector.helper import Verbose, u
from pyerector.exception import Error
from pyerector.base import Initer, Target, Task
from pyerector.iterators import Uptodate
from pyerector.targets import *
from pyerector.main import PyErector

if hasattr(unittest.TestCase, 'assertIsNone'):
    testcasewrapper = unittest.TestCase
else:
    class testcasewrapper(unittest.TestCase):
        def assertIs(self, a, b, msg=None):
            return self.assertTrue(a is b, msg=msg)
        def assertIsNot(self, a, b, msg=None):
            return self.assertFalse(a is b, msg=msg)
        def assertIsNone(self, x, msg=None):
            return self.assertIs(x, None, msg=msg)
        def assertIsNotNone(self, x, msg=None):
            return self.assertIsNot(x, None, msg=msg)
        def assertIn(self, a, b, msg=None):
            return self.assertTrue(a in b, msg=msg)
        def assertNotIn(self, a, b, msg=None):
            return self.assertFalse(a in b, msg=msg)
        def assertIsInstance(self, a, b, msg=None):
            return self.assertTrue(isinstance(a, b), msg=msg)
        def assertNotIsInstance(self, a, b, msg=None):
            return self.assertFalse(isinstance(a, b), msg=msg)
        def assertRaisesRegexp(self, exp, regexp, callable=None, *args, **kwds):
            raise NotImplementedError('assertRaisesRegexp')
        def assertGreater(self, a, b, msg=None):
            return self.assertTrue(a > b, msg=msg)
        def assertGreaterEqual(self, a, b, msg=None):
            return self.assertTrue(a >= b, msg=msg)
        def assertLess(self, a, b, msg=None):
            return self.assertTrue(a < b, msg=msg)
        def assertLessEqual(self, a, b, msg=None):
            return self.assertTrue(a <= b, msg=msg)
        def assertRegexpMatches(self, a, b, msg=None):
            import re
            return self.assertIsNot(re.search(b, a), None, msg=msg)
        def assertNotRegexpMatches(self, a, b, msg=None):
            return self.assertIs(re.search(b, a), None, msg=msg)
        def assertItemsEqual(self, a, b, msg=None):
            return self.assertEqual(sorted(a), sorted(b), msg=msg)
        def assertDictContainsSubset(self, a, b, msg=None):
            raise NotImplementedError('assertDictContainsSubset')
        def assertMultiLineEqual(self, a, b, msg=None):
            raise NotImplementedError('assertMultiLineEqual')
        def assertSequenceEqual(self, a, b, msg=None, seq_type=None):
            if seq_type is not None:
                self.assertIsInstance(a, seq_type, msg=msg)
                self.assertIsInstance(b, seq_type, msg=msg)
            return self.assertEqual(a, b, msg=msg)
        def assertListEqual(self, a, b, msg=None):
            return self.assertSequenceEqual(a, b, msg=msg, seq_type=list)
        def assertTupleEqual(self, a, b, msg=None):
            return self.assertSequenceEqual(a, b, msg=msg, seq_type=tuple)
        def assertSetEqual(self, a, b, msg=None):
            return self.assertSequenceEqual(a, b, msg=msg, seq_type=set)
        def assertDictEqual(self, a, b, msg=None):
            return self.assertSequenceEqual(
                sorted(a.items()),
                sorted(b.items()),
                msg=msg)

class TestStandardTargets(testcasewrapper):
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
        self.stream = StringIO()
        self.real_stream = verbose.stream
        verbose.stream = self.stream
        self.noop_state = noop.state
        noop.on()
    def tearDown(self):
        verbose.stream = self.real_stream
        noop.state = self.noop_state
    #@unittest.skip("not working on reillym-lt")
    def _test_all(self):
        PyErector("all")
        output = self.stream.getvalue()
        long_output = self.clean_output + self.long_output + self.all_output
        short_output = self.clean_output + self.all_output
        self.assertEqual(output, u(long_output))
    #@unittest.skip("not working on reillym-lt")
    def _test_default(self):
        PyErector("default")
        output = self.stream.getvalue()
        long_output = self.long_output + self.default_output
        short_output = self.default_output
        self.assertEqual(output, u(long_output))

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

