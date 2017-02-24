#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Symlink."""

from ..helper import newer
from ._base import MapperTask

class Symlink(MapperTask):
    """Generate a symbolic link.
constructor arguments:
Symlink(*files, dest=<dest>, exclude=<defaults>)"""

    def dojob(self, sname, dname, context):
        """Create a symbolic link; dname is what is created,
and sname is the contents."""
        self.logger.debug('symlink.sname=%s; symlink.dname=%s',
                          sname, dname)
        if sname.islink and newer(sname, dname):
            self.logger.debug('uptodate: %s', dname)
        else:
            self.logger.info('symlink(%s, %s)', dname, sname)
            dname.makelink(sname)

Symlink.register()
