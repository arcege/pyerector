#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import *

PyVersionCheck()

from pyerector import normjoin, verbose, debug, noop
from pyerector.exception import Error, extract_tb

class TestError(TestCase):
    pass

class Test_extract_tb(TestCase):
    pass

