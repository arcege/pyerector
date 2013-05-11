#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import *

PyVersionCheck()

from pyerector.version import get_release, get_version

class TestVersion(TestCase):
    def test_get_version(self):
        self.assertEqual(
                get_version(),
                'r%hg.version% (%hg.branch%) <%hg.tags%>'
        )
    def test_get_release(self):
        self.assertEqual(
                get_release(),
                '%release.product% %release.number%'
        )

