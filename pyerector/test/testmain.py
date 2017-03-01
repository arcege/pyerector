#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

import logging
import sys

try:
    from .base import *
except ValueError:
    import os
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

from pyerector.main import *
from pyerector.variables import Variable
from pyerector.targets import Target


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


class Thread(Target):
    def run(self):
        import threading
        Variable('thread.name', threading.currentThread().name)


class TestPyErectorThread(TestCase):
    def test_thread_name(self):
        self.assertRaises(SystemExit, PyErector, 'thread')
        # it is sufficient to check that the thread is not 'MainThread'
        self.assertEqual(Variable('thread.name').value, 'PyErector')

class TestPyErector(TestCase):
    def test_cli_variable(self):
        with self.assertRaises(SystemExit):
            PyErector('test_cli_variable=foo', 'thread')
        self.assertEqual(Variable('test_cli_variable').value, 'foo')
        self.assertEqual(Variable('thread.name').value, 'PyErector')

