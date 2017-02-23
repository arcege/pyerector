#!/usr/bin/python
# Copyright @ 2017 Michael P. Reilly. All rights reserved.
"""Tasks plugin for Copy."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Initer, Iterator, MapperTask
from ..iterators import FileIterator, FileMapper
from ..helper import newer

class Copy(MapperTask, Base):
    """Copy files to a destination directory, Exclude standard
hidden files.
constructor arguments:
Copy(*files, dest=<destdir>, exclude=<defaults>)"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str)),
    ) + Initer.basearguments

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
