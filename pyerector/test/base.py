#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import shutil
import sys
import tempfile
import unittest

from pyerector import debug
from pyerector.base import Initer

def PyVersionCheck():
    from sys import version_info
    if version_info[0] == 2 and version_info[1] < 7:
        raise ImportError('wrong python version')

class TestCase(unittest.TestCase):
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

