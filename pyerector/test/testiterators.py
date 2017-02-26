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

from pyerector.iterators import *

class TestIterator(TestCase):
    pass


class TestMapper(TestCase):
    pass


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

