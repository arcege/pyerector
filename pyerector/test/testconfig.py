#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os

from .base import *

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
        self.assertEqual(V['basedir'], c.basedir)

