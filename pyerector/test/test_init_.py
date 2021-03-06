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

import pyerector


class Test_all_(TestCase):
    def test__all__(self):
        self.assertEqual(len(pyerector.__all__), 62)


class TestSettings(TestCase):
    def test_V(self):
        self.assertTrue(hasattr(pyerector, 'V'))
        self.assertIsInstance(pyerector.V, pyerector.variables.VariableCache)

