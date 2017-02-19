#!/usr/bin/python
"""Tasks plugin for Copy."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..base import Initer, Iterator, Task
from ..iterators import FileIterator, FileMapper

class Copy(Task, Base):
    """Copy files to a destination directory, Exclude standard
hidden files.
constructor arguments:
Copy(*files, dest=<destdir>, exclude=<defaults>)"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str)),
    ) + Initer.basearguments

    def run(self):
        """Copy files to a destination directory."""
        self.logger.debug('Copy.run: args=%s', self.args)
        # pylint: disable=no-member
        dest = self.args.dest
        files = self.get_files()
        # pylint: disable=no-member
        excludes = self.args.exclude
        self.logger.debug('Copy.run: files=%s; dest=%s',
                          repr(files), repr(dest))
        fmap = FileMapper(files, destdir=dest, exclude=excludes)
        self.logger.debug('Copy.fmap = %s', vars(fmap))
        for (sname, dname) in fmap:
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
            elif dstfile.isfile and fmap.checkpair(srcfile, dstfile):
                self.logger.debug('uptodate: %s', dstfile)
            else:
                if not dstfile.dirname.isdir:
                    dstfile.dirname.mkdir()
                self.logger.info('copy2(%s,%s)', sname, dname)
                srcfile.copy(dstfile)

Copy.register()
