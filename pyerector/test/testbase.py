#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

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
from pyerector.base import Initer, Sequential
from pyerector.targets import Target
from pyerector.tasks import Task
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

    def test__init_(self):
        import logging
        obj = Initer()
        self.assertIsInstance(obj.logger, logging.Logger)
        self.assertTrue(obj.fileonly)
        self.assertEqual(obj.exclude, ())
        self.assertEqual(obj.pattern, None)
        self.assertEqual(obj.noglob, False)
        self.assertEqual(obj.recurse, False)
        self.assertFalse(hasattr(obj, 'args'))
        obj = Initer(foo='bar')
        self.assertTrue(hasattr(obj, 'foo'))
        self.assertEqual(obj.foo, 'bar')

    def test_join(self):
        #"""Ensure that join() method returns proper values."""
        obj = Initer()
        self.assertEqual(obj.join('foobar'),
                         Path(self.dir, 'foobar'))
        self.assertEqual(obj.join('xyzzy', 'foobar'),
                         Path(self.dir, 'xyzzy', 'foobar'))

    def test_get_kwarg(self):
        obj = Initer(was='my test', they='are here', howmany=8)
        obj.kwargs = {'that': 'is so cool'}
        obj.we = 'will rock you'
        obj.wehave = None
        self.assertEqual(obj.get_kwarg('wehave', str), None)
        self.assertRaises(TypeError, obj.get_kwarg, 'was', int)
        self.assertRaises(TypeError, obj.get_kwarg, 'wehave', str, noNone=True)
        self.assertEqual(obj.they, 'are here')
        self.assertEqual(obj.get_kwarg('that', str), 'is so cool')
        self.assertEqual(obj.get_kwarg('that', str, noNone=True), 'is so cool')
        self.assertEqual(obj.get_kwarg('that', (str, int)), 'is so cool')
        self.assertEqual(obj.get_kwarg('howmany', int), 8)
        self.assertRaises(TypeError, obj.get_kwarg, (str, bool))
        self.assertRaises(TypeError, obj.get_kwarg, 'that', (int, bool))

    def test_get_args(self):
        obj = Initer('hi', 8, 'there', foo=True, whatever=None)
        self.assertEqual(obj.args, ('hi', 8, 'there'))
        self.assertEqual(obj.get_args('args'), ('hi', 8, 'there'))
        obj = Initer(foo=(True,))
        self.assertEqual(obj.get_args('foo'), (True,))
        obj = Initer()
        self.assertEqual(obj.get_args('foo'), ())

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


class TestSequential(TestCase):
    def test_iter(self):
        s = Sequential(1, 2, 3, 4)
        self.assertSequenceEqual(tuple(s), (1, 2, 3, 4))

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
