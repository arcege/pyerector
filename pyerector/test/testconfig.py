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

from pyerector.config import Config, State, noop, noTimer
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
        s = State()
        self.assertFalse(s.state)
        s = State(True)
        self.assertTrue(s.state)
        s = State(False)
        self.assertFalse(s.state)

    def test__bool_(self):
        s = State()
        self.assertFalse(s)
        s = State(True)
        self.assertTrue(s)

    def test_on(self):
        s = State()
        self.assertFalse(s)
        s.on()
        self.assertTrue(s)
        s = State(True)
        self.assertTrue(s)
        s.on()
        self.assertTrue(s)

    def test_off(self):
        s = State(True)
        self.assertTrue(s)
        s.off()
        self.assertFalse(s)
        s = State()
        self.assertFalse(s)
        s.off()
        self.assertFalse(s)

class TestGlobals(TestCase):
    def test_noop(self):
        self.assertIsInstance(noop, State)
        self.assertFalse(noop)  # default value

    def test_noTimer(self):
        self.assertIsInstance(noTimer, State)
        self.assertFalse(noTimer)  # default value

