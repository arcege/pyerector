#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.

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


class TestContainer(TestCase):
    pass


class TestCopy(TestCase):
    def setUp(self):
        self.src = 'src'
        self.dest = 'dest'
        self.savedir = os.getcwd()
        os.chdir(self.dir)
        self.fullsrc = os.path.join(self.dir, self.src)
        self.fulldest = os.path.join(self.dir, self.dest)
        os.mkdir(self.fullsrc)
        os.mkdir(self.fulldest)
        open(os.path.join(self.dir, 'a'), 'w').write('hi\n')
        open(os.path.join(self.dir, 'b'), 'w').write('bye\n')
        open(os.path.join(self.dir, 'c'), 'w').write('xyzzy\n')
    def tearDown(self):
        import shutil
        os.chdir(self.savedir)
        shutil.rmtree(self.fullsrc)
        shutil.rmtree(self.fulldest)

    def testfile2dir(self):
        src = normjoin('a')
        Copy(src, dest=self.dest)()
        self.assertTrue(os.path.exists(os.path.join(self.dest, 'a')))
        self.assertEqual('hi\n', open(os.path.join(self.dest, 'a')).read())
    def testfiles2dir(self):
        Copy('a', 'b', 'c', dest=self.dest)()
        self.assertTrue(os.path.exists(os.path.join(self.dest, 'a')))
        self.assertTrue(os.path.exists(os.path.join(self.dest, 'b')))
        self.assertTrue(os.path.exists(os.path.join(self.dest, 'c')))
        self.assertEqual('hi\n', open(os.path.join(self.dest, 'a')).read())
        self.assertEqual('bye\n', open(os.path.join(self.dest, 'b')).read())
        self.assertEqual('xyzzy\n', open(os.path.join(self.dest, 'c')).read())

    def _testexclusion(self):
        src = os.path.join(self.dir, 'src')
        dest = os.path.join(self.dir, 'dest')
        Copy(
            os.path.join(src, 'a'),
            os.path.join(src, 'b'),
            os.path.join(src, 'c'),
            dest=dest,
            exclusions=['b'])()
        self.assertTrue(os.path.exists(os.path.join(dest, 'a')))
        self.assertFalse(os.path.exists(os.path.join(dest, 'b')))
        self.assertTrue(os.path.exists(os.path.join(dest, 'c')))
        self.assertEqual('hi\n', open(os.path.join(dest, 'a').read()))
        self.assertEqual('xyzzy\n', open(os.path.join(dest, 'c').read()))

class TestCopyTree(TestCase):
    pass


class TestDownload(TestCase):
    pass


class TestEcho(TestCase):
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


class TestSshEngine(TestCase):
    pass


class TestSsh(TestCase):
    pass


class TestSymlink(TestCase):
    pass


class TestTar(TestCase):
    pass


class TestTokenize(TestCase):
    pass


class TestTouch(TestCase):
    pass


class TestUncontainer(TestCase):
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
