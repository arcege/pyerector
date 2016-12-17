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


class TestError(TestCase):
    pass


class Test_extract_tb(TestCase):
    pass

if __name__ == '__main__':
    import logging, unittest
    logging.getLogger('pyerector').level = logging.ERROR
    unittest.main()
