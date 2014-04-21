#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

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
        self.assertEqual(len(pyerector.__all__), 59)


class TestSettings(TestCase):
    def test_V(self):
        self.assertTrue(hasattr(pyerector, 'V'))
        self.assertIsInstance(pyerector.V, pyerector.variables.VariableCache)

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
