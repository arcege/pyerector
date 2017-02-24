#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Copy."""

from ..helper import newer
from ._base import MapperTask

class Copy(MapperTask):
    """Copy files to a destination directory, Exclude standard
hidden files.
constructor arguments:
Copy(*files, dest=<destdir>, exclude=<defaults>)"""

    # pylint: disable=unused-argument
    def dojob(self, sname, dname, context):
        self.logger.debug('sname = %s; dname = %s', sname, dname)
        srcfile = self.join(sname)
        dstfile = self.join(dname)
        if srcfile.isdir:
            # remove whatever is there
            if dstfile.exists and not dstfile.isdir:
                dstfile.remove()
            # create the directory
            if not dstfile.exists:
                dstfile.mkdir()
        elif srcfile.isfile and newer(srcfile, dstfile, logger=self.logger):
            self.logger.debug('uptodate: %s', dstfile)
        else:
            if not dstfile.dirname.isdir:
                dstfile.dirname.mkdir()
            self.logger.info('copy2(%s,%s)', sname, dname)
            srcfile.copy(dstfile)

Copy.register()
