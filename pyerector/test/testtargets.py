#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

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
from pyerector.base import Target
from pyerector.iterators import Uptodate
from pyerector.targets import *
from pyerector.tasks import *
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

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
