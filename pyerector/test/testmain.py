#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

import sys

from .base import *

PyVersionCheck()

from pyerector.main import *

class Test_pymain(TestCase):
    def test_same(self):
        self.assertIs(PyErector, pymain)

class TestPyErectorArguments(TestCase):
    # causing failures in other tests
    def _test_result(self):
        PyErector('--dry-run')
    # causing failures in other tests
    def _test_noargs(self):
        real_args = sys.argv[:]
        try:
            del sys.argv[1:]
            PyErector('--dry-run')
        finally:
            sys.argv[:] = real_args
    # causing failures in other tests
    def _test_passed_args(self):
        PyErector('--dry-run')

