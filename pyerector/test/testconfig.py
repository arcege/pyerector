#!/usr/bin/python
# Copyright @ 2012-2015 Michael P. Reilly. All rights reserved.

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

from pyerector.config import Config
from pyerector.variables import V


class TestConfig(TestCase):
    def setUp(self):
        self.thisdir = os.path.realpath(os.curdir)
        self.dir = os.path.realpath(self.dir)
        if 'basedir' not in V:
            from os import curdir
            V['basedir'] = curdir

    def test_property_get(self):
        c = Config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always', DeprecationWarning)
            self.assertEqual(V['basedir'], c.basedir)
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "deprecated" in str(w[-1].message)

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
