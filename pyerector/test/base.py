#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest import SkipTest

__all__ = [
    'logger',
    'PyVersionCheck',
    'SkipTest',
    'TestCase',
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('pyerector.test')
logger.propagate = False
logger.addHandler(logging.StreamHandler())

# this will initialize by virtue of importing pyerector implicitly
from pyerector.variables import V

Platform = sys.platform[:3]


def PyVersionCheck():
    from sys import version_info
    if version_info[0] == 2 and version_info[1] < 7:
        raise ImportError('wrong python version')


class TestCase(unittest.TestCase):
    oldconfigbasedir = None
    platform = Platform

    @classmethod
    def setUpClass(cls):
        logger.debug('%s.setupClass()', cls.__name__)
        cls.dir = tempfile.mkdtemp()
        try:
            cls.oldconfigbasedir = V['basedir']
        except KeyError:
            cls.oldconfigbasedir = os.curdir
        V['basedir'] = cls.dir
        if cls.platform not in ('win', 'lin', 'mac'):
            cls.platform = None

    @classmethod
    def tearDownClass(cls):
        logger.debug('%s.tearDownClass()', cls.__name__)
        V['basedir'] = cls.oldconfigbasedir

        def handle_perms(func, path, exc_info):
            import os
            if cls.platform == 'win':  # broken OS again
                writable = os.path.stat.S_IWRITE
            else:
                writable = int('755', 8)
            os.chmod(path, writable)
            func(path)
        shutil.rmtree(cls.dir, onerror=handle_perms)
