#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os, sys

from .base import *

PyVersionCheck()

import pyerector

class Test_all_(TestCase):
    def test__all__(self):
        self.assertEqual(len(pyerector.__all__), 52)

# we don't need to test the functionality of these, that's done in
# testhelpers.py
class TestVerbose(TestCase):
    def testdefaults(self):
        self.assertFalse(pyerector.noop)

class TestSettings(TestCase):
    def test_V(self):
        self.assertTrue(hasattr(pyerector, 'V'))
        self.assertIsInstance(pyerector.V, pyerector.variables.VariableCache)

