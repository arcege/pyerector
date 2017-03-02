#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

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

from pyerector.path import Path
from pyerector.exception import Error
from pyerector.variables import V
from pyerector.tasks import *
from pyerector.tasks import Task, IteratorTask, MapperTask


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
        old_noop = V['pyerector.noop']
        try:
            V['pyerector.noop'] = True

            class NoopTask(Task):
                foobar = False

                def run(self):
                    self.foobar = True
            obj = NoopTask()
            obj()
            self.assertFalse(obj.foobar)
        finally:
            V['pyerector.noop'] = old_noop


class TestIteratorTask(TestCase):
    pass


class TestMapperTask(TestCase):
    pass


class TestChmod(TestCase):
    @staticmethod
    def getmode(filename):
        return os.path.stat.S_IMODE(os.stat(filename).st_mode)

    def testsimple(self):
        fname = Path(self.dir, 'testsimple1.txt')
        fname.open('w')  # create the file
        fname.chmod(0)  # no permissions to start
        self.assertTrue(fname.isfile)
        Chmod(fname)()
        self.assertEqual(fname.mode, int('666', 8))

    def testchange(self):
        if self.platform == 'win':  # Broken OS
            return
        newmode = int('555', 8)
        fname = Path(self.dir, 'testchange1.txt')
        fname.open('w')
        fname.chmod(0)
        oldmode = fname.mode
        self.assertEqual(oldmode, 0)
        Chmod(fname, mode=newmode)()
        fname.refresh()
        self.assertEqual(fname.mode, newmode)
        Chmod(fname, mode=oldmode)()
        fname.refresh()
        self.assertEqual(fname.mode, oldmode)

    def testmultiple(self):
        files = [
            Path(self.dir, fname) for fname in
                ('testmultple1', 'testmultiple2',
                 'testmultiple3')
        ]
        newmode = int('666', 8)
        for fname in files:
            fname.open('w')
            fname.chmod(0)
        Chmod(*tuple(files), mode=newmode)()
        for fname in files:
            fname.refresh()
            self.assertEqual(fname.mode, newmode)


class TestContainer(TestCase):
    pass


class TestCopy(TestCase):
    def setUp(self):
        self.src = 'src'
        self.dest = 'dest'
        self.savedir = Path.cwd()
        self.dir.chdir()
        self.fullsrc = self.dir + self.src
        self.fulldest = self.dir + self.dest
        self.fullsrc.mkdir()
        self.fulldest.mkdir()
        (self.dir + 'a').open('w').write('hi\n')
        (self.dir + 'b').open('w').write('bye\n')
        (self.dir + 'c').open('w').write('xyzzy\n')
    def tearDown(self):
        import shutil
        self.savedir.chdir()
        self.fullsrc.remove()
        self.fulldest.remove()

    def testfile2dir(self):
        src = Path('a')
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

