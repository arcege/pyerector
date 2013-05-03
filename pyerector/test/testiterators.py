#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import PyVersionCheck, TestCase

PyVersionCheck()

from pyerector import normjoin, verbose, debug, noop
from pyerector.iterators import *

class TestStaticIterator(TestCase):
    pass

class TestFileIterator(TestCase):
    pass

class TestFileList(TestCase):
    pass

class TestDirList(TestCase):
    pass

class TestFileSet(TestCase):
    pass

class TestFileMapper(TestCase):
    pass

class TestBasenameMapper(TestCase):
    pass

class TestMergeMapper(TestCase):
    pass

class TestUptodate(TestCase):
    pass

