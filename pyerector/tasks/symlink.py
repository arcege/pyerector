#!/usr/bin/python
"""Tasks plugin for Symlink."""

from ._base import Base
from ..args import Arguments
from ..path import Path
from ..exception import Error
from ..base import Initer, Iterator, Mapper, Task
from ..iterators import FileIterator, FileMapper

class Symlink(Task, Base):
    """Generate a symbolic link.
constructor arguments:
Symlink(*files, dest=<dest>, exclude=<defaults>)"""
    arguments = Arguments(
        Arguments.List('files', types=(Iterator, Path, str), cast=FileIterator),
        Arguments.Keyword('dest', types=(Path, str), cast=Path),
        Arguments.Exclusions('exclude'),
    ) + Initer.basearguments

    def run(self):
        files = self.get_files()
        # pylint: disable=no-member
        dest = self.args.dest
        # pylint: disable=no-member
        excludes = self.args.excludes
        if len(files) == 1 and dest is None and isinstance(files[0], Mapper):
            fmap = files[0]
        elif len(files) == 1 and dest is not None and not dest.isdir:
            fmap = FileMapper(files[0], destdir=dest, exclude=excludes)
        elif dest is not None:
            fmap = FileMapper(self.get_files(files),
                              destdir=dest, exclude=excludes)
        else:
            raise Error('must supply dest to %s' % self)
        for (sname, dname) in fmap:
            self.logger.debug('symlink.sname=%s; symlink.dname=%s',
                              sname, dname)
            srcfile = self.join(sname)
            dstfile = self.join(dname)
            if not excludes.match(sname):
                if srcfile.islink and fmap.checkpair(dstfile, srcfile):
                    self.logger.debug('uptodate: %s', dstfile)
                else:
                    self.logger.info('symlink(%s, %s)', dname, sname)
                    dstfile.makelink(srcfile)

Symlink.register()
