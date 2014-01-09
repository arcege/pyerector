#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import *

PyVersionCheck()

from pyerector.version import Version


class TestVersion(TestCase):
    def test_version(self):
        self.assertEqual(
            Version.version,
            'r () <>'
            #'r%hg.version% (%hg.branch%) <%hg.tags%>'
        )

    def test_release(self):
        self.assertEqual(
            Version.release,
            '%release.product% %release.number%'
        )
