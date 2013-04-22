#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os

from .base import PyVersionCheck, TestCase

PyVersionCheck()

from pyerector.config import Config

class TestConfig(TestCase):
    def setUp(self):
        self.thisdir = os.path.realpath(os.curdir)
        self.dir = os.path.realpath(self.dir)
    def test_initialized(self):
        c = Config()
        self.assertFalse(c.initialized)
        self.assertEqual(c._basedir, self.thisdir)
    def test_property_get(self):
        c = Config()
        self.assertEqual(c.basedir, c._basedir)
        c = Config(self.dir)
        self.assertEqual(c.basedir, self.dir)
    def test_property_set_nochange(self):
        c = Config(self.dir)
        self.assertEqual(c._basedir, self.dir)
        c.basedir = self.dir
        self.assertEqual(c._basedir, self.dir)
    def test_property_set_None(self):
        c = Config()
        with self.assertRaises(AttributeError):
            c.basedir = None
            self.assertEqual(c._basedir, self.thisdir)
    def test_property_set_notdir(self):
        c = Config()
        with self.assertRaises(ValueError):
            c.basedir = '/etc/passwd'
        self.assertEqual(c._basedir, self.thisdir)

