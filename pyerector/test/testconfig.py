#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

import os
import warnings

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

PyVersionCheck()

from pyerector.config import Config, State
from pyerector.variables import V


class TestConfig(TestCase):
    def setUp(self):
        self.thisdir = os.path.realpath(os.curdir)
        self.dir = self.dir.real
        if 'basedir' not in V:
            from os import curdir
            V['basedir'] = Path(curdir)

    def test_property_get(self):
        c = Config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always', DeprecationWarning)
            self.assertEqual(V['basedir'], c.basedir)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[-1].message))

    def test_property_set(self):
        c = Config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always', DeprecationWarning)
            c.testset = 'foobar'
            self.assertEqual(V['testset'], c.testset)
            self.assertEqual(len(w), 2)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[-1].message))

class TestState(TestCase):
    def test__init_(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            s = State('test_init_1')
            self.assertFalse(s.state)
            s = State('test_init_2', True)
            self.assertTrue(s.state)
            s = State('test_init_3', False)
            self.assertFalse(s.state)

    def test__bool_(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            s = State('test_bool_1')
            self.assertFalse(s)
            s = State('test_bool_2', True)
            self.assertTrue(s)

    def test_on(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            s = State('test_on_1')
            self.assertFalse(s)
            s.on()
            self.assertTrue(s)
            s = State('test_on_2', True)
            self.assertTrue(s)
            s.on()
            self.assertTrue(s)

    def test_off(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            s = State('test_off_1', True)
            self.assertTrue(s)
            s.off()
            self.assertFalse(s)
            s = State('test_off_2')
            self.assertFalse(s)
            s.off()
            self.assertFalse(s)

class TestGlobals(TestCase):
    """The noop and noTimer global instances are not deprecated,
so stop testing."""

