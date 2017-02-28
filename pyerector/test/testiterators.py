#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

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

from pyerector.helper import Exclusions
from pyerector.path import Path
from pyerector.iterators import Iterator
from pyerector.iterators import *

class TestIterator(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestIterator, cls).setUpClass()
        top = cls.dir
        bin, lib, src = (top + 'bin'), (top + 'lib'), (top + 'src')
        bin.mkdir()
        lib.mkdir()
        src.mkdir()
        (src + 'foo.py').open()
        (src + 'bar.c').open()
        (src + 'bar.h').open()
        (src + 'testfoo.py').open()
        (lib + 'bar.a').open()
        (bin + 'foo').open()
        (bin + 'bar').open()
        (top + 'README.txt').open()

    def test_init_(self):
        obj = Iterator('src', 'lib', 'bin')
        self.assertEqual(obj.args, ('src', 'lib', 'bin'))
        self.assertIsNone(obj.path)
        obj = Iterator(pattern='*.py')
        self.assertEqual(obj.pattern, '*.py')
        obj = Iterator('src', pattern='*.py', recurse=True, noglob=True,
            fileonly=False, exclude=('test*.py'))
        self.assertEqual(obj.args, ('src',))
        self.assertEqual(obj.pattern, '*.py')
        self.assertTrue(obj.recurse)
        self.assertTrue(obj.noglob)
        self.assertFalse(obj.fileonly)
        self.assertIsInstance(obj.exclusion, Exclusions)
        self.assertEqual(obj.exclusion, set(('test*.py',)))

    def test_repr_(self):
        i = Iterator()
        self.assertEqual(repr(i), '<Iterator ()>')
        i = Iterator('src', 'bin')
        self.assertEqual(repr(i), "<Iterator ('src', 'bin')>")

    def test_call_(self):
        self.assertRaises(NotImplementedError, Iterator())

    def test_attributes(self):
        obj = Iterator()
        self.assertIsNone(obj.pattern)
        self.assertFalse(obj.recurse)
        self.assertFalse(obj.noglob)
        self.assertTrue(obj.fileonly)
        self.assertEqual(obj.exclusion, set())

    def testappend(self):
        obj = Iterator()
        self.assertIsNone(obj.path)
        obj.append('foo')
        self.assertIsNotNone(obj.path)
        self.assertIsInstance(obj.path, tuple)
        self.assertEqual(len(obj.path), 1)
        self.assertIsInstance(obj.path[0], Path)
        self.assertEqual(obj.path[0].value, 'foo')
        foo = Path('foo')
        obj.append(foo)
        self.assertEqual(len(obj.path), 2)
        self.assertIsInstance(obj.path[1], Path)
        self.assertEqual(obj.path[1], foo)
        obj.append(['xyzzy', foo, 'hello'])
        self.assertEqual(len(obj.path), 5)
        for i in obj.path:
            self.assertIsInstance(i, Path)
        self.assertEqual(obj.path[2].value, 'xyzzy')
        self.assertEqual(obj.path[3], foo)
        self.assertEqual(obj.path[4].value, 'hello')

    def test_prepend(self):
        obj = Iterator()
        self.assertIsNone(obj.pool)
        iter(obj)
        self.assertIsNotNone(obj.pool)
        obj._prepend('foo')
        self.assertEqual(len(obj.pool), 1)
        self.assertIsInstance(obj.pool[0], Path)
        self.assertEqual(obj.pool[0].value, 'foo')
        foo = Path('foo')
        obj._prepend(foo)
        self.assertEqual(len(obj.pool), 2)
        self.assertIsInstance(obj.pool[0], Path)
        self.assertEqual(obj.pool[0], foo)
        obj._prepend(['A', 'B', foo, 'C'])
        self.assertEqual(len(obj.pool), 6)
        for i in obj.pool:
            self.assertIsInstance(i, Path)
        self.assertEqual(obj.pool[0].value, 'A')
        self.assertEqual(obj.pool[1].value, 'B')
        self.assertEqual(obj.pool[2], foo)
        self.assertEqual(obj.pool[3].value, 'C')

    def test_iter_(self):
        obj = Iterator('src', 'lib', 'bin')
        self.assertEqual(iter(obj), obj)
        self.assertIsInstance(obj.curset, type(iter([])))
        self.assertEqual(obj.pool, ['src', 'lib', 'bin'])

    def test_next_(self):
        obj = Iterator('src', 'lib')
        iter(obj)
        self.assertEqual(next(obj), 'src')
        self.assertEqual(next(obj), 'lib')
        self.assertRaises(StopIteration, obj.next)

    def testgetnextset(self):
        obj = Iterator('src', 'lib', 'bin')
        iter(obj)
        initialset = obj.curset
        self.assertIsNone(obj.getnextset())
        self.assertNotEqual(initialset, obj.curset)

    def testpost_process_candidate(self):
        obj = Iterator()
        self.assertEqual(obj.post_process_candidate(None), None)
        self.assertEqual(obj.post_process_candidate("hello"), "hello")

    def testadjust(self):
        obj = Iterator()
        f = "hello.py"
        result = obj.adjust(f)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, f)
        f = Path(f)
        result = obj.adjust(f)
        self.assertEqual(result[0].value, f)

    def testpattern(self):
        obj = Iterator('foo.py', 'foo.pyc', 'foo.c', 'bar.txt', 'testfoo.py',
                       pattern='*.py')
        # foo.pyc is excluded
        self.assertEqual(list(obj), [Path('foo.py'), Path('testfoo.py')])
        obj = Iterator('foo.py', 'foo.pyc', 'foo.c', 'bar.txt', 'testfoo.py',
                       pattern='*.py*')
        # foo.pyc is excluded
        self.assertEqual(list(obj), [Path('foo.py'), Path('testfoo.py')])
        obj = Iterator('foo.py', 'foo.pyc', 'foo.c', 'bar.txt', 'testfoo.py',
                       pattern='*foo*')
        self.assertEqual(list(obj),
                         [Path('foo.py'), Path('foo.c'), Path('testfoo.py')])

    # the noglob argument does nothing for Iterator and should be moved
    def _testnoglob(self):
        pass

    # the recurse argument does nothing for Iterator and should be moved
    def _testrecurse(self):
        pass

    # the recurse argument does nothing for Iterator and should be moved
    def _testfileonly(self):
        pass

    def testexclude(self):
        obj = Iterator('foo.py', 'foo.py~', 'foo.pyc')
        self.assertEqual(tuple(obj), (Path('foo.py'),))
        obj = Iterator('foo.py', 'foo.c', exclude='*.py')
        self.assertEqual(tuple(obj), (Path('foo.c'),))
        obj = Iterator('foo.py', 'foo.py~', 'foo.pyc',
                exclude=Exclusions(usedefaults=None))
        self.assertEqual(tuple(obj),
                (Path('foo.py'), Path('foo.py~'), Path('foo.pyc')))

    def testofiterator(self):
        i0 = Iterator('foo.py', 'foo.c', 'testfoo.py')
        i1 = Iterator(i0, 'bar.txt')
        self.assertEqual(tuple(i1),
                (Path('foo.py'), Path('foo.c'), Path('testfoo.py'),
                 Path('bar.txt')))
        i1 = Iterator(i0, pattern='*.py')
        self.assertEqual(tuple(i1),
                (Path('foo.py'), Path('testfoo.py')))
        i1 = Iterator(i0, exclude='test*')
        i2 = Iterator(i1, pattern='*.py')
        self.assertEqual(tuple(i2), (Path('foo.py'),))

    def testcheck_candidate(self):
        obj = Iterator()
        self.assertTrue(obj.check_candidate(Path("hello")))
        obj = Iterator(pattern="*.py")
        self.assertTrue(obj.check_candidate(Path("hello.py")))
        self.assertFalse(obj.check_candidate(Path("hello.c")))
        self.assertRaises(AttributeError, obj.check_candidate, ('hello.py',))

class TestMapper(TestCase):
    pass


class TestStaticIterator(TestCase):
    pass


class TestFileIterator(TestCase):
    pass


class TestFileList(TestCase):
    pass


class TestDirList(TestCase):
    pass


class TestFileSet(TestCase):
    pass


class TestFileMapper(TestCase):
    pass


class TestBasenameMapper(TestCase):
    pass


class TestMergeMapper(TestCase):
    pass


class TestUptodate(TestCase):
    pass

