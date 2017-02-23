#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Symlink."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..base import Initer, Iterator, Mapper, MapperTask
from ..iterators import FileIterator, FileMapper
from ..helper import newer

class Symlink(MapperTask, Base):
    """Generate a symbolic link.
constructor arguments:
Symlink(*files, dest=<dest>, exclude=<defaults>)"""

    def dojob(self, sname, dname, context):
            self.logger.debug('symlink.sname=%s; symlink.dname=%s',
                              sname, dname)
            srcfile = self.join(sname)
            dstfile = self.join(dname)
            if not excludes.match(sname):
                if srcfile.islink and newer(srcfile, dstfile):
                    self.logger.debug('uptodate: %s', dstfile)
                else:
                    self.logger.info('symlink(%s, %s)', dname, sname)
                    dstfile.makelink(srcfile)

Symlink.register()
