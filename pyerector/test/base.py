#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import sys
import unittest

def PyVersionCheck():
    from sys import version_info
    if version_info[0] == 2 and version_info[1] < 7:
        raise ImportError('wrong python version')

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

class TestCase(testcasewrapper):
    @classmethod
    def setUpClass(cls):
        debug('%s.setupClass()' % cls.__name__)
        cls.dir = tempfile.mkdtemp()
        cls.oldconfigbasedir = Initer.config.basedir
        Initer.config.basedir = cls.dir
    @classmethod
    def tearDownClass(cls):
        debug('%s.tearDownClass()' % cls.__name__)
        Initer.config.basedir = cls.oldconfigbasedir
        shutil.rmtree(cls.dir)
