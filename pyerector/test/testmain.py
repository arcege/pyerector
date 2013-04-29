#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import sys

from .base import PyVersionCheck, TestCase

PyVersionCheck()

from pyerector.main import *

class Test_pymain(TestCase):
    def test_same(self):
        self.assertIs(PyErector, pymain)

class TestPyErectorArguments(TestCase):
    def test_result(self):
        PyErector('--dry-run')
    def test_noargs(self):
        real_args = sys.argv[:]
        try:
            del sys.argv[1:]
            PyErector()
        finally:
            sys.argv[:] = real_args
    def test_passed_args(self):
        PyErector('--dry-run')

