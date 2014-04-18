#!/usr/bin/python
# Copyright @ 2012-2013 Michael P. Reilly. All rights reserved.

from .base import *

PyVersionCheck()

from pyerector.version import Version


class TestVersion(TestCase):
    def test_version(self):
        self.assertEqual(
            Version.version,
            'r%hg.version% (%hg.branch%) <%hg.tags%>'
        )

    def test_release(self):
        self.assertEqual(
            Version.release,
            '%release.product% %release.number%'
        )
    def test__call__(self):
        from logging import getLogger, FATAL
        from ..variables import V
        # we don't have a release number at this level, so use the token
        self.assertIsNone(Version('%release.number%'))
        oldlevel = getLogger('pyerector').level
        getLogger('pyerector').level = FATAL
        self.assertRaises(SystemExit, Version, '9999')
        getLogger('pyerector').level = oldlevel

