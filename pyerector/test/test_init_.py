#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os, sys

from .base import *

PyVersionCheck()

import pyerector

class Test_all_(TestCase):
    def test__all__(self):
        self.assertEqual(len(pyerector.__all__), 49)

# we don't need to test the functionality of these, that's done in
# testhelpers.py
class TestVerbose(TestCase):
    def testdefaults(self):
        self.assertTrue(pyerector.warn)
        self.assertFalse(pyerector.verbose)
        self.assertEqual(bool(pyerector.debug),
                'DEBUG' in os.environ and os.environ['DEBUG'] != ''
        )
        self.assertFalse(pyerector.noop)
    def teststreams(self):
        self.assertIs(pyerector.warn.stream, sys.stdout)
        # we've change the stream in TestCase
        #self.assertIs(pyerector.verbose.stream, sys.stdout)
        self.assertIs(pyerector.debug.stream, sys.stdout)

class TestSettings(TestCase):
    def test_hasformat(self):
        self.assertEqual(pyerector.hasformat, hasattr('', 'format'))
    def test_V(self):
        self.assertTrue(hasattr(pyerector, 'V'))
        self.assertIsInstance(pyerector.V, pyerector.variables.VariableCache)

