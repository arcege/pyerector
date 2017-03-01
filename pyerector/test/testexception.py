#!/usr/bin/python
# Copyright @ 2012-2016 Michael P. Reilly. All rights reserved.

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

import sys

from pyerector.exception import Error, Abort, extract_tb

class TestError(TestCase):
    def test_str_(self):
        try:
            raise Error('ENOENT', 'no such file or directory')
        except Error:
            t, e, tb = sys.exc_info()
            self.assertEqual(str(e), 'ENOENT: no such file or directory')

    def test_format_(self):
        try:
            raise Error('What is wrong?', 'I do not know')
        except Error:
            t, e, tb = sys.exc_info()
            self.assertEqual(format(e), 'What is wrong?: I do not know')


class Test_extract_tb(TestCase):
    pass

