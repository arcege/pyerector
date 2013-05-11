#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import unittest
import sys

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from .base import *

PyVersionCheck()

from pyerector import normjoin, verbose, debug, noop
from pyerector.helper import Verbose, u
from pyerector.exception import Error
from pyerector.base import Initer, Target, Task
from pyerector.iterators import Uptodate
from pyerector.targets import *
from pyerector.main import PyErector

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

