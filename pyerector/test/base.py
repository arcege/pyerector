#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import os
import shutil
import sys
import tempfile
import unittest
from unittest import SkipTest

__all__ = [
  'PyVersionCheck',
  'SkipTest',
  'TestCase',
]

from pyerector import debug
from pyerector.variables import V

Platform = sys.platform[:3]

def PyVersionCheck():
    from sys import version_info
    if version_info[0] == 2 and version_info[1] < 7:
        raise ImportError('wrong python version')

class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        debug('%s.setupClass()' % cls.__name__)
        cls.dir = tempfile.mkdtemp()
        try:
            cls.oldconfigbasedir = V['basedir']
        except KeyError:
            cls.oldconfigbasedir = os.curdir
        V['basedir'] = cls.dir
        cls.platform = Platform
        if cls.platform not in ('win', 'lin', 'mac'):
            cls.platform = None
    @classmethod
    def tearDownClass(cls):
        debug('%s.tearDownClass()' % cls.__name__)
        V['basedir'] = cls.oldconfigbasedir
        def handle_perms(func, path, exc_info):
            import os
            if cls.platform == 'win': # broken OS again
                writable = os.path.stat.S_IWRITE
            else:
                writable = int('755', 8)
            os.chmod(path, writable)
            func(path)
        shutil.rmtree(cls.dir, onerror=handle_perms)

