#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Touch."""

from ._base import MapperTask

class Touch(MapperTask):
    """Create file if it didn't exist already.
constructor arguments:
Touch(*files, dest=None)"""

    def dojob(self, sname, dname, context):
        self.logger.info('touch(%s)', dname)
        dname.open('a')

Touch.register()
