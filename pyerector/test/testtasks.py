#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os

try:
    from .base import *
except ValueError:
    import sys
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

from pyerector.helper import normjoin
from pyerector.iterators import FileList
from pyerector.tasks import *


class TestChmod(TestCase):
    @staticmethod
    def getmode(filename):
        return os.path.stat.S_IMODE(os.stat(filename).st_mode)

    def testsimple(self):
        fname = normjoin(self.dir, 'testsimple1.txt')
        open(fname, 'w')
        os.chmod(fname, 0)  # no permissions to start
        Chmod('testsimple1.txt')()
        self.assertEqual(self.getmode(fname), 438)

    def testchange(self):
        if self.platform == 'win':  # Broken OS
            return
        fname = normjoin(self.dir, 'testchange1.txt')
        open(fname, 'w')
        oldmode = self.getmode(fname)
        Chmod('testchange1.txt', mode=int('555', 8))()
        self.assertEqual(self.getmode(fname), int('555', 8))
        Chmod('testchange1.txt', mode=oldmode)()
        self.assertEqual(self.getmode(fname), oldmode)

    def testmultiple(self):
        files = FileList(
            'testmultiple1', 'testmultiple2', 'testmultiple3',
        )
        for fname in files:
            open(normjoin(self.dir, fname), 'w')
            os.chmod(normjoin(self.dir, fname), 0)
        Chmod('testmultiple1', 'testmultiple2', 'testmultiple3')()
        for fname in files:
            self.assertEqual(self.getmode(normjoin(self.dir, fname)), int('666', 8))


class TestCopy(TestCase):
    pass


class TestCopyTree(TestCase):
    pass


class TestDownload(TestCase):
    pass


class TestEgg(TestCase):
    pass


class TestHashGen(TestCase):
    pass


class TestJava(TestCase):
    pass


class TestMkdir(TestCase):
    pass


class TestPyCompile(TestCase):
    pass


class TestRemove(TestCase):
    pass


class TestScp(TestCase):
    pass


class TestShebang(TestCase):
    pass


class TestSpawn(TestCase):
    pass


class TestSsh(TestCase):
    pass


class TestSymlink(TestCase):
    pass


class TestTar(TestCase):
    pass


class TestTokenize(TestCase):
    pass


class TestUnittest(TestCase):
    pass


class TestUntar(TestCase):
    pass


class TestUnzip(TestCase):
    pass


class TestZip(TestCase):
    pass

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
